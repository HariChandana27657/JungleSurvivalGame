import socket, threading, json, random, string, os

PORT   = int(os.environ.get("PORT", 55432))
BUFFER = 8192

# ── Set this after deploying relay_server.py to Railway ──────────────────────
# Replace with your actual Railway domain after deploy
RELAY_HOST = os.environ.get("RELAY_HOST", "your-relay.up.railway.app")
RELAY_PORT = int(os.environ.get("RELAY_PORT", 55432))

def _get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]; s.close(); return ip
    except Exception:
        return "127.0.0.1"

def make_code(n=6):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=n))

def parse_share(share_str):
    share_str = share_str.strip().upper()
    # bare 6-char code
    if len(share_str) <= 8 and "@" not in share_str and ":" not in share_str:
        return share_str, RELAY_HOST, RELAY_PORT
    if "@" in share_str:
        code, addr = share_str.split("@", 1)
        if ":" in addr:
            host, port = addr.rsplit(":", 1)
            return code, host, int(port)
        return code, addr, RELAY_PORT
    if ":" in share_str:
        host, port = share_str.rsplit(":", 1)
        return "", host, int(port)
    return share_str, RELAY_HOST, RELAY_PORT


class MPServer:
    """Host-side wrapper — creates a room on the relay server."""
    MAX_PLAYERS = 4

    def __init__(self):
        self.code      = ""
        self.players   = {}
        self.started   = False
        self.level     = 0
        self._lock     = threading.Lock()
        self._log      = []
        self._conn     = None
        self._buf      = ""
        self.connected = False
        self.error     = ""
        # join_requests: list of {pid, name} waiting for approval
        self.join_requests = []
        # tunnel stub (kept for UI compatibility)
        self.tunnel    = _TunnelStub()

    def start(self):
        threading.Thread(target=self._connect, daemon=True).start()

    def _connect(self):
        try:
            self._conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._conn.settimeout(10.0)
            self._conn.connect((RELAY_HOST, RELAY_PORT))
            self._conn.settimeout(None)
            self.connected = True
            self._send({"type": "create", "name": "Host"})
            threading.Thread(target=self._recv_loop, daemon=True).start()
        except Exception as e:
            self.error = str(e)

    def _recv_loop(self):
        while self.connected:
            try:
                data = self._conn.recv(BUFFER).decode("utf-8", errors="ignore")
                if not data: break
                self._buf += data
                while "\n" in self._buf:
                    line, self._buf = self._buf.split("\n", 1)
                    try: self._handle(json.loads(line))
                    except Exception: pass
            except Exception: break
        self.connected = False

    def _handle(self, msg):
        t = msg.get("type")
        with self._lock:
            if t == "created":
                self.code = msg.get("code", "")
                self.tunnel._code = self.code
            elif t in ("lobby", "state"):
                pl = msg.get("players", [])
                self.players = {p["id"]: p for p in pl}
                if t == "lobby":
                    self.started = msg.get("started", False)
                    self.level   = msg.get("level", 0)
            elif t == "start":
                self.started = True; self.level = msg.get("level", 0)
            elif t == "join_request":
                req = {"pid": msg["pid"], "name": msg.get("name", "?")}
                if req not in self.join_requests:
                    self.join_requests.append(req)
                    self._log.append(f"{req['name']} wants to join")

    def approve(self, pid):
        self._send({"type": "approve", "pid": pid})
        with self._lock:
            self.join_requests = [r for r in self.join_requests if r["pid"] != pid]
            self._log.append(f"Player {pid} approved")

    def reject(self, pid):
        self._send({"type": "reject", "pid": pid})
        with self._lock:
            self.join_requests = [r for r in self.join_requests if r["pid"] != pid]
            self._log.append(f"Player {pid} rejected")

    def send_start(self, level):
        self.started = True; self.level = level
        self._send({"type": "start", "level": level})

    def _send(self, obj):
        if self._conn and self.connected:
            try: self._conn.sendall((json.dumps(obj) + "\n").encode())
            except Exception: self.connected = False

    def stop(self):
        self.connected = False
        if self._conn:
            try: self._conn.close()
            except: pass

    @property
    def share_string(self):
        return f"{self.code}@{RELAY_HOST}:{RELAY_PORT}"

    @property
    def player_list(self):
        with self._lock: return list(self.players.values())

    @property
    def logs(self):
        with self._lock: return list(self._log[-6:])

    @property
    def pending_requests(self):
        with self._lock: return list(self.join_requests)


class _TunnelStub:
    """Stub so existing UI code that checks tunnel.ready / tunnel.address still works."""
    def __init__(self):
        self._code = ""
    @property
    def ready(self): return bool(self._code)
    @property
    def address(self): return f"{RELAY_HOST}:{RELAY_PORT}"
    @property
    def error(self): return ""
    def start(self): pass
    def stop(self): pass


class MPClient:
    """Joiner-side — connects to relay and joins a room by code."""
    def __init__(self, host=RELAY_HOST, port=RELAY_PORT, name="Player"):
        self.host=host; self.port=port; self.name=name; self.my_id=None
        self.players={}; self.lobby=[]; self.connected=False
        self.started=False; self.level=0; self._conn=None
        self._lock=threading.Lock(); self._buf=""; self.error=""
        self.approved=False; self.rejected=False; self.waiting=False
        self._code=""

    def connect(self, code):
        self._code = code.upper()
        try:
            self._conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._conn.settimeout(8.0)
            self._conn.connect((self.host, self.port))
            self._conn.settimeout(None); self.connected = True
            threading.Thread(target=self._recv_loop, daemon=True).start()
            self._send({"type": "join", "code": self._code, "name": self.name})
        except Exception as e:
            self.error = str(e); self.connected = False

    def _recv_loop(self):
        while self.connected:
            try:
                data = self._conn.recv(BUFFER).decode("utf-8", errors="ignore")
                if not data: break
                self._buf += data
                while "\n" in self._buf:
                    line, self._buf = self._buf.split("\n", 1)
                    try: self._handle(json.loads(line))
                    except Exception: pass
            except Exception: break
        self.connected = False

    def _handle(self, msg):
        t = msg.get("type")
        with self._lock:
            if t == "waiting":
                self.my_id = msg.get("pid"); self.waiting = True
            elif t == "approved":
                self.approved = True; self.waiting = False
            elif t == "rejected":
                self.rejected = True; self.connected = False
            elif t in ("lobby", "state"):
                pl = msg.get("players", [])
                self.lobby = pl; self.players = {p["id"]: p for p in pl}
                if t == "lobby":
                    self.started = msg.get("started", False)
                    self.level   = msg.get("level", 0)
            elif t == "start":
                self.started = True; self.level = msg.get("level", 0)
            elif t == "error":
                self.error = msg.get("msg", "Unknown error")
                self.connected = False

    def send_update(self, x, y, score, lives, hp, energy, finished=False):
        self._send({"type":"update","x":x,"y":y,"score":score,
                    "lives":lives,"hp":hp,"energy":energy,"finished":finished})

    def _send(self, obj):
        if self._conn and self.connected:
            try: self._conn.sendall((json.dumps(obj) + "\n").encode())
            except Exception: self.connected = False

    def disconnect(self):
        self.connected = False
        if self._conn:
            try: self._conn.close()
            except: pass

    @property
    def other_players(self):
        with self._lock:
            return [p for p in self.players.values() if p["id"] != self.my_id]

    @property
    def lobby_list(self):
        with self._lock: return list(self.lobby)
