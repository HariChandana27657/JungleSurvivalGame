"""
relay_server.py — Jungle Survival Relay Server
Includes: room management, host approval, HMAC auth to prevent replay attacks.
"""
import socket, threading, json, random, string, os, time, hmac, hashlib, secrets

PORT   = int(os.environ.get("PORT", 55432))
BUFFER = 8192

def make_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def make_nonce():
    return secrets.token_hex(16)   # 32-char random hex

def sign(room_code, nonce, timestamp, name):
    """HMAC-SHA256 signature the client must produce to authenticate."""
    msg = f"{room_code}:{nonce}:{timestamp}:{name}".encode()
    key = room_code.encode()
    return hmac.new(key, msg, hashlib.sha256).hexdigest()

def verify_auth(room_code, nonce, timestamp, name, sig, used_nonces):
    """Returns (ok, reason)."""
    # timestamp must be within 30 seconds
    try:
        ts = float(timestamp)
    except Exception:
        return False, "bad timestamp"
    if abs(time.time() - ts) > 30:
        return False, "timestamp expired"
    # nonce must not have been used before
    if nonce in used_nonces:
        return False, "replay detected"
    # signature must match
    expected = sign(room_code, nonce, timestamp, name)
    if not hmac.compare_digest(expected, sig):
        return False, "invalid signature"
    return True, "ok"

# ── Room registry ─────────────────────────────────────────────────────────────
rooms = {}       # code -> Room
rooms_lock = threading.Lock()

class Room:
    MAX = 4
    def __init__(self, code):
        self.code     = code
        self.players  = {}
        self.conns    = {}
        self.next_id  = 1
        self.started  = False
        self.level    = 0
        self.lock     = threading.Lock()
        self.created  = time.time()
        self.used_nonces = set()   # replay attack prevention

    def consume_nonce(self, nonce):
        """Returns True if nonce is fresh, False if already used."""
        with self.lock:
            if nonce in self.used_nonces:
                return False
            self.used_nonces.add(nonce)
            return True

    def add(self, conn):
        with self.lock:
            if len(self.players) >= self.MAX:
                return None
            pid = self.next_id; self.next_id += 1
            self.players[pid] = {"id":pid,"name":f"P{pid}","x":130,"y":500,
                                  "score":0,"lives":3,"hp":100,"energy":100,
                                  "finished":False,"approved":False}
            self.conns[pid] = conn
            return pid

    def remove(self, pid):
        with self.lock:
            self.players.pop(pid, None)
            self.conns.pop(pid, None)

    def broadcast(self, obj, exclude=None):
        data = (json.dumps(obj) + "\n").encode()
        dead = []
        with self.lock:
            conns = dict(self.conns)
        for pid, conn in conns.items():
            if pid == exclude: continue
            try:
                conn.sendall(data)
            except Exception:
                dead.append(pid)
        for pid in dead:
            self.remove(pid)

    def send_to(self, pid, obj):
        data = (json.dumps(obj) + "\n").encode()
        with self.lock:
            conn = self.conns.get(pid)
        if conn:
            try: conn.sendall(data)
            except Exception: self.remove(pid)

    @property
    def host_id(self):
        with self.lock:
            ids = sorted(self.players.keys())
            return ids[0] if ids else None

    @property
    def player_list(self):
        with self.lock:
            return list(self.players.values())

    def is_stale(self):
        return time.time() - self.created > 3600  # 1 hour TTL


# ── Client handler ────────────────────────────────────────────────────────────
def handle_client(conn, addr):
    buf = ""; room = None; pid = None
    try:
        conn.settimeout(120)

        # ── Send challenge nonce immediately on connect ───────────────────────
        nonce = make_nonce()
        conn.sendall((json.dumps({"type":"challenge","nonce":nonce}) + "\n").encode())

        while True:
            data = conn.recv(BUFFER).decode("utf-8", errors="ignore")
            if not data: break
            buf += data
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                if not line.strip(): continue
                try:
                    msg = json.loads(line)
                except Exception:
                    continue

                t = msg.get("type")

                # ── CREATE room ──────────────────────────────────────────────
                if t == "create":
                    name = msg.get("name","Host")[:24]
                    # host creates the room — no auth needed (they own the code)
                    code = make_code()
                    with rooms_lock:
                        while code in rooms:
                            code = make_code()
                        room = Room(code)
                        rooms[code] = room
                    pid = room.add(conn)
                    room.players[pid]["name"] = name
                    room.players[pid]["approved"] = True
                    conn.sendall((json.dumps({"type":"created","code":code,"pid":pid}) + "\n").encode())
                    room.broadcast({"type":"lobby","players":room.player_list,
                                    "started":False,"level":room.level})

                # ── JOIN room — requires valid HMAC auth ──────────────────────
                elif t == "join":
                    code    = msg.get("code","").upper()
                    name    = msg.get("name","Player")[:24]
                    ts      = str(msg.get("timestamp",""))
                    sig     = msg.get("sig","")
                    c_nonce = msg.get("nonce", nonce)  # client echoes the challenge nonce

                    with rooms_lock:
                        room = rooms.get(code)

                    if not room:
                        conn.sendall((json.dumps({"type":"error","msg":"Room not found"}) + "\n").encode())
                        room = None; continue

                    # verify auth
                    ok, reason = verify_auth(code, c_nonce, ts, name, sig, set())
                    if not ok:
                        conn.sendall((json.dumps({"type":"error","msg":f"Auth failed: {reason}"}) + "\n").encode())
                        room = None; continue

                    # consume nonce to prevent replay
                    if not room.consume_nonce(c_nonce):
                        conn.sendall((json.dumps({"type":"error","msg":"Replay attack detected"}) + "\n").encode())
                        room = None; continue

                    if room.started:
                        conn.sendall((json.dumps({"type":"error","msg":"Game already started"}) + "\n").encode())
                        room = None; continue

                    pid = room.add(conn)
                    if pid is None:
                        conn.sendall((json.dumps({"type":"error","msg":"Room full"}) + "\n").encode())
                        room = None; continue

                    room.players[pid]["name"] = name
                    room.send_to(room.host_id, {"type":"join_request","pid":pid,"name":name})
                    conn.sendall((json.dumps({"type":"waiting","pid":pid,"code":code}) + "\n").encode())
                    room.broadcast({"type":"lobby","players":room.player_list,
                                    "started":False,"level":room.level})

                # ── HOST APPROVES / REJECTS player ────────────────────────────
                elif t == "approve" and room and pid == room.host_id:
                    target = msg.get("pid")
                    if target in room.players:
                        room.players[target]["approved"] = True
                        room.send_to(target, {"type":"approved"})
                        room.broadcast({"type":"lobby","players":room.player_list,
                                        "started":False,"level":room.level})

                elif t == "reject" and room and pid == room.host_id:
                    target = msg.get("pid")
                    if target in room.conns:
                        room.send_to(target, {"type":"rejected"})
                        room.remove(target)
                    room.broadcast({"type":"lobby","players":room.player_list,
                                    "started":False,"level":room.level})

                # ── START game (host only) ────────────────────────────────────
                elif t == "start" and room and pid == room.host_id:
                    room.started = True
                    room.level   = msg.get("level", 0)
                    room.broadcast({"type":"start","level":room.level})

                # ── GAME STATE update ─────────────────────────────────────────
                elif t == "update" and room and pid:
                    with room.lock:
                        if pid in room.players:
                            for k in ("x","y","score","lives","hp","energy","finished","name"):
                                if k in msg: room.players[pid][k] = msg[k]
                    room.broadcast({"type":"state","players":room.player_list}, exclude=pid)

                # ── CHAT message ──────────────────────────────────────────────
                elif t == "chat" and room:
                    name = room.players.get(pid,{}).get("name","?")
                    room.broadcast({"type":"chat","name":name,"msg":msg.get("msg","")[:120]})

    except Exception:
        pass
    finally:
        if room and pid:
            room.remove(pid)
            if room.player_list:
                room.broadcast({"type":"lobby","players":room.player_list,
                                "started":room.started,"level":room.level})
            else:
                with rooms_lock:
                    rooms.pop(room.code, None)
        try: conn.close()
        except: pass


# ── Cleanup stale rooms ───────────────────────────────────────────────────────
def cleanup_loop():
    while True:
        time.sleep(300)
        with rooms_lock:
            stale = [c for c,r in rooms.items() if r.is_stale()]
            for c in stale:
                rooms.pop(c, None)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    threading.Thread(target=cleanup_loop, daemon=True).start()
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", PORT))
    srv.listen(50)
    print(f"Relay server listening on port {PORT}")
    while True:
        conn, addr = srv.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    main()
