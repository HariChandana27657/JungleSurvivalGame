# -*- coding: utf-8 -*-
"""
LIFE SURVIVAL  —  Advanced Platformer
Features: 5 themed levels, 3 lives, energy system, weather FX,
          map screen, sound engine, Mario-style obstacles, 3-D UI
"""
import pygame, random, math, sys
from enum import Enum
from multiplayer import MPServer, MPClient, _get_local_ip, parse_share, PORT

pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# ── Display ──────────────────────────────────────────────────────────────────
SW, SH = 1100, 650
screen = pygame.display.set_mode((SW, SH))
pygame.display.set_caption("Life Survival")
clock  = pygame.time.Clock()
FPS    = 60

# ── Physics ──────────────────────────────────────────────────────────────────
GRAVITY    = 0.72
JUMP_POWER = -15.5
GROUND_Y   = SH - 75

# ── Palette ──────────────────────────────────────────────────────────────────
def c(*v): return tuple(v)
BLACK=(0,0,0);WHITE=(255,255,255);GOLD=(255,200,0);YELLOW=(255,230,50)
GREEN=(34,139,34);DGREEN=(0,80,0);ORANGE=(255,140,0);RED=(210,40,40)
BLUE=(70,130,210);LBLUE=(150,205,255);BROWN=(110,65,18);DBROWN=(70,40,8)
GRAY=(90,90,100);LGRAY=(180,185,195);TEAL=(0,175,155);PURPLE=(120,55,195)
PINK=(255,80,150);CYAN=(0,220,220);HP_G=(50,220,80);HP_R=(220,50,50)
HP_Y=(240,200,0);SKYT=(18,60,140);SKYB=(100,175,255)

# ── Fonts ─────────────────────────────────────────────────────────────────────
F80=pygame.font.Font(None,80); F60=pygame.font.Font(None,60)
F48=pygame.font.Font(None,48); F36=pygame.font.Font(None,36)
F28=pygame.font.Font(None,28); F22=pygame.font.Font(None,22)
F16=pygame.font.Font(None,16)

# ── States ────────────────────────────────────────────────────────────────────
class GS(Enum):
    SPLASH=0; MAP=1; PLAYING=2; PAUSED=3; LEVEL_WIN=4
    GAME_OVER=5; DEAD=6; TRANSITION=7
    MP_MENU=10; MP_HOST=11; MP_JOIN=12; MP_LOBBY=13; MP_PLAYING=14
    CHAR_SELECT=20; MP_WAITING=21

# ── Level definitions ─────────────────────────────────────────────────────────
LEVELS = [
  # Level 1 — gentle intro, wide platforms, few obstacles
  dict(name="Jungle Dawn",   theme="jungle",  sky_t=(18,60,140),  sky_b=(100,175,255),
       time=100, lives=3, world_w=3000, plat_kind="wood",
       boulders=2, spikes=3,  flyers=0, pits=1,
       boulder_speed=(1.8,2.5), gap_base=160,
       map_pos=(180,320), map_col=(40,160,60)),
  # Level 2 — lava theme, faster boulders, first flyers
  dict(name="Lava Cavern",   theme="lava",    sky_t=(80,10,10),   sky_b=(180,60,20),
       time=85,  lives=3, world_w=3600, plat_kind="lava_rock",
       boulders=4, spikes=6,  flyers=2, pits=3,
       boulder_speed=(2.5,3.5), gap_base=190,
       map_pos=(340,260), map_col=(200,80,20)),
  # Level 3 — ice, slippery feel, more flyers, bigger gaps
  dict(name="Ice Peaks",     theme="ice",     sky_t=(10,30,80),   sky_b=(140,200,255),
       time=70,  lives=3, world_w=4000, plat_kind="ice",
       boulders=6, spikes=8,  flyers=4, pits=4,
       boulder_speed=(3.0,4.2), gap_base=210,
       map_pos=(510,310), map_col=(100,180,255)),
  # Level 4 — storm, narrow platforms, fast everything
  dict(name="Storm Ruins",   theme="storm",   sky_t=(30,20,50),   sky_b=(80,60,120),
       time=60,  lives=3, world_w=4600, plat_kind="stone",
       boulders=9, spikes=11, flyers=6, pits=5,
       boulder_speed=(3.8,5.0), gap_base=230,
       map_pos=(680,240), map_col=(130,60,200)),
  # Level 5 — abyss, brutal, tiny platforms, max obstacles
  dict(name="Shadow Abyss",  theme="abyss",   sky_t=(5,5,15),     sky_b=(30,20,60),
       time=50,  lives=3, world_w=5000, plat_kind="obsidian",
       boulders=13,spikes=15, flyers=8, pits=7,
       boulder_speed=(4.5,6.0), gap_base=250,
       map_pos=(860,290), map_col=(80,20,120)),
]

ITEM_COL={"candy":(255,80,150),"basket":(255,160,30),"stick":(80,200,80),
           "gem":(140,80,255),"heart":(255,60,100),"shield":(80,180,255)}
ITEM_VAL={"candy":10,"basket":25,"stick":5,"gem":60,"heart":0,"shield":0}

# ── Character definitions ─────────────────────────────────────────────────────
CHARACTERS = [
    dict(id="boy",      label="Boy",      desc="Fast & agile",
         skin=(235,185,125), hair=(60,35,10),  body=(55,115,215),
         legs=(25,55,130),   shoes=(40,25,10), extra="cap"),
    dict(id="girl",     label="Girl",     desc="Quick jumper",
         skin=(240,195,140), hair=(180,80,20),  body=(220,80,150),
         legs=(180,60,120),  shoes=(200,100,140), extra="ponytail"),
    dict(id="grandpa",  label="Grandpa",  desc="Tough & sturdy",
         skin=(210,175,130), hair=(200,200,200), body=(80,80,160),
         legs=(60,60,120),   shoes=(50,35,20),  extra="beard"),
    dict(id="grandma",  label="Grandma",  desc="Wise collector",
         skin=(215,180,135), hair=(220,215,210), body=(160,80,160),
         legs=(120,60,120),  shoes=(140,80,100), extra="bun"),
    dict(id="police",   label="Officer",  desc="Shield bonus",
         skin=(235,185,125), hair=(40,30,10),   body=(30,60,140),
         legs=(20,40,100),   shoes=(20,20,30),  extra="badge"),
]

# ═══════════════════════════════════════════════════════════════════════════════
#  SOUND ENGINE  (procedural — no external files needed)
# ═══════════════════════════════════════════════════════════════════════════════
import numpy as np

def _make_sound(freq, duration, wave="sine", volume=0.3, decay=True):
    sr = 44100
    n  = int(sr * duration)
    t  = np.linspace(0, duration, n, False)
    if wave == "sine":
        w = np.sin(2 * np.pi * freq * t)
    elif wave == "square":
        w = np.sign(np.sin(2 * np.pi * freq * t))
    elif wave == "noise":
        w = np.random.uniform(-1, 1, n)
    else:
        w = np.sin(2 * np.pi * freq * t)
    if decay:
        env = np.linspace(1, 0, n) ** 1.5
        w  *= env
    w = (w * volume * 32767).astype(np.int16)
    stereo = np.column_stack([w, w])
    return pygame.sndarray.make_sound(stereo)

def _make_jump():
    sr=44100; n=int(sr*0.18)
    t=np.linspace(0,0.18,n,False)
    freq=np.linspace(300,600,n)
    w=np.sin(2*np.pi*freq*t)*np.linspace(1,0,n)**1.2*0.4
    w=(w*32767).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack([w,w]))

def _make_collect():
    sr=44100; n=int(sr*0.12)
    t=np.linspace(0,0.12,n,False)
    freq=np.linspace(600,1200,n)
    w=np.sin(2*np.pi*freq*t)*np.linspace(1,0,n)**1.0*0.35
    w=(w*32767).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack([w,w]))

def _make_hit():
    sr=44100; n=int(sr*0.15)
    t=np.linspace(0,0.15,n,False)
    w=np.random.uniform(-1,1,n)*np.linspace(1,0,n)**0.8*0.5
    w=(w*32767).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack([w,w]))

def _make_finish():
    sr=44100; n=int(sr*0.6)
    t=np.linspace(0,0.6,n,False)
    notes=[523,659,784,1047]
    w=np.zeros(n)
    seg=n//4
    for i,f in enumerate(notes):
        s=i*seg; e=min(s+seg,n)
        tt=t[s:e]-t[s]
        w[s:e]=np.sin(2*np.pi*f*tt)*np.linspace(1,0,e-s)**0.8
    w=(w*0.4*32767).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack([w,w]))

def _make_death():
    sr=44100; n=int(sr*0.5)
    t=np.linspace(0,0.5,n,False)
    freq=np.linspace(400,80,n)
    w=np.sin(2*np.pi*freq*t)*np.linspace(1,0,n)**0.6*0.45
    w=(w*32767).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack([w,w]))

def _make_bgm(theme):
    """Simple loopable background tone per theme."""
    sr=44100; dur=2.0; n=int(sr*dur)
    t=np.linspace(0,dur,n,False)
    freqs={"jungle":[130,165,196],"lava":[110,138,165],
           "ice":[196,247,294],"storm":[98,123,147],"abyss":[82,104,123]}
    fs=freqs.get(theme,[130,165,196])
    w=sum(np.sin(2*np.pi*f*t)*0.08 for f in fs)
    w=(w*32767).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack([w,w]))

def _make_gunshot():
    """Sharp crack: short noise burst + low thump layered together."""
    sr=44100; n=int(sr*0.09)
    t=np.linspace(0,0.09,n,False)
    # high crack — white noise with fast decay
    crack=np.random.uniform(-1,1,n)*np.exp(-t*80)*0.55
    # low thump — sine at 120 Hz with very fast decay
    thump=np.sin(2*np.pi*120*t)*np.exp(-t*60)*0.45
    w=(crack+thump)
    w=np.clip(w,-1,1)
    w=(w*32767).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack([w,w]))

try:
    SND_JUMP    = _make_jump()
    SND_COLLECT = _make_collect()
    SND_HIT     = _make_hit()
    SND_FINISH  = _make_finish()
    SND_DEATH   = _make_death()
    SND_GUN     = _make_gunshot()
    SND_BGM     = {th: _make_bgm(th) for th in ["jungle","lava","ice","storm","abyss"]}
    SOUND_OK    = True
except Exception:
    SOUND_OK = False

def play(snd):
    if SOUND_OK:
        try: snd.play()
        except: pass

def play_bgm(theme):
    if not SOUND_OK: return
    try:
        pygame.mixer.stop()
        s=SND_BGM.get(theme)
        if s: s.play(-1)
    except: pass

# ═══════════════════════════════════════════════════════════════════════════════
#  DRAW UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════
def grad(surf, ct, cb, rect):
    r1,g1,b1=ct; r2,g2,b2=cb
    for i in range(rect.height):
        t=i/max(rect.height-1,1)
        pygame.draw.line(surf,
            (int(r1+(r2-r1)*t),int(g1+(g2-g1)*t),int(b1+(b2-b1)*t)),
            (rect.x,rect.y+i),(rect.x+rect.width,rect.y+i))

def shadow_text(surf,txt,font,col,x,y,sh=BLACK,off=2):
    surf.blit(font.render(txt,True,sh),(x+off,y+off))
    surf.blit(font.render(txt,True,col),(x,y))

def rr(surf,col,rect,r=10,bw=0,bc=WHITE):
    pygame.draw.rect(surf,col,rect,border_radius=r)
    if bw: pygame.draw.rect(surf,bc,rect,bw,border_radius=r)

def lerp(a,b,t): return a+(b-a)*t

def bright(col,amt):
    return tuple(min(255,max(0,v+amt)) for v in col)

def alpha_surf(w,h,col,a):
    s=pygame.Surface((w,h),pygame.SRCALPHA); s.fill((*col,a)); return s

# ═══════════════════════════════════════════════════════════════════════════════
#  BUTTON  (3-D bevel, glow on hover)
# ═══════════════════════════════════════════════════════════════════════════════
class Button:
    def __init__(self,x,y,w,h,txt,col,hcol,tcol=WHITE,icon=None):
        self.rect=pygame.Rect(x,y,w,h); self.txt=txt
        self.col=col; self.hcol=hcol; self.tcol=tcol
        self.hov=False; self.sc=1.0; self.glow=0.0; self.icon=icon

    def draw(self,surf):
        self.sc  =lerp(self.sc,  1.08 if self.hov else 1.0, 0.16)
        self.glow=lerp(self.glow,1.0  if self.hov else 0.0, 0.14)
        sw=int(self.rect.w*self.sc); sh=int(self.rect.h*self.sc)
        sx=self.rect.centerx-sw//2;  sy=self.rect.centery-sh//2
        sr=pygame.Rect(sx,sy,sw,sh)
        # outer glow
        if self.glow>0.05:
            gs=pygame.Surface((sw+20,sh+20),pygame.SRCALPHA)
            ga=int(self.glow*80)
            pygame.draw.rect(gs,(*self.hcol,ga),(0,0,sw+20,sh+20),border_radius=14)
            surf.blit(gs,(sx-10,sy-10))
        # drop shadow
        pygame.draw.rect(surf,(0,0,0,0),pygame.Rect(sx+5,sy+6,sw,sh),border_radius=13)
        c=self.hcol if self.hov else self.col
        # gradient fill
        grad(surf,bright(c,50),bright(c,-30),sr)
        # top highlight
        pygame.draw.rect(surf,bright(c,90),pygame.Rect(sx+2,sy+2,sw-4,5),border_radius=12)
        # bottom shadow
        pygame.draw.rect(surf,bright(c,-70),pygame.Rect(sx+2,sy+sh-7,sw-4,5),border_radius=12)
        pygame.draw.rect(surf,WHITE,sr,2,border_radius=13)
        ts=F28.render(self.txt,True,self.tcol)
        surf.blit(ts,ts.get_rect(center=sr.center))

    def hit(self,ev):
        if ev.type==pygame.MOUSEMOTION: self.hov=self.rect.collidepoint(ev.pos)
        if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1 and self.rect.collidepoint(ev.pos):
            return True
        return False

# ═══════════════════════════════════════════════════════════════════════════════
#  WEATHER SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════
class WeatherSystem:
    def __init__(self,theme):
        self.theme=theme
        self.drops=[]; self.flakes=[]; self.embers=[]; self.lightning=0
        if theme=="jungle":
            self.drops=[[random.randint(0,SW),random.randint(-SH,0),
                         random.uniform(8,14),random.uniform(1,3)] for _ in range(120)]
        elif theme=="ice":
            self.flakes=[[random.randint(0,SW),random.randint(-SH,0),
                          random.uniform(1,3),random.uniform(0.5,1.5),
                          random.uniform(0,math.pi*2)] for _ in range(80)]
        elif theme=="lava":
            self.embers=[[random.randint(0,SW),random.randint(GROUND_Y-50,GROUND_Y),
                          random.uniform(-1,1),random.uniform(-3,-1),
                          random.randint(15,35)] for _ in range(60)]
        elif theme=="storm":
            self.drops=[[random.randint(0,SW),random.randint(-SH,0),
                         random.uniform(14,20),random.uniform(2,4)] for _ in range(200)]
            self.lightning=0

    def update(self,tick):
        if self.theme in("jungle","storm"):
            for d in self.drops:
                d[1]+=d[2]
                if d[1]>SH: d[1]=-random.randint(10,60); d[0]=random.randint(0,SW)
            if self.theme=="storm" and random.random()<0.004:
                self.lightning=8
            if self.lightning>0: self.lightning-=1
        elif self.theme=="ice":
            for f in self.flakes:
                f[1]+=f[3]; f[0]+=math.sin(f[4])*0.8; f[4]+=0.02
                if f[1]>SH: f[1]=-10; f[0]=random.randint(0,SW)
        elif self.theme=="lava":
            for e in self.embers:
                e[0]+=e[2]; e[1]+=e[3]; e[3]+=0.05
                if e[1]<GROUND_Y-200 or e[1]>GROUND_Y:
                    e[0]=random.randint(0,SW); e[1]=GROUND_Y-random.randint(0,30)
                    e[2]=random.uniform(-1,1); e[3]=random.uniform(-3,-1)

    def draw(self,surf):
        if self.theme in("jungle","storm"):
            if self.theme=="storm" and self.lightning>0:
                fl=alpha_surf(SW,SH,(200,200,255),min(120,self.lightning*20))
                surf.blit(fl,(0,0))
                # lightning bolt
                lx=random.randint(100,SW-100)
                pts=[(lx,0)]
                y=0
                while y<GROUND_Y:
                    y+=random.randint(30,60)
                    pts.append((lx+random.randint(-40,40),y))
                if len(pts)>1:
                    pygame.draw.lines(surf,(220,220,255),False,pts,2)
            for d in self.drops:
                a=180 if self.theme=="storm" else 120
                pygame.draw.line(surf,(180,210,255,a),(int(d[0]),int(d[1])),
                                 (int(d[0]-d[3]),int(d[1]+d[2])),1)
        elif self.theme=="ice":
            for f in self.flakes:
                pygame.draw.circle(surf,(220,240,255),(int(f[0]),int(f[1])),int(f[2]))
        elif self.theme=="lava":
            for e in self.embers:
                r=random.randint(2,4)
                pygame.draw.circle(surf,(255,random.randint(80,160),20),(int(e[0]),int(e[1])),r)
        elif self.theme=="abyss":
            # floating dark motes
            pass

# ═══════════════════════════════════════════════════════════════════════════════
#  PLATFORM  (3-D layered with depth edge)
# ═══════════════════════════════════════════════════════════════════════════════
class Platform:
    THEMES={
        "wood":     ((135,85,28),(85,50,8),(175,115,45)),
        "stone":    ((105,105,115),(65,65,75),(145,145,155)),
        "ice":      ((160,210,255),(100,160,220),(200,235,255)),
        "lava_rock":((120,40,10),(70,20,5),(200,80,20)),
        "obsidian": ((30,20,50),(15,10,30),(80,50,120)),
        "ground":   ((55,135,35),(25,75,8),(75,175,45)),
    }
    def __init__(self,x,y,w,h,kind="wood"):
        self.rect=pygame.Rect(x,y,w,h); self.kind=kind

    def draw(self,surf,cam):
        sx=self.rect.x-cam
        if sx+self.rect.w<-10 or sx>SW+10: return
        r=pygame.Rect(sx,self.rect.y,self.rect.w,self.rect.h)
        top,bot,hi=self.THEMES.get(self.kind,self.THEMES["wood"])
        grad(surf,top,bot,r)
        # top highlight strip
        pygame.draw.rect(surf,hi,pygame.Rect(sx,self.rect.y,self.rect.w,5),border_radius=3)
        # 3-D depth bottom edge
        depth=pygame.Rect(sx+2,self.rect.y+self.rect.h,self.rect.w-2,7)
        grad(surf,bright(bot,-30),bright(bot,-60),depth)
        # right edge
        pygame.draw.rect(surf,bright(bot,-40),(sx+self.rect.w,self.rect.y+3,5,self.rect.h+4))
        # border
        pygame.draw.rect(surf,bright(hi,-20),r,1,border_radius=3)
        # texture details
        if self.kind=="wood":
            for i in range(0,self.rect.w,16):
                pygame.draw.line(surf,bright(bot,10),(sx+i,self.rect.y+2),(sx+i,self.rect.y+self.rect.h-2))
        elif self.kind=="ice":
            pygame.draw.rect(surf,(230,248,255,80),pygame.Rect(sx+4,self.rect.y+2,self.rect.w-8,4),border_radius=3)
        elif self.kind=="lava_rock":
            for i in range(0,self.rect.w,25):
                pygame.draw.circle(surf,(240,100,20),(sx+i+8,self.rect.y+self.rect.h//2),3)
        elif self.kind=="obsidian":
            for i in range(0,self.rect.w,20):
                pygame.draw.line(surf,(100,60,160),(sx+i,self.rect.y),(sx+i+8,self.rect.y+self.rect.h),1)
        elif self.kind=="ground":
            pygame.draw.rect(surf,(100,60,20),pygame.Rect(sx,self.rect.y+6,self.rect.w,self.rect.h-6))
            pygame.draw.rect(surf,(75,175,45),pygame.Rect(sx,self.rect.y,self.rect.w,6))

# ═══════════════════════════════════════════════════════════════════════════════
#  PIT  (gap in ground — instant death)
# ═══════════════════════════════════════════════════════════════════════════════
class Pit:
    def __init__(self,x,w):
        self.rect=pygame.Rect(x,GROUND_Y,w,200)
        self.x=x; self.w=w

    def draw(self,surf,cam):
        sx=self.x-cam
        if sx+self.w<0 or sx>SW: return
        # dark void
        grad(surf,(10,5,20),(0,0,0),pygame.Rect(sx,GROUND_Y,self.w,200))
        # lava glow at bottom
        pygame.draw.rect(surf,(80,20,0),pygame.Rect(sx,GROUND_Y+180,self.w,20))
        # edge warning stripes
        for i in range(0,self.w,20):
            col=RED if (i//20)%2==0 else YELLOW
            pygame.draw.rect(surf,col,(sx+i,GROUND_Y-6,10,6))

# ═══════════════════════════════════════════════════════════════════════════════
#  COLLECTIBLE
# ═══════════════════════════════════════════════════════════════════════════════
class Collectible:
    def __init__(self,x,y,kind):
        self.kind=kind; self.rect=pygame.Rect(x,y,26,26)
        self.val=ITEM_VAL[kind]; self.bob=random.uniform(0,math.pi*2)

    def draw(self,surf,cam,tick):
        sx=self.rect.x-cam
        if sx<-30 or sx>SW+30: return
        by=int(math.sin(tick*0.055+self.bob)*5)
        cy=self.rect.y+by; col=ITEM_COL[self.kind]
        # glow
        ga=int(40+30*math.sin(tick*0.07+self.bob))
        gs=pygame.Surface((44,44),pygame.SRCALPHA)
        pygame.draw.circle(gs,(*col,ga),(22,22),20)
        surf.blit(gs,(sx-9,cy-9))
        if self.kind=="candy":
            pygame.draw.circle(surf,col,(sx+13,cy+13),11)
            pygame.draw.circle(surf,WHITE,(sx+13,cy+13),11,2)
            pygame.draw.circle(surf,WHITE,(sx+8,cy+8),4)
        elif self.kind=="basket":
            pygame.draw.ellipse(surf,col,(sx+2,cy+7,22,15))
            pygame.draw.arc(surf,DBROWN,(sx+5,cy+1,16,14),0,math.pi,3)
            pygame.draw.rect(surf,bright(col,-40),(sx+2,cy+14,22,8),border_radius=3)
        elif self.kind=="gem":
            pts=[(sx+13,cy),(sx+24,cy+9),(sx+20,cy+24),(sx+6,cy+24),(sx+2,cy+9)]
            pygame.draw.polygon(surf,col,pts)
            pygame.draw.polygon(surf,WHITE,pts,2)
            pygame.draw.line(surf,WHITE,(sx+13,cy+2),(sx+18,cy+11),2)
        elif self.kind=="heart":
            pygame.draw.circle(surf,(255,60,100),(sx+8,cy+9),7)
            pygame.draw.circle(surf,(255,60,100),(sx+18,cy+9),7)
            pygame.draw.polygon(surf,(255,60,100),[(sx+1,cy+12),(sx+13,cy+26),(sx+25,cy+12)])
            pygame.draw.circle(surf,(255,150,170),(sx+7,cy+7),3)
        elif self.kind=="shield":
            pts=[(sx+13,cy),(sx+24,cy+8),(sx+20,cy+22),(sx+13,cy+26),(sx+6,cy+22),(sx+2,cy+8)]
            pygame.draw.polygon(surf,(80,180,255),pts)
            pygame.draw.polygon(surf,WHITE,pts,2)
            pygame.draw.line(surf,WHITE,(sx+13,cy+4),(sx+13,cy+22),2)
        else:  # stick
            pygame.draw.line(surf,col,(sx+5,cy+22),(sx+21,cy+5),4)
            pygame.draw.circle(surf,(180,255,90),(sx+21,cy+5),6)

# ═══════════════════════════════════════════════════════════════════════════════
#  OBSTACLES
# ═══════════════════════════════════════════════════════════════════════════════
class Boulder:
    def __init__(self,x,y,speed,patrol=300):
        self.x=float(x); self.y=float(y); self.r=24
        self.speed=speed; self.dir=1; self.angle=0.0
        self.start_x=x; self.patrol=patrol
        self.rect=pygame.Rect(int(x)-self.r,int(y)-self.r,self.r*2,self.r*2)

    def update(self):
        self.x+=self.speed*self.dir; self.angle+=self.speed*0.04
        if self.x>self.start_x+self.patrol or self.x<self.start_x: self.dir*=-1
        self.rect.center=(int(self.x),int(self.y))

    def draw(self,surf,cam):
        sx=int(self.x)-cam; sy=int(self.y)
        if sx<-60 or sx>SW+60: return
        pygame.draw.ellipse(surf,(0,0,0,40),pygame.Rect(sx-self.r+6,sy+self.r-4,self.r*2-6,10))
        pygame.draw.circle(surf,(85,75,65),(sx,sy),self.r)
        pygame.draw.circle(surf,(115,105,95),(sx,sy),self.r,3)
        for i in range(5):
            a=self.angle+i*math.pi*2/5
            ex=int(sx+math.cos(a)*(self.r-7)); ey=int(sy+math.sin(a)*(self.r-7))
            pygame.draw.line(surf,(55,45,35),(sx,sy),(ex,ey),2)
        pygame.draw.circle(surf,(145,135,125),(sx-7,sy-7),5)

class SpikeTrap:
    def __init__(self,x,y,count=4):
        self.x=x; self.y=y; self.count=count
        self.rect=pygame.Rect(x,y-22,count*18,24)
        self.pulse=random.uniform(0,math.pi*2)

    def draw(self,surf,cam,tick):
        sx=self.x-cam
        if sx<-80 or sx>SW+80: return
        ga=int(70+50*math.sin(tick*0.09+self.pulse))
        gs=pygame.Surface((self.count*18+12,32),pygame.SRCALPHA)
        pygame.draw.rect(gs,(255,50,50,ga),(0,0,self.count*18+12,32),border_radius=5)
        surf.blit(gs,(sx-6,self.y-24))
        for i in range(self.count):
            bx=sx+i*18+4
            pygame.draw.rect(surf,(75,75,85),(bx,self.y-5,10,7))
            pts=[(bx,self.y-5),(bx+10,self.y-5),(bx+5,self.y-24)]
            pygame.draw.polygon(surf,(195,200,215),pts)
            pygame.draw.polygon(surf,WHITE,pts,1)
            pygame.draw.circle(surf,(255,100,100),(bx+5,self.y-24),3)

class FlyingEnemy:
    def __init__(self,x,y,patrol=280,speed=2.2):
        self.x=float(x); self.y=float(y); self.base_y=float(y)
        self.start_x=x; self.patrol=patrol; self.speed=speed
        self.dir=1; self.anim=random.randint(0,40)
        self.rect=pygame.Rect(int(x)-20,int(y)-15,40,30)
        self.hp=2

    def update(self):
        self.x+=self.speed*self.dir; self.anim+=1
        self.y=self.base_y+math.sin(self.anim*0.07)*22
        if self.x>self.start_x+self.patrol or self.x<self.start_x: self.dir*=-1
        self.rect.center=(int(self.x),int(self.y))

    def draw(self,surf,cam):
        sx=int(self.x)-cam; sy=int(self.y)
        if sx<-60 or sx>SW+60: return
        wf=int(math.sin(self.anim*0.28)*12)
        pygame.draw.ellipse(surf,(160,50,185),(sx-30,sy-9+wf,26,16))
        pygame.draw.ellipse(surf,(160,50,185),(sx+4, sy-9-wf,26,16))
        pygame.draw.ellipse(surf,(200,100,220),(sx-28,sy-7+wf,22,12))
        pygame.draw.ellipse(surf,(200,100,220),(sx+6, sy-7-wf,22,12))
        pygame.draw.ellipse(surf,(130,35,155),(sx-13,sy-11,26,22))
        pygame.draw.ellipse(surf,(175,75,195),(sx-11,sy-9,22,18))
        pygame.draw.circle(surf,RED,(sx-5,sy-2),4)
        pygame.draw.circle(surf,RED,(sx+5,sy-2),4)
        pygame.draw.circle(surf,YELLOW,(sx-5,sy-2),2)
        pygame.draw.circle(surf,YELLOW,(sx+5,sy-2),2)
        # HP dots
        for i in range(self.hp):
            pygame.draw.circle(surf,HP_G,(sx-4+i*8,sy-18),3)

# ═══════════════════════════════════════════════════════════════════════════════
#  BULLET
# ═══════════════════════════════════════════════════════════════════════════════
class Bullet:
    W=14; H=6
    def __init__(self,x,y,direction):
        self.x=float(x); self.y=float(y)
        self.dir=direction          # 1=right, -1=left
        self.speed=14.0
        self.alive=True
        self.rect=pygame.Rect(int(x),int(y),self.W,self.H)

    def update(self,world_w):
        self.x+=self.speed*self.dir
        self.rect.x=int(self.x); self.rect.y=int(self.y)
        if self.x<0 or self.x>world_w: self.alive=False

    def draw(self,surf,cam):
        sx=int(self.x)-cam; sy=int(self.y)
        if sx<-20 or sx>SW+20: return
        # glowing bullet
        gs=pygame.Surface((self.W+8,self.H+8),pygame.SRCALPHA)
        pygame.draw.ellipse(gs,(255,200,50,80),(0,0,self.W+8,self.H+8))
        surf.blit(gs,(sx-4,sy-4))
        pygame.draw.ellipse(surf,(255,230,80),(sx,sy,self.W,self.H))
        pygame.draw.ellipse(surf,WHITE,(sx,sy,self.W,self.H),1)
        # trail
        for i in range(1,5):
            tx=sx-self.dir*i*4; a=max(0,180-i*40)
            ts=pygame.Surface((6,4),pygame.SRCALPHA)
            ts.fill((255,180,30,a)); surf.blit(ts,(tx,sy+1))


# ═══════════════════════════════════════════════════════════════════════════════
#  ANIMAL ENEMIES  (Cat, Dog, Dragon)
# ═══════════════════════════════════════════════════════════════════════════════
class AnimalEnemy:
    TYPES = {
        "cat":    dict(hp=2, speed=2.8, dmg=10, score=40,  size=(44,34),
                       col=(200,160,120), eye=(60,30,10),  label="Cat"),
        "dog":    dict(hp=3, speed=3.4, dmg=15, score=60,  size=(52,36),
                       col=(140,90,40),   eye=(30,15,5),   label="Dog"),
        "dragon": dict(hp=6, speed=2.0, dmg=25, score=150, size=(64,48),
                       col=(40,160,60),   eye=(200,20,20), label="Dragon"),
    }

    def __init__(self, x, y, kind="cat"):
        cfg=self.TYPES[kind]
        self.kind=kind; self.x=float(x); self.y=float(y)
        self.hp=cfg["hp"]; self.max_hp=cfg["hp"]
        self.speed=cfg["speed"]; self.dmg=cfg["dmg"]
        self.score_val=cfg["score"]
        self.col=cfg["col"]; self.eye=cfg["eye"]
        self.w,self.h=cfg["size"]
        self.dir=-1          # always chase player
        self.anim=random.randint(0,60)
        self.on_ground=False
        self.vy=0.0
        self.alive=True
        self.hit_flash=0
        self.alert=False     # true when player is nearby
        # dragon can shoot fireballs
        self.fire_timer=0
        self.fireballs=[]    # list of [x,y,vx,life]
        self.rect=pygame.Rect(int(x),int(y),self.w,self.h)

    def update(self, player_x, player_y, platforms, world_w):
        if not self.alive: return
        self.anim+=1
        if self.hit_flash>0: self.hit_flash-=1
        if self.fire_timer>0: self.fire_timer-=1

        # chase player
        dx=player_x-self.x
        self.alert=abs(dx)<500
        if self.alert:
            self.dir=1 if dx>0 else -1
            self.x+=self.speed*self.dir
        else:
            # idle patrol
            self.x+=self.speed*0.4*self.dir
            if self.x<50 or self.x>world_w-50: self.dir*=-1

        # gravity
        self.vy=min(self.vy+GRAVITY,20)
        self.y+=self.vy
        self.on_ground=False
        yr=pygame.Rect(int(self.x),int(self.y),self.w,self.h)
        for p in platforms:
            if yr.colliderect(p.rect) and self.vy>0:
                self.y=p.rect.top-self.h; self.vy=0; self.on_ground=True
        if self.y+self.h>=GROUND_Y:
            self.y=GROUND_Y-self.h; self.vy=0; self.on_ground=True

        # dog jumps over obstacles
        if self.kind=="dog" and self.on_ground and self.alert and abs(dx)<200:
            self.vy=-12

        # dragon shoots fireballs
        if self.kind=="dragon" and self.alert and self.fire_timer==0:
            self.fire_timer=120
            self.fireballs.append([self.x+self.w//2, self.y+self.h//2,
                                    self.dir*5.0, 90])
        for fb in self.fireballs[:]:
            fb[0]+=fb[2]; fb[3]-=1
            if fb[3]<=0: self.fireballs.remove(fb)

        self.x=max(0,min(self.x,world_w-self.w))
        self.rect=pygame.Rect(int(self.x),int(self.y),self.w,self.h)

    def take_hit(self):
        self.hp-=1; self.hit_flash=12
        if self.hp<=0: self.alive=False

    def draw(self,surf,cam):
        if not self.alive: return
        sx=int(self.x)-cam; sy=int(self.y)
        if sx<-80 or sx>SW+80: return

        flash=self.hit_flash>0 and (self.hit_flash//3)%2==0
        col=WHITE if flash else self.col
        dark=tuple(max(0,v-50) for v in col)
        hi  =tuple(min(255,v+60) for v in col)

        if self.kind=="cat":
            self._draw_cat(surf,sx,sy,col,dark,hi)
        elif self.kind=="dog":
            self._draw_dog(surf,sx,sy,col,dark,hi)
        elif self.kind=="dragon":
            self._draw_dragon(surf,sx,sy,col,dark,hi)

        # HP bar
        bw=self.w; bh=5
        pygame.draw.rect(surf,(60,10,10),(sx,sy-10,bw,bh),border_radius=2)
        pygame.draw.rect(surf,HP_R,(sx,sy-10,int(bw*self.hp/self.max_hp),bh),border_radius=2)
        pygame.draw.rect(surf,WHITE,(sx,sy-10,bw,bh),1,border_radius=2)

        # alert indicator
        if self.alert:
            a=int(180+75*math.sin(self.anim*0.15))
            es=F16.render("!",True,(255,80,80))
            es.set_alpha(a); surf.blit(es,(sx+self.w//2-4,sy-26))

        # dragon fireballs
        for fb in self.fireballs:
            fx=int(fb[0])-cam; fy=int(fb[1])
            if -20<fx<SW+20:
                a2=int(fb[3]*2.8)
                gs=pygame.Surface((24,24),pygame.SRCALPHA)
                pygame.draw.circle(gs,(255,120,20,min(255,a2)),(12,12),10)
                surf.blit(gs,(fx-12,fy-12))
                pygame.draw.circle(surf,(255,200,50),(fx,fy),6)
                pygame.draw.circle(surf,WHITE,(fx,fy),6,1)

    def _draw_cat(self,surf,sx,sy,col,dark,hi):
        # body
        pygame.draw.ellipse(surf,col,(sx+4,sy+12,36,22))
        pygame.draw.ellipse(surf,hi,(sx+4,sy+12,36,8))
        # head
        pygame.draw.circle(surf,col,(sx+22,sy+10),14)
        pygame.draw.circle(surf,hi,(sx+16,sy+5),5)
        # ears
        pygame.draw.polygon(surf,col,[(sx+10,sy+2),(sx+6,sy-10),(sx+16,sy+2)])
        pygame.draw.polygon(surf,col,[(sx+30,sy+2),(sx+36,sy-10),(sx+26,sy+2)])
        pygame.draw.polygon(surf,PINK,[(sx+11,sy+1),(sx+8,sy-7),(sx+16,sy+1)])
        pygame.draw.polygon(surf,PINK,[(sx+29,sy+1),(sx+34,sy-7),(sx+26,sy+1)])
        # eyes
        ex=sx+26 if self.dir==1 else sx+16
        pygame.draw.circle(surf,self.eye,(ex,sy+8),4)
        pygame.draw.circle(surf,WHITE,(ex+1,sy+7),1)
        # nose
        pygame.draw.circle(surf,PINK,(sx+22,sy+13),3)
        # whiskers
        pygame.draw.line(surf,LGRAY,(sx+22,sy+13),(sx+6,sy+10),1)
        pygame.draw.line(surf,LGRAY,(sx+22,sy+13),(sx+38,sy+10),1)
        # tail
        swing=int(math.sin(self.anim*0.12)*8)
        pygame.draw.arc(surf,col,pygame.Rect(sx-10,sy+20+swing,20,20),0,math.pi,3)
        # legs
        lsw=int(math.sin(self.anim*0.25)*5)
        pygame.draw.rect(surf,dark,(sx+6, sy+30+lsw,8,10),border_radius=3)
        pygame.draw.rect(surf,dark,(sx+16,sy+30-lsw,8,10),border_radius=3)
        pygame.draw.rect(surf,dark,(sx+26,sy+30+lsw,8,10),border_radius=3)

    def _draw_dog(self,surf,sx,sy,col,dark,hi):
        # body
        pygame.draw.ellipse(surf,col,(sx+2,sy+14,48,22))
        pygame.draw.ellipse(surf,hi,(sx+2,sy+14,48,8))
        # head
        pygame.draw.ellipse(surf,col,(sx+28,sy+2,28,24))
        pygame.draw.ellipse(surf,hi,(sx+30,sy+4,14,8))
        # snout
        pygame.draw.ellipse(surf,dark,(sx+38,sy+14,16,12))
        pygame.draw.circle(surf,BLACK,(sx+44,sy+16),3)
        # ears (floppy)
        pygame.draw.ellipse(surf,dark,(sx+28,sy+2,10,18))
        pygame.draw.ellipse(surf,dark,(sx+46,sy+2,10,18))
        # eyes
        pygame.draw.circle(surf,self.eye,(sx+36,sy+10),4)
        pygame.draw.circle(surf,WHITE,(sx+37,sy+9),1)
        # tail wag
        tw=int(math.sin(self.anim*0.2)*12)
        pygame.draw.arc(surf,col,pygame.Rect(sx-8,sy+10+tw,18,18),0,math.pi,4)
        # legs
        lsw=int(math.sin(self.anim*0.28)*6)
        for lx in [sx+6,sx+16,sx+28,sx+38]:
            pygame.draw.rect(surf,dark,(lx,sy+32+(lsw if lx<sx+20 else -lsw),9,12),border_radius=3)

    def _draw_dragon(self,surf,sx,sy,col,dark,hi):
        # body
        pygame.draw.ellipse(surf,col,(sx+4,sy+16,56,32))
        pygame.draw.ellipse(surf,hi,(sx+4,sy+16,56,12))
        # belly
        pygame.draw.ellipse(surf,(200,220,180),(sx+12,sy+24,36,18))
        # neck + head
        pygame.draw.rect(surf,col,(sx+44,sy+6,18,20),border_radius=6)
        pygame.draw.ellipse(surf,col,(sx+42,sy+2,28,22))
        pygame.draw.ellipse(surf,hi,(sx+44,sy+4,16,8))
        # horns
        pygame.draw.polygon(surf,dark,[(sx+46,sy+2),(sx+44,sy-10),(sx+50,sy+2)])
        pygame.draw.polygon(surf,dark,[(sx+58,sy+2),(sx+62,sy-10),(sx+56,sy+2)])
        # eyes (glowing red)
        pygame.draw.circle(surf,(255,30,30),(sx+52,sy+10),5)
        pygame.draw.circle(surf,(255,150,0),(sx+52,sy+10),3)
        pygame.draw.circle(surf,WHITE,(sx+53,sy+9),1)
        # wings
        wf=int(math.sin(self.anim*0.18)*14)
        pygame.draw.polygon(surf,dark,[(sx+20,sy+16),(sx+2,sy-10+wf),(sx+14,sy+16)])
        pygame.draw.polygon(surf,dark,[(sx+36,sy+16),(sx+54,sy-10-wf),(sx+42,sy+16)])
        pygame.draw.polygon(surf,col,[(sx+20,sy+16),(sx+4,sy-6+wf),(sx+14,sy+16)])
        pygame.draw.polygon(surf,col,[(sx+36,sy+16),(sx+52,sy-6-wf),(sx+42,sy+16)])
        # tail spikes
        for i in range(3):
            tx=sx+i*8; ty=sy+36
            pygame.draw.polygon(surf,dark,[(tx,ty),(tx+4,ty),(tx+2,ty-8)])
        # legs
        lsw=int(math.sin(self.anim*0.2)*6)
        for lx in [sx+10,sx+24,sx+38,sx+50]:
            pygame.draw.rect(surf,dark,(lx,sy+44+(lsw if lx<sx+30 else -lsw),10,14),border_radius=4)

class Particle:
    def __init__(self,x,y,col,vx=None,vy=None,life=None,sz=None):
        self.x=float(x); self.y=float(y)
        self.vx=vx if vx is not None else random.uniform(-4,4)
        self.vy=vy if vy is not None else random.uniform(-7,-1)
        self.life=life or random.randint(20,50); self.ml=self.life
        self.col=col; self.sz=sz or random.randint(3,8)
    def update(self): self.x+=self.vx; self.y+=self.vy; self.vy+=0.25; self.life-=1
    def draw(self,surf,cam):
        a=int(255*self.life/self.ml)
        s=pygame.Surface((self.sz,self.sz),pygame.SRCALPHA)
        s.fill((*self.col,a)); surf.blit(s,(int(self.x)-cam,int(self.y)))

# ═══════════════════════════════════════════════════════════════════════════════
#  FINISH FLAG
# ═══════════════════════════════════════════════════════════════════════════════
class FinishFlag:
    def __init__(self,x):
        self.x=x; self.zone=pygame.Rect(x-30,GROUND_Y-190,110,190)

    def draw(self,surf,cam,tick):
        sx=self.x-cam
        if sx<-120 or sx>SW+120: return
        # glow pillar
        ga=int(55+40*math.sin(tick*0.07))
        gs=pygame.Surface((120,210),pygame.SRCALPHA)
        pygame.draw.rect(gs,(255,215,0,ga),(5,0,110,210),border_radius=12)
        surf.blit(gs,(sx-38,GROUND_Y-208))
        # pole with 3-D shading
        pygame.draw.rect(surf,DBROWN,(sx,GROUND_Y-178,10,178))
        pygame.draw.rect(surf,BROWN,(sx+1,GROUND_Y-178,5,178))
        pygame.draw.rect(surf,GOLD,(sx,GROUND_Y-178,10,178),1)
        # waving flag
        wave=int(math.sin(tick*0.13)*9)
        fp=[(sx+10,GROUND_Y-176),(sx+70,GROUND_Y-152+wave),(sx+10,GROUND_Y-128)]
        pygame.draw.polygon(surf,RED,fp)
        pygame.draw.polygon(surf,bright(RED,60),fp,2)
        fl=F16.render("FINISH",True,WHITE)
        surf.blit(fl,(sx+13,GROUND_Y-168))
        # checkered base
        for row in range(2):
            for col2 in range(8):
                c2=WHITE if (row+col2)%2==0 else BLACK
                pygame.draw.rect(surf,c2,(sx-32+col2*12,GROUND_Y-5+row*12,12,12))
        # bouncing arrow
        ay=GROUND_Y-200+int(math.sin(tick*0.11)*7)
        pygame.draw.polygon(surf,GOLD,[(sx+14,ay+18),(sx+24,ay),(sx+34,ay+18)])
        pygame.draw.polygon(surf,WHITE,[(sx+14,ay+18),(sx+24,ay),(sx+34,ay+18)],1)

# ═══════════════════════════════════════════════════════════════════════════════
#  CHARACTER SPRITE RENDERER  (shared by select screen + in-game)
# ═══════════════════════════════════════════════════════════════════════════════
def draw_character_sprite(surf, char, sx, sy, scale=1.0, facing=1,
                          swing=0, jump_anim=0, anim=0):
    """Draw a character at screen position (sx,sy). scale=1 → 38×50px."""
    s = scale
    W = int(38*s); H = int(50*s)

    skin  = char["skin"];  hair  = char["hair"]
    body  = char["body"];  legs  = char["legs"]
    shoes = char["shoes"]; extra = char["extra"]

    def r(x,y,w,h,**kw): pygame.draw.rect(surf,kw.get("c",WHITE),
                                           (sx+int(x*s),sy+int(y*s),max(1,int(w*s)),max(1,int(h*s))),
                                           border_radius=kw.get("br",0))
    def circ(x,y,rad,col): pygame.draw.circle(surf,col,(sx+int(x*s),sy+int(y*s)),max(1,int(rad*s)))
    def line(x1,y1,x2,y2,col,w2=2):
        pygame.draw.line(surf,col,(sx+int(x1*s),sy+int(y1*s)),(sx+int(x2*s),sy+int(y2*s)),max(1,int(w2*s)))

    # shadow
    pygame.draw.ellipse(surf,(0,0,0,40),pygame.Rect(sx+int(3*s),sy+int(46*s),int(32*s),int(7*s)))

    # legs
    r(4, 33+swing, 13,17, c=legs, br=3)
    r(21,33-swing, 13,17, c=legs, br=3)
    r(3, 47+swing, 15, 6, c=shoes,br=2)
    r(20,47-swing, 15, 6, c=shoes,br=2)

    # body
    r(2,17,34,20, c=body, br=4)
    r(2,17,34, 5, c=bright(body,70), br=4)
    r(2,32,34, 5, c=bright(body,-60),br=4)

    # character-specific body detail
    if extra=="badge":
        r(10,20,10,8, c=(255,215,0), br=2)
        circ(15,24,3,(255,215,0))
    elif extra in("girl","ponytail"):
        r(2,17,34,4, c=bright(body,40), br=4)   # collar ruffle

    # belt
    r(2,31,34,4, c=bright(shoes,20))

    # head
    circ(19,12,13,skin)
    circ(14, 8, 5,bright(skin,50))   # highlight

    # hair / head accessory
    if extra=="cap":
        r(5,1,28,9, c=hair, br=3)
        r(2,1,6,5,  c=hair, br=2)   # brim
    elif extra=="ponytail":
        r(6,1,26,9, c=hair, br=3)
        # ponytail
        pygame.draw.arc(surf,hair,pygame.Rect(sx+int(28*s),sy+int(2*s),int(12*s),int(18*s)),
                        -math.pi*0.3,math.pi*0.5,max(1,int(3*s)))
    elif extra=="beard":
        r(6,1,26,9, c=hair, br=3)   # white hair
        r(6,20,26,8, c=hair, br=3)  # beard
    elif extra=="bun":
        r(6,1,26,9, c=hair, br=3)
        circ(19,-2,7,hair)           # bun on top
    elif extra=="badge":
        r(6,1,26,9, c=hair, br=3)
        r(5,0,28,5, c=bright(hair,-20), br=2)  # police cap peak

    # eyes
    ex2 = 24 if facing==1 else 12
    circ(ex2,10,3,BLACK)
    circ(ex2+1,9,1,WHITE)

    # grandpa/grandma glasses
    if extra in("beard","bun"):
        pygame.draw.rect(surf,(180,200,220),(sx+int(10*s),sy+int(8*s),int(8*s),int(6*s)),
                         max(1,int(1*s)),border_radius=2)
        pygame.draw.rect(surf,(180,200,220),(sx+int(20*s),sy+int(8*s),int(8*s),int(6*s)),
                         max(1,int(1*s)),border_radius=2)
        line(18,11,20,11,(180,200,220),1)

    # jump arc
    if jump_anim>0:
        pygame.draw.arc(surf,YELLOW,pygame.Rect(sx+int(-7*s),sy+int(43*s),
                                                 int(52*s),int(14*s)),0,math.pi,max(1,int(3*s)))

    # name tag (only when scale>=1)
    if scale>=1.0:
        ns=F16.render(char["label"],True,WHITE)
        surf.blit(ns,(sx+W//2-ns.get_width()//2, sy-18))


# ═══════════════════════════════════════════════════════════════════════════════
#  CHARACTER SELECT SCREEN
# ═══════════════════════════════════════════════════════════════════════════════
def draw_char_select(surf, tick, name_input, sel_idx, confirm_btn, back_btn):
    grad(surf,(8,18,45),(20,55,25),pygame.Rect(0,0,SW,SH))

    # animated stars
    for i in range(35):
        sx2=(i*137+tick)%SW; sy2=(i*97)%(SH//2)
        br=int(100+80*math.sin(tick*0.05+i))
        pygame.draw.circle(surf,(br,br,br),(sx2,sy2),1)

    shadow_text(surf,"CREATE YOUR HERO",F60,GOLD,SW//2-255,28,(0,0,0),4)
    pygame.draw.line(surf,GOLD,(60,88),(SW-60,88),2)

    # ── Name input ──────────────────────────────────────────────────────────
    shadow_text(surf,"Your Name:",F28,LBLUE,SW//2-280,105)
    nb=pygame.Rect(SW//2-100,100,380,46)
    pygame.draw.rect(surf,(15,30,65),nb,border_radius=10)
    pygame.draw.rect(surf,GOLD,nb,2,border_radius=10)
    display=name_input if name_input else "Enter name..."
    col=WHITE if name_input else GRAY
    cursor="|" if (tick//28)%2==0 else ""
    ns=F36.render(display+cursor,True,col)
    surf.blit(ns,ns.get_rect(center=nb.center))

    # ── Character cards ──────────────────────────────────────────────────────
    n=len(CHARACTERS); card_w=150; card_h=220; gap=18
    total=n*card_w+(n-1)*gap; start_x=SW//2-total//2

    for i,ch in enumerate(CHARACTERS):
        cx2=start_x+i*(card_w+gap); cy2=165
        selected=(i==sel_idx)

        # card background
        card=pygame.Rect(cx2,cy2,card_w,card_h)
        if selected:
            # glowing selected card
            ga=int(60+40*math.sin(tick*0.1))
            gs=pygame.Surface((card_w+16,card_h+16),pygame.SRCALPHA)
            pygame.draw.rect(gs,(*ch["body"],ga),(0,0,card_w+16,card_h+16),border_radius=14)
            surf.blit(gs,(cx2-8,cy2-8))
            grad(surf,bright(ch["body"],-60),(10,20,45),card)
            pygame.draw.rect(surf,GOLD,card,3,border_radius=12)
        else:
            grad(surf,(15,28,58),(8,14,30),card)
            pygame.draw.rect(surf,(60,80,120),card,2,border_radius=12)

        # character preview (scale 2.2)
        draw_character_sprite(surf,ch,cx2+card_w//2-42,cy2+14,scale=2.2,facing=1)

        # name label
        nl=F28.render(ch["label"],True,GOLD if selected else LGRAY)
        surf.blit(nl,nl.get_rect(center=(cx2+card_w//2,cy2+card_h-52)))

        # desc
        dl=F16.render(ch["desc"],True,LBLUE if selected else GRAY)
        surf.blit(dl,dl.get_rect(center=(cx2+card_w//2,cy2+card_h-30)))

        # selected tick
        if selected:
            pygame.draw.circle(surf,GOLD,(cx2+card_w-16,cy2+16),10)
            pygame.draw.circle(surf,WHITE,(cx2+card_w-16,cy2+16),10,2)
            pygame.draw.line(surf,WHITE,(cx2+card_w-21,cy2+16),(cx2+card_w-17,cy2+20),2)
            pygame.draw.line(surf,WHITE,(cx2+card_w-17,cy2+20),(cx2+card_w-11,cy2+12),2)

    # hint
    hint=F22.render("Click a character to select   |   Arrow keys to browse",True,(160,190,215))
    surf.blit(hint,hint.get_rect(center=(SW//2,SH-80)))

    confirm_btn.draw(surf)
    back_btn.draw(surf)


# ═══════════════════════════════════════════════════════════════════════════════
#  PLAYER  (Mario-style: 3 lives, energy, shield, stomp)
# ═══════════════════════════════════════════════════════════════════════════════
class Player:
    W=38; H=50; MAX_HP=100; MAX_EN=100

    def __init__(self, lives=3, char=None, name="Hero"):
        self.x=130.0; self.y=float(GROUND_Y-self.H-2)
        self.vx=0.0; self.vy=0.0
        self.on_ground=False; self.facing=1
        self.hp=self.MAX_HP; self.energy=self.MAX_EN
        self.lives=lives; self.score=0; self.items=[]
        self.invincible=0; self.shield=0
        self.anim=0; self.jump_anim=0
        self.dead=False; self.stomping=False
        self.low_en_warn=0; self.hit_flash=0
        self.char=char or CHARACTERS[0]
        self.name=name

    @property
    def rect(self): return pygame.Rect(int(self.x),int(self.y),self.W,self.H)

    def update(self,keys,platforms,world_w):
        if self.dead: return
        self.anim+=1
        if self.invincible>0: self.invincible-=1
        if self.jump_anim>0:  self.jump_anim-=1
        if self.shield>0:     self.shield-=1
        if self.hit_flash>0:  self.hit_flash-=1

        # energy drain
        self.energy=max(0,self.energy-0.035)
        if self.energy<20: self.low_en_warn=(self.low_en_warn+1)%50

        speed=6.0 if self.energy>15 else 3.2
        self.vx=0.0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: self.vx=-speed; self.facing=-1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.vx= speed; self.facing= 1

        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.vy=JUMP_POWER; self.on_ground=False
            self.jump_anim=20; self.energy=max(0,self.energy-3)
            play(SND_JUMP)

        self.vy=min(self.vy+GRAVITY,24)

        # X
        self.x+=self.vx
        xr=pygame.Rect(int(self.x),int(self.y),self.W,self.H)
        for p in platforms:
            if xr.colliderect(p.rect):
                if self.vx>0: self.x=p.rect.left-self.W
                elif self.vx<0: self.x=p.rect.right

        # Y
        self.y+=self.vy; self.on_ground=False
        yr=pygame.Rect(int(self.x),int(self.y),self.W,self.H)
        for p in platforms:
            if yr.colliderect(p.rect):
                if self.vy>0:
                    self.y=p.rect.top-self.H; self.vy=0; self.on_ground=True
                elif self.vy<0:
                    self.y=p.rect.bottom; self.vy=0

        if self.y+self.H>=GROUND_Y:
            self.y=GROUND_Y-self.H; self.vy=0; self.on_ground=True

        self.x=max(0,min(self.x,world_w-self.W))

    def take_damage(self,dmg):
        if self.invincible>0 or self.shield>0: return False
        self.hp=max(0,self.hp-dmg); self.invincible=70; self.hit_flash=12
        play(SND_HIT)
        # every obstacle hit costs one life directly (Mario-style)
        self._lose_life()
        return True

    def _lose_life(self):
        self.lives-=1; play(SND_DEATH)
        if self.lives<=0:
            self.lives=0; self.dead=True   # triggers GAME_OVER
        else:
            self.hp=self.MAX_HP; self.energy=self.MAX_EN
            self.invincible=150            # longer grace period after losing a life
            self.x=130.0; self.y=float(GROUND_Y-self.H-2)

    def draw(self,surf,cam):
        sx=int(self.x)-cam; sy=int(self.y)
        if self.invincible>0 and (self.invincible//5)%2==1: return

        # shield aura
        if self.shield>0:
            sa=int(80+60*math.sin(self.anim*0.2))
            ss=pygame.Surface((self.W+24,self.H+24),pygame.SRCALPHA)
            pygame.draw.ellipse(ss,(80,180,255,sa),(0,0,self.W+24,self.H+24))
            surf.blit(ss,(sx-12,sy-12))

        # hit flash
        if self.hit_flash>0:
            hf=pygame.Surface((self.W+8,self.H+8),pygame.SRCALPHA)
            hf.fill((255,50,50,140)); surf.blit(hf,(sx-4,sy-4))

        # draw character sprite
        swing=int(math.sin(self.anim*0.3)*9) if abs(self.vx)>0.3 else 0
        draw_character_sprite(surf,self.char,sx,sy,scale=1.0,
                              facing=self.facing,swing=swing,
                              jump_anim=self.jump_anim,anim=self.anim)

        # custom name tag
        ns=F16.render(self.name,True,WHITE)
        surf.blit(ns,(sx+self.W//2-ns.get_width()//2, sy-22))

        # score bubble
        sc=F16.render(f"+{self.score}",True,GOLD)
        surf.blit(sc,(sx+2,sy-36))

        # low energy red glow
        if self.energy<20 and self.low_en_warn<25:
            lg=pygame.Surface((self.W+22,self.H+22),pygame.SRCALPHA)
            la=int(100*math.sin(self.anim*0.22))
            pygame.draw.rect(lg,(255,40,40,max(0,la)),(0,0,self.W+22,self.H+22),border_radius=8)
            surf.blit(lg,(sx-11,sy-11))

# ═══════════════════════════════════════════════════════════════════════════════
#  WORLD GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════
def generate_world(level_idx):
    cfg=LEVELS[level_idx]; ww=cfg["world_w"]; pk=cfg["plat_kind"]
    gap_base=cfg.get("gap_base",180)
    bspeed=cfg.get("boulder_speed",(2.0,3.0))
    plat_w_max=max(80,160-level_idx*16)
    plat_w_min=max(55,90-level_idx*6)

    platforms=[Platform(0,GROUND_Y,ww,35,"ground")]
    x=200
    while x<ww-300:
        w=random.randint(plat_w_min,plat_w_max)
        y=random.randint(GROUND_Y-220,GROUND_Y-80)
        platforms.append(Platform(x,y,w,20,pk))
        x+=w+random.randint(gap_base,gap_base+80)

    # pits
    pits=[]
    n_pits=cfg["pits"]
    if n_pits>0:
        pit_positions=sorted(random.sample(range(400,ww-400,180),min(n_pits,8)))
        for px2 in pit_positions:
            pw=random.randint(80,110+level_idx*18)
            pits.append(Pit(px2,pw))

    # collectibles
    collectibles=[]
    for p in platforms:
        if p.kind!="ground":
            for _ in range(random.randint(1,3)):
                kind=random.choices(["candy","basket","stick","gem","heart","shield"],
                                    weights=[4,3,5,2,2,1])[0]
                ix=p.rect.x+random.randint(5,max(6,p.rect.w-30))
                collectibles.append(Collectible(ix,p.rect.y-28,kind))
    for _ in range(35):
        kind=random.choices(["candy","basket","stick","gem","heart"],weights=[4,3,5,2,2])[0]
        collectibles.append(Collectible(random.randint(80,ww-80),GROUND_Y-28,kind))

    # boulders — speed from level config
    boulders=[]
    for i in range(cfg["boulders"]):
        bx=350+i*(ww//max(cfg["boulders"],1))
        spd=random.uniform(bspeed[0],bspeed[1])
        boulders.append(Boulder(bx,GROUND_Y-24,spd,random.randint(200,350)))

    # spikes — denser per level
    spikes=[]
    for i in range(cfg["spikes"]):
        sx2=280+i*(ww//max(cfg["spikes"],1))
        spikes.append(SpikeTrap(sx2,GROUND_Y,random.randint(3,4+level_idx)))

    # flying enemies — faster per level
    enemies=[]
    for i in range(cfg["flyers"]):
        ex=500+i*(ww//max(cfg["flyers"],1))
        spd=random.uniform(2.0+level_idx*0.3,3.0+level_idx*0.4)
        fe=FlyingEnemy(ex,GROUND_Y-160-random.randint(0,80),280,spd)
        enemies.append(fe)

    finish=FinishFlag(ww-160)

    # animal enemies — scale count and type with level
    animals=[]
    animal_counts={"cat":2+level_idx,"dog":1+level_idx,"dragon":level_idx//2}
    for kind,count in animal_counts.items():
        for i in range(count):
            ax=random.randint(300,ww-300)
            ay=GROUND_Y-AnimalEnemy.TYPES[kind]["size"][1]-2
            animals.append(AnimalEnemy(ax,ay,kind))

    return platforms,pits,collectibles,boulders,spikes,enemies,animals,finish,ww

# ═══════════════════════════════════════════════════════════════════════════════
#  PARALLAX BACKGROUND
# ═══════════════════════════════════════════════════════════════════════════════
def draw_bg(surf,cam,level_idx,tick):
    cfg=LEVELS[level_idx]
    grad(surf,cfg["sky_t"],cfg["sky_b"],pygame.Rect(0,0,SW,SH))

    theme=cfg["theme"]
    if theme=="jungle":
        for i in range(9):
            cx=(130+i*145-int(cam*0.1))%(SW+240)-120
            cy=35+(i%3)*26
            for dx,dy,r in [(-24,0,26),(0,-13,32),(24,0,26),(0,11,22)]:
                pygame.draw.circle(surf,(235,245,255),(cx+dx,cy+dy),r)
        for i in range(16):
            tx=(60+i*210-int(cam*0.32))%(SW+350)-175
            ty=GROUND_Y-95
            pygame.draw.rect(surf,DBROWN,(tx+15,ty+48,14,48))
            pygame.draw.circle(surf,DGREEN,(tx+22,ty+34),34)
            pygame.draw.circle(surf,GREEN,(tx+22,ty+20),24)
            pygame.draw.circle(surf,bright(GREEN,30),(tx+16,ty+14),12)

    elif theme=="lava":
        # lava sky glow
        for i in range(5):
            lx=(80+i*200-int(cam*0.18))%(SW+220)-110
            gs=pygame.Surface((140,90),pygame.SRCALPHA)
            pygame.draw.ellipse(gs,(255,80,0,45),(0,0,140,90))
            surf.blit(gs,(lx,GROUND_Y-70))
        # stalactites
        for i in range(12):
            sx2=(40+i*95-int(cam*0.28))%(SW+160)-80
            h=random.randint(40,90)
            pts=[(sx2,0),(sx2+18,0),(sx2+9,h)]
            pygame.draw.polygon(surf,(55,25,8),pts)
            pygame.draw.polygon(surf,(90,40,10),pts,1)
        # lava river at bottom
        for i in range(0,SW,4):
            lh=int(4*math.sin((i+tick*2)*0.05))
            pygame.draw.rect(surf,(200,60,0),(i,GROUND_Y+28,4,8+lh))
            pygame.draw.rect(surf,(255,120,0),(i,GROUND_Y+28,4,3))

    elif theme=="ice":
        for i in range(6):
            mx=(90+i*200-int(cam*0.22))%(SW+320)-160
            pts=[(mx,GROUND_Y),(mx+110,GROUND_Y-130),(mx+220,GROUND_Y)]
            pygame.draw.polygon(surf,(175,210,240),pts)
            pygame.draw.polygon(surf,WHITE,pts,2)
            pygame.draw.polygon(surf,(220,240,255),[(mx+80,GROUND_Y),(mx+110,GROUND_Y-130),(mx+140,GROUND_Y)])

    elif theme=="storm":
        for i in range(7):
            cx=(90+i*160-int(cam*0.16))%(SW+200)-100
            pygame.draw.circle(surf,(55,45,75),(cx,35+(i%3)*24),30)
            pygame.draw.circle(surf,(70,60,90),(cx,35+(i%3)*24),30,2)
        # ruins silhouette
        for i in range(5):
            rx=(100+i*220-int(cam*0.38))%(SW+300)-150
            pygame.draw.rect(surf,(40,30,55),(rx,GROUND_Y-110,60,110))
            pygame.draw.rect(surf,(50,40,65),(rx+10,GROUND_Y-140,15,30))
            pygame.draw.rect(surf,(50,40,65),(rx+35,GROUND_Y-125,15,25))

    elif theme=="abyss":
        for i in range(10):
            rx=(55+i*115-int(cam*0.2))%(SW+200)-100
            ry=70+(i%4)*38
            pygame.draw.ellipse(surf,(18,12,28),(rx,ry,90,32))
        ms=pygame.Surface((SW,120),pygame.SRCALPHA)
        ms.fill((55,18,75,35)); surf.blit(ms,(0,GROUND_Y-90))
        # void cracks
        for i in range(4):
            vx=(200+i*280-int(cam*0.15))%(SW+300)-150
            pygame.draw.line(surf,(80,40,120),(vx,GROUND_Y-20),(vx+30,GROUND_Y),3)

# ═══════════════════════════════════════════════════════════════════════════════
#  HUD
# ═══════════════════════════════════════════════════════════════════════════════
def draw_hud(surf,player,time_left,level_idx,tick,ammo=12,shoot_cd=0):
    # top bar
    bar=pygame.Surface((SW,68),pygame.SRCALPHA); bar.fill((4,10,28,220))
    surf.blit(bar,(0,0))
    pygame.draw.line(surf,GOLD,(0,68),(SW,68),2)

    # ── LIVES (hearts) ──
    for i in range(3):
        col=RED if i<player.lives else (50,30,30)
        lx=14+i*32; ly=8
        pygame.draw.circle(surf,col,(lx+7,ly+9),7)
        pygame.draw.circle(surf,col,(lx+17,ly+9),7)
        pygame.draw.polygon(surf,col,[(lx,ly+12),(lx+12,ly+26),(lx+24,ly+12)])
        if i<player.lives:
            pygame.draw.circle(surf,bright(col,60),(lx+6,ly+7),3)

    # ── HP bar ──
    hx,hy=110,8
    surf.blit(F22.render("HP",True,WHITE),(hx,hy+2))
    bw=140; bh=16
    pygame.draw.rect(surf,(30,10,10),(hx+28,hy+4,bw,bh),border_radius=7)
    ratio=player.hp/player.MAX_HP
    hcol=HP_G if ratio>0.5 else HP_Y if ratio>0.25 else HP_R
    if ratio<0.25:
        pa=int(50*math.sin(tick*0.18))
        pygame.draw.rect(surf,(*HP_R,80+pa),pygame.Rect(hx+28,hy+4,bw,bh),border_radius=7)
    pygame.draw.rect(surf,hcol,(hx+28,hy+4,int(bw*ratio),bh),border_radius=7)
    pygame.draw.rect(surf,WHITE,(hx+28,hy+4,bw,bh),2,border_radius=7)
    surf.blit(F16.render(f"{int(player.hp)}",True,WHITE),(hx+30,hy+5))

    # ── Energy bar ──
    ex2,ey=110,32
    surf.blit(F22.render("EN",True,CYAN),(ex2,ey+2))
    ecol=CYAN if player.energy>50 else YELLOW if player.energy>20 else RED
    pygame.draw.rect(surf,(10,20,30),(ex2+28,ey+4,bw,bh),border_radius=7)
    pygame.draw.rect(surf,ecol,(ex2+28,ey+4,int(bw*(player.energy/player.MAX_EN)),bh),border_radius=7)
    pygame.draw.rect(surf,WHITE,(ex2+28,ey+4,bw,bh),2,border_radius=7)
    surf.blit(F16.render(f"{int(player.energy)}%",True,WHITE),(ex2+30,ey+5))

    # shield indicator
    if player.shield>0:
        surf.blit(F22.render(f"SHIELD {player.shield//60+1}s",True,(80,200,255)),(ex2+175,ey+2))

    # ── Score ──
    shadow_text(surf,f"Score: {player.score}",F36,GOLD,SW//2-85,10)

    # ── Ammo / Gun widget ──
    ax=SW//2-85; ay=44
    # gun icon (simple silhouette)
    pygame.draw.rect(surf,(80,80,90),(ax,ay+4,22,10),border_radius=3)
    pygame.draw.rect(surf,(60,60,70),(ax+18,ay+2,6,6),border_radius=2)
    pygame.draw.rect(surf,(80,80,90),(ax+6,ay+14,8,5),border_radius=2)
    # bullet dots
    for i in range(12):
        bx2=ax+28+i*14; by2=ay+4
        if i<ammo:
            col2=YELLOW if shoot_cd==0 else (180,160,40)
            pygame.draw.ellipse(surf,col2,(bx2,by2,10,14))
            pygame.draw.ellipse(surf,WHITE,(bx2,by2,10,14),1)
        else:
            pygame.draw.ellipse(surf,(40,40,50),(bx2,by2,10,14))
            pygame.draw.ellipse(surf,(60,60,70),(bx2,by2,10,14),1)
    # label
    surf.blit(F16.render(f"AMMO {ammo}/12",True,YELLOW if ammo>3 else RED),(ax+28,ay+20))

    # ── Timer ──
    tw=170; tx=SW-tw-14; ty=6
    pygame.draw.rect(surf,(18,18,38),(tx,ty,tw,56),border_radius=10)
    pygame.draw.rect(surf,WHITE,(tx,ty,tw,56),2,border_radius=10)
    ratio_t=max(0,time_left/LEVELS[level_idx]["time"])
    tc=(int(220*(1-ratio_t)+50*ratio_t),int(220*ratio_t),50)
    pygame.draw.rect(surf,tc,(tx+4,ty+34,int((tw-8)*ratio_t),14),border_radius=5)
    shadow_text(surf,f"{int(time_left)}s",F28,WHITE,tx+tw//2-18,ty+6)
    surf.blit(F16.render("TIME",True,LGRAY),(tx+tw//2-14,ty+28))

    # ── Level badge ──
    lx2=SW//2+130
    pygame.draw.rect(surf,(18,38,78),(lx2,6,160,56),border_radius=10)
    pygame.draw.rect(surf,GOLD,(lx2,6,160,56),2,border_radius=10)
    shadow_text(surf,f"LVL {level_idx+1}/5",F22,GOLD,lx2+8,10)
    surf.blit(F16.render(LEVELS[level_idx]["name"],True,LBLUE),(lx2+4,32))

    # ── LOW ENERGY WARNING ──
    if player.energy<20:
        wa=int(160+95*math.sin(tick*0.2))
        ws=pygame.Surface((SW,SH),pygame.SRCALPHA)
        pygame.draw.rect(ws,(255,20,20,min(55,wa)),(0,0,SW,SH))
        surf.blit(ws,(0,0))
        wt=F48.render("!! LOW ENERGY !!",True,(255,70,70))
        wt.set_alpha(wa); surf.blit(wt,wt.get_rect(center=(SW//2,SH-55)))

    # ── LOW HP WARNING ──
    if player.hp<25 and player.hp>0:
        ha=int(140+115*math.sin(tick*0.22))
        hs2=pygame.Surface((SW,SH),pygame.SRCALPHA)
        pygame.draw.rect(hs2,(255,0,0,min(45,ha)),(0,0,SW,SH))
        surf.blit(hs2,(0,0))
        ht=F48.render("!! DANGER !!",True,RED)
        ht.set_alpha(ha); surf.blit(ht,ht.get_rect(center=(SW//2,SH-100)))

    # ── bottom hint ──
    hint=F16.render("A/D Move   SPACE Jump   ESC Pause",True,(150,180,210))
    surf.blit(hint,hint.get_rect(center=(SW//2,SH-12)))

# ═══════════════════════════════════════════════════════════════════════════════
#  MAP SCREEN
# ═══════════════════════════════════════════════════════════════════════════════
def draw_map(surf, tick, unlocked, hover_idx, btns):
    # parchment background
    grad(surf,(80,55,20),(50,35,10),pygame.Rect(0,0,SW,SH))
    # grid texture
    for x in range(0,SW,40):
        pygame.draw.line(surf,(90,65,25,60),(x,0),(x,SH),1)
    for y in range(0,SH,40):
        pygame.draw.line(surf,(90,65,25,60),(0,y),(SW,y),1)
    # vignette
    for edge in range(60):
        a=int(180*(1-edge/60))
        pygame.draw.rect(surf,(30,18,5,a),(edge,edge,SW-edge*2,SH-edge*2),1)

    # title
    shadow_text(surf,"WORLD MAP",F60,GOLD,SW//2-165,22,(60,35,0),4)
    pygame.draw.line(surf,GOLD,(80,82),(SW-80,82),2)

    # path lines between nodes
    positions=[lv["map_pos"] for lv in LEVELS]
    for i in range(len(positions)-1):
        p1=positions[i]; p2=positions[i+1]
        col=GOLD if i<unlocked else (80,60,30)
        # dashed path
        dx=p2[0]-p1[0]; dy=p2[1]-p1[1]
        dist=math.hypot(dx,dy); steps=int(dist//18)
        for s in range(steps):
            t1=s/steps; t2=min(1,(s+0.5)/steps)
            x1=int(p1[0]+dx*t1); y1=int(p1[1]+dy*t1)
            x2=int(p1[0]+dx*t2); y2=int(p1[1]+dy*t2)
            pygame.draw.line(surf,col,(x1,y1),(x2,y2),3)

    # level nodes
    for i,lv in enumerate(LEVELS):
        px,py=lv["map_pos"]
        locked=i>unlocked
        col=lv["map_col"]
        is_hover=(i==hover_idx and not locked)

        # node glow
        if is_hover:
            ga=int(60+40*math.sin(tick*0.1))
            gs=pygame.Surface((80,80),pygame.SRCALPHA)
            pygame.draw.circle(gs,(*col,ga),(40,40),38)
            surf.blit(gs,(px-40,py-40))

        # outer ring
        ring_col=col if not locked else (60,50,40)
        pygame.draw.circle(surf,ring_col,(px,py),28)
        pygame.draw.circle(surf,bright(ring_col,60),(px,py),28,3)

        # inner
        inner=bright(col,40) if not locked else (40,35,30)
        pygame.draw.circle(surf,inner,(px,py),22)

        # level number
        num_col=WHITE if not locked else (80,70,60)
        ns=F36.render(str(i+1),True,num_col)
        surf.blit(ns,ns.get_rect(center=(px,py)))

        # lock icon
        if locked:
            pygame.draw.rect(surf,(80,70,60),(px-8,py+30,16,12),border_radius=3)
            pygame.draw.rect(surf,(80,70,60),(px-5,py+22,10,10),border_radius=5)
            pygame.draw.rect(surf,(60,50,40),(px-5,py+22,10,10),border_radius=5,width=2)

        # name label
        lname=F22.render(lv["name"],True,num_col)
        surf.blit(lname,lname.get_rect(center=(px,py+48)))

        # theme icon hint
        icons={"jungle":"[J]","lava":"[L]","ice":"[I]","storm":"[S]","abyss":"[A]"}
        ic=F16.render(icons.get(lv["theme"],""),True,bright(col,40))
        surf.blit(ic,ic.get_rect(center=(px,py-38)))

    # hover info panel
    if 0<=hover_idx<len(LEVELS) and hover_idx<=unlocked:
        lv=LEVELS[hover_idx]
        px2,py2=lv["map_pos"]
        panel_x=min(SW-280,max(10,px2-130)); panel_y=py2+65
        if panel_y+130>SH: panel_y=py2-175
        pp=pygame.Rect(panel_x,panel_y,260,120)
        pygame.draw.rect(surf,(20,14,5,200),pp,border_radius=10)
        pygame.draw.rect(surf,GOLD,pp,2,border_radius=10)
        shadow_text(surf,lv["name"],F28,GOLD,panel_x+10,panel_y+8)
        surf.blit(F22.render(f"Time: {lv['time']}s",True,WHITE),(panel_x+10,panel_y+36))
        surf.blit(F22.render(f"Obstacles: {lv['boulders']+lv['spikes']+lv['flyers']}",True,LBLUE),(panel_x+10,panel_y+58))
        surf.blit(F22.render(f"Lives: {lv['lives']}",True,RED),(panel_x+10,panel_y+80))
        surf.blit(F16.render("Click to play",True,YELLOW),(panel_x+10,panel_y+100))

    for b in btns: b.draw(surf)

# ═══════════════════════════════════════════════════════════════════════════════
#  SCOREBOARD POPUP
# ═══════════════════════════════════════════════════════════════════════════════
def draw_scoreboard(surf,player,finish_time,level_idx,won,tick,btns):
    ov=pygame.Surface((SW,SH),pygame.SRCALPHA); ov.fill((0,0,0,190)); surf.blit(ov,(0,0))
    pw,ph=640,500; px=SW//2-pw//2; py=SH//2-ph//2-10
    # shadow
    pygame.draw.rect(surf,(0,0,0,100),pygame.Rect(px+10,py+10,pw,ph),border_radius=20)
    # panel
    grad(surf,(10,25,55),(4,12,28),pygame.Rect(px,py,pw,ph))
    # shimmer
    shx=px+int((tick*3)%(pw+100))-50
    sh2=pygame.Surface((100,ph),pygame.SRCALPHA)
    for i in range(100):
        a=int(20*math.sin(math.pi*i/100))
        pygame.draw.line(sh2,(255,215,0,a),(i,0),(i,ph))
    surf.blit(sh2,(shx,py))
    pygame.draw.rect(surf,GOLD,(px,py,pw,ph),3,border_radius=20)

    htxt="LEVEL COMPLETE!" if won else ("OUT OF LIVES!" if player.lives<=0 else "TIME'S UP!")
    hcol=GOLD if won else RED
    hs=F60.render(htxt,True,hcol)
    surf.blit(hs,hs.get_rect(center=(SW//2,py+46)))
    pygame.draw.line(surf,GOLD,(px+30,py+82),(px+pw-30,py+82),2)

    items=player.items
    rows=[
        ("Candies", items.count("candy"),  items.count("candy")*ITEM_VAL["candy"],  ITEM_COL["candy"]),
        ("Baskets", items.count("basket"), items.count("basket")*ITEM_VAL["basket"],ITEM_COL["basket"]),
        ("Sticks",  items.count("stick"),  items.count("stick")*ITEM_VAL["stick"],  ITEM_COL["stick"]),
        ("Gems",    items.count("gem"),    items.count("gem")*ITEM_VAL["gem"],       ITEM_COL["gem"]),
    ]
    ry=py+92
    for label,cnt,pts,col in rows:
        rb=pygame.Rect(px+28,ry,pw-56,38)
        rbs=pygame.Surface((rb.w,rb.h),pygame.SRCALPHA); rbs.fill((255,255,255,10))
        surf.blit(rbs,(rb.x,rb.y))
        pygame.draw.circle(surf,col,(px+50,ry+19),9)
        surf.blit(F28.render(label,True,WHITE),(px+68,ry+9))
        surf.blit(F28.render(f"x{cnt}",True,LBLUE),(px+230,ry+9))
        surf.blit(F28.render(f"+{pts} pts",True,GOLD),(px+pw-165,ry+9))
        ry+=42

    pygame.draw.line(surf,(70,90,130),(px+30,ry+4),(px+pw-30,ry+4),1); ry+=14
    ts=F28.render(f"Finished in {finish_time:.1f}s" if won else "Did not reach finish",True,(160,210,230))
    surf.blit(ts,ts.get_rect(center=(SW//2,ry+12))); ry+=40
    surf.blit(F36.render(f"TOTAL SCORE:  {player.score}",True,GOLD),
              F36.render(f"TOTAL SCORE:  {player.score}",True,GOLD).get_rect(center=(SW//2,ry+10)))
    ry+=50
    sc=player.score
    grade="S" if sc>=700 else "A" if sc>=400 else "B" if sc>=200 else "C"
    gcol=GOLD if grade=="S" else (100,230,100) if grade=="A" else LBLUE if grade=="B" else LGRAY
    br=pygame.Rect(SW//2-32,ry-4,64,62)
    pygame.draw.rect(surf,(20,40,80),br,border_radius=12)
    pygame.draw.rect(surf,gcol,br,3,border_radius=12)
    surf.blit(F60.render(grade,True,gcol),F60.render(grade,True,gcol).get_rect(center=br.center))
    for b in btns: b.draw(surf)

# ═══════════════════════════════════════════════════════════════════════════════
#  TRANSITION SCREEN
# ═══════════════════════════════════════════════════════════════════════════════
def draw_transition(surf,level_idx,alpha):
    a=max(0,min(255,int(alpha)))
    ov=pygame.Surface((SW,SH),pygame.SRCALPHA); ov.fill((0,0,0,a)); surf.blit(ov,(0,0))
    if a>100:
        lv=LEVELS[level_idx]
        ts=F60.render(f"Level {level_idx+1}",True,GOLD)
        ns=F36.render(lv["name"],True,WHITE)
        ts.set_alpha(a); ns.set_alpha(a)
        surf.blit(ts,ts.get_rect(center=(SW//2,SH//2-30)))
        surf.blit(ns,ns.get_rect(center=(SW//2,SH//2+30)))

# ═══════════════════════════════════════════════════════════════════════════════
#  MULTIPLAYER UI HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
# Player colors for up to 4 remote players
MP_COLORS = [(80,140,220),(220,80,80),(80,200,80),(220,180,40)]

def draw_mp_menu(surf, tick, btns):
    grad(surf,(8,20,50),(4,10,25),pygame.Rect(0,0,SW,SH))
    for i in range(40):
        sx=(i*137+tick)%SW; sy=(i*97)%(SH)
        br=int(80+60*math.sin(tick*0.04+i))
        pygame.draw.circle(surf,(br,br,br),(sx,sy),1)
    shadow_text(surf,"MULTIPLAYER",F60,GOLD,SW//2-195,80,(0,0,0),4)
    shadow_text(surf,"Up to 4 players on the same LAN",F28,LBLUE,SW//2-210,148)
    for b in btns: b.draw(surf)

def draw_mp_host(surf, tick, server, btns, qr_surf_cache, copied_timer):
    grad(surf,(8,20,50),(4,10,25),pygame.Rect(0,0,SW,SH))
    shadow_text(surf,"HOST ROOM",F60,GOLD,SW//2-165,50,(0,0,0),4)

    ip   = _get_local_ip()
    code = server.code
    share_str = server.share_string   # CODE@host:port  (tunnel or LAN)

    # ── Tunnel status badge ───────────────────────────────────────────────────
    if server.tunnel.ready:
        tb=pygame.Rect(SW//2-180,95,360,28)
        pygame.draw.rect(surf,(0,60,20),tb,border_radius=8)
        pygame.draw.rect(surf,HP_G,tb,1,border_radius=8)
        shadow_text(surf,f"Online tunnel active: {server.tunnel.address}",F16,HP_G,SW//2-170,101)
    elif server.tunnel.error:
        tb=pygame.Rect(SW//2-200,95,400,28)
        pygame.draw.rect(surf,(60,20,0),tb,border_radius=8)
        pygame.draw.rect(surf,ORANGE,tb,1,border_radius=8)
        shadow_text(surf,f"Tunnel unavailable ({server.tunnel.error}) — LAN only",F16,ORANGE,SW//2-195,101)
    else:
        tb=pygame.Rect(SW//2-160,95,320,28)
        pygame.draw.rect(surf,(20,30,60),tb,border_radius=8)
        pygame.draw.rect(surf,LBLUE,tb,1,border_radius=8)
        shadow_text(surf,"Opening online tunnel...",F16,LBLUE,SW//2-110,101)

    # ── Left panel: QR code ──────────────────────────────────────────────────
    qr_size = 180
    qr_x, qr_y = 80, 120

    # generate QR surface once and cache it
    if qr_surf_cache[0] is None or qr_surf_cache[1] != share_str:
        try:
            import qrcode as _qr
            qr = _qr.QRCode(version=2, box_size=5, border=2,
                             error_correction=_qr.constants.ERROR_CORRECT_M)
            qr.add_data(share_str); qr.make(fit=True)
            img = qr.make_image(fill_color="white", back_color=(8,20,50))
            # convert PIL image → pygame surface
            import io
            buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
            qr_pg = pygame.image.load(buf)
            qr_pg = pygame.transform.scale(qr_pg, (qr_size, qr_size))
            qr_surf_cache[0] = qr_pg; qr_surf_cache[1] = share_str
        except Exception:
            qr_surf_cache[0] = None; qr_surf_cache[1] = share_str

    # QR frame
    frame = pygame.Rect(qr_x-8, qr_y-8, qr_size+16, qr_size+16)
    pygame.draw.rect(surf,(15,30,65),frame,border_radius=10)
    pygame.draw.rect(surf,GOLD,frame,2,border_radius=10)

    if qr_surf_cache[0]:
        surf.blit(qr_surf_cache[0],(qr_x, qr_y))
    else:
        # fallback pixel grid if qrcode failed
        cell=9
        for ci,ch in enumerate(code):
            val=ord(ch)
            for row in range(5):
                for col2 in range(5):
                    bit=(val>>(row+col2))&1
                    c2=GOLD if bit else (25,35,60)
                    pygame.draw.rect(surf,c2,(qr_x+ci*(cell*5+4)+col2*cell,
                                              qr_y+row*cell,cell-1,cell-1))

    shadow_text(surf,"Scan or share code to join from anywhere",F22,LBLUE, qr_x+2, qr_y+qr_size+10)

    # ── Right panel: IP + Code + Copy ───────────────────────────────────────
    rx = qr_x + qr_size + 40
    panel = pygame.Rect(rx, 115, SW-rx-40, 310)
    grad(surf,(15,30,65),(8,15,35),panel)
    pygame.draw.rect(surf,GOLD,panel,2,border_radius=14)

    shadow_text(surf,"Share with friends anywhere:",F22,LGRAY,rx+14,128)

    # Share string row (full invite code)
    ib = pygame.Rect(rx+14, 162, panel.w-28, 48)
    pygame.draw.rect(surf,(20,40,80),ib,border_radius=8)
    pygame.draw.rect(surf,TEAL,ib,2,border_radius=8)
    shadow_text(surf,"Invite:",F22,LBLUE,ib.x+8,ib.y+10)
    # truncate if too long for display
    ss_disp=share_str if len(share_str)<32 else share_str[:30]+"..."
    shadow_text(surf,ss_disp,F22,WHITE,ib.x+72,ib.y+12)

    # Code row
    cb = pygame.Rect(rx+14, 222, panel.w-28, 48)
    pygame.draw.rect(surf,(20,40,80),cb,border_radius=8)
    pygame.draw.rect(surf,GOLD,cb,2,border_radius=8)
    shadow_text(surf,"CODE:",F22,YELLOW,cb.x+8,cb.y+10)
    shadow_text(surf,code,F36,GOLD,cb.x+80,cb.y+6)

    # Copy button area (drawn as a highlighted rect — actual Button is in btns)
    # "Copied!" flash
    if copied_timer[0]>0:
        copied_timer[0]-=1
        ca=min(255,copied_timer[0]*12)
        cs=F22.render("Copied to clipboard!",True,HP_G)
        cs.set_alpha(ca); surf.blit(cs,cs.get_rect(center=(rx+panel.w//2, 290)))

    # QR data label
    shadow_text(surf,f"QR data:  {share_str}",F16,GRAY,rx+14,300)

    # Connection logs
    shadow_text(surf,"Activity:",F22,LGRAY,rx+14,328)
    for i,log in enumerate(server.logs[-4:]):
        col2=HP_G if "joined" in log else (200,140,100)
        surf.blit(F16.render(log,True,col2),(rx+14,350+i*18))

    for b in btns: b.draw(surf)


def draw_mp_join(surf, tick, input_text, error, btns):
    grad(surf,(8,20,50),(4,10,25),pygame.Rect(0,0,SW,SH))
    shadow_text(surf,"JOIN ROOM",F60,TEAL,SW//2-165,50,(0,0,0),4)

    panel=pygame.Rect(SW//2-300,120,600,310)
    grad(surf,(15,30,65),(8,15,35),panel)
    pygame.draw.rect(surf,TEAL,panel,2,border_radius=14)

    # instructions
    shadow_text(surf,"Paste the invite code your friend shared:",F28,WHITE,SW//2-270,140)
    shadow_text(surf,"Format:  CODE@host:port   or just the CODE",F16,GRAY,SW//2-270,172)

    # big code input box
    ib=pygame.Rect(SW//2-260,192,520,62)
    pygame.draw.rect(surf,(10,22,50),ib,border_radius=12)
    pygame.draw.rect(surf,TEAL,ib,2,border_radius=12)
    display=input_text if input_text else "Paste invite code here..."
    col=WHITE if input_text else GRAY
    cursor="|" if (tick//28)%2==0 else ""
    ts=F36.render(display+cursor,True,col)
    # truncate display if too wide
    if ts.get_width()>500:
        ts=F28.render(display+cursor,True,col)
    surf.blit(ts,ts.get_rect(center=ib.center))

    # example
    shadow_text(surf,"Example:  AB3X7K@abcde.serveo.net:55432",F16,GRAY,SW//2-260,268)

    # how to get code hint
    hint_box=pygame.Rect(SW//2-260,292,520,60)
    pygame.draw.rect(surf,(10,30,60),hint_box,border_radius=8)
    pygame.draw.rect(surf,(40,80,140),hint_box,1,border_radius=8)
    shadow_text(surf,"Ask your friend to click  Copy Code  in their Host Room.",F22,LBLUE,SW//2-248,302)
    shadow_text(surf,"Then paste it here and click Connect.",F22,LBLUE,SW//2-248,322)

    if error:
        eb=pygame.Rect(SW//2-260,360,520,36)
        pygame.draw.rect(surf,(60,10,10),eb,border_radius=6)
        shadow_text(surf,f"  {error}",F22,RED,SW//2-255,366)

    for b in btns: b.draw(surf)


def draw_mp_lobby(surf, tick, lobby_list, is_host, my_id, pending_requests, btns):
    grad(surf,(8,20,50),(4,10,25),pygame.Rect(0,0,SW,SH))
    shadow_text(surf,"LOBBY",F60,GOLD,SW//2-90,40,(0,0,0),4)

    # ── Approved players panel ───────────────────────────────────────────────
    panel=pygame.Rect(SW//2-320,105,640,310)
    grad(surf,(12,25,55),(6,12,28),panel)
    pygame.draw.rect(surf,GOLD,panel,2,border_radius=16)

    approved=[p for p in lobby_list if p.get("approved",True)]
    shadow_text(surf,f"Players  ({len(approved)}/4)",F28,LBLUE,SW//2-290,115)
    pygame.draw.line(surf,GOLD,(SW//2-300,145),(SW//2+300,145),1)

    for i,p in enumerate(approved[:4]):
        py2=158+i*60
        col=MP_COLORS[i%4]
        card=pygame.Rect(SW//2-290,py2,580,50)
        grad(surf,tuple(v//3 for v in col),(10,15,30),card)
        pygame.draw.rect(surf,col,card,2,border_radius=10)
        pygame.draw.circle(surf,col,(SW//2-262,py2+25),18)
        pygame.draw.circle(surf,WHITE,(SW//2-262,py2+25),18,2)
        surf.blit(F22.render(str(i+1),True,WHITE),
                  F22.render(str(i+1),True,WHITE).get_rect(center=(SW//2-262,py2+25)))
        name=p.get("name",f"Player {p['id']}")
        you=" (YOU)" if p["id"]==my_id else ""
        shadow_text(surf,name+you,F28,WHITE,SW//2-234,py2+10)
        tag="HOST" if i==0 else "READY"
        tc=GOLD if i==0 else HP_G
        surf.blit(F22.render(tag,True,tc),(SW//2+200,py2+14))

    # ── Pending join requests (host only) ────────────────────────────────────
    if is_host and pending_requests:
        rx=SW//2-320; ry=425
        shadow_text(surf,"Join Requests:",F28,ORANGE,rx,ry-24)
        for j,req in enumerate(pending_requests[:3]):
            rcard=pygame.Rect(rx,ry+j*52,640,44)
            pygame.draw.rect(surf,(40,25,10),rcard,border_radius=8)
            pygame.draw.rect(surf,ORANGE,rcard,2,border_radius=8)
            shadow_text(surf,req["name"],F28,WHITE,rx+14,ry+j*52+8)
            # approve / reject labels (actual buttons passed in btns)
            surf.blit(F22.render("Approve",True,HP_G),(SW//2+100,ry+j*52+10))
            surf.blit(F22.render("Reject", True,RED), (SW//2+210,ry+j*52+10))

    # ── Waiting / status line ────────────────────────────────────────────────
    sy2=SH-90
    if len(approved)<2:
        wa=int(180+75*math.sin(tick*0.1))
        wt=F22.render("Waiting for players to join...",True,(wa,wa,wa))
        surf.blit(wt,wt.get_rect(center=(SW//2,sy2)))
    elif is_host:
        surf.blit(F22.render("All set! Press START when ready.",True,HP_G),
                  F22.render("All set! Press START when ready.",True,HP_G).get_rect(center=(SW//2,sy2)))
    else:
        wa2=int(180+75*math.sin(tick*0.08))
        wt2=F22.render("Waiting for host to start...",True,(wa2,wa2,255))
        surf.blit(wt2,wt2.get_rect(center=(SW//2,sy2)))

    for b in btns: b.draw(surf)


def draw_mp_waiting(surf, tick, name, code):
    """Screen shown to joiner while waiting for host approval."""
    grad(surf,(8,20,50),(4,10,25),pygame.Rect(0,0,SW,SH))
    shadow_text(surf,"WAITING FOR APPROVAL",F48,ORANGE,SW//2-270,80,(0,0,0),3)

    panel=pygame.Rect(SW//2-260,160,520,220)
    grad(surf,(15,30,65),(8,15,35),panel)
    pygame.draw.rect(surf,ORANGE,panel,2,border_radius=14)

    shadow_text(surf,f"Hi, {name}!",F36,WHITE,SW//2-80,180)
    shadow_text(surf,f"Room code:  {code}",F28,GOLD,SW//2-120,230)
    shadow_text(surf,"The host needs to approve your request.",F22,LBLUE,SW//2-210,275)
    shadow_text(surf,"Please wait...",F22,LGRAY,SW//2-80,305)

    # spinner
    for i in range(8):
        a2=math.pi*2*i/8 + tick*0.08
        r2=30; cx2=SW//2; cy2=370
        px2=int(cx2+math.cos(a2)*r2); py2=int(cy2+math.sin(a2)*r2)
        alpha=int(255*(i/8))
        pygame.draw.circle(surf,(alpha,alpha,255),(px2,py2),5)


def draw_remote_player(surf, cam, p, idx):
    """Draw another player's character from their synced state."""
    sx=int(p.get("x",0))-cam; sy=int(p.get("y",500))
    col=MP_COLORS[idx%4]
    # body
    pygame.draw.rect(surf,col,(sx+2,sy+17,34,20),border_radius=5)
    pygame.draw.rect(surf,bright(col,60),(sx+2,sy+17,34,5),border_radius=5)
    # head
    pygame.draw.circle(surf,bright(col,80),(sx+19,sy+12),13)
    pygame.draw.circle(surf,WHITE,(sx+19,sy+12),13,2)
    # legs
    pygame.draw.rect(surf,tuple(max(0,v-60) for v in col),(sx+4,sy+33,13,17),border_radius=4)
    pygame.draw.rect(surf,tuple(max(0,v-60) for v in col),(sx+21,sy+33,13,17),border_radius=4)
    # name tag
    name=p.get("name",f"P{idx+1}")
    ns=F16.render(name,True,col)
    surf.blit(ns,(sx-ns.get_width()//2+19,sy-22))
    # mini HP bar
    hp=p.get("hp",100)/100
    pygame.draw.rect(surf,(60,20,20),(sx,sy-10,38,5),border_radius=2)
    pygame.draw.rect(surf,HP_G,(sx,sy-10,int(38*hp),5),border_radius=2)


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN GAME CLASS
# ═══════════════════════════════════════════════════════════════════════════════
class Game:
    def __init__(self):
        self.state=GS.SPLASH; self.tick=0
        self.level=0; self.unlocked=0
        self.total_score=0; self.splash_alpha=0
        self.map_hover=-1
        self.trans_alpha=0; self.trans_dir=1; self.trans_target=GS.PLAYING
        # player profile
        self.player_name="Hero"
        self.player_char=CHARACTERS[0]
        self.char_sel_idx=0
        self.char_name_input=""
        # multiplayer
        self.mp_server=None
        self.mp_client=None
        self.mp_join_input=""
        self.mp_join_error=""
        self.mp_is_host=False
        self.mp_qr_cache=[None, ""]
        self.mp_copied_timer=[0]
        self._init_level(); self._make_buttons()

    def _init_level(self):
        cfg=LEVELS[self.level]
        self.player=Player(cfg["lives"], self.player_char, self.player_name)
        (self.platforms,self.pits,self.collectibles,
         self.boulders,self.spikes,self.enemies,
         self.animals,self.finish,self.world_w)=generate_world(self.level)
        self.particles=[]; self.camera=0.0
        self.bullets=[]
        self.ammo=12          # bullets per life
        self.shoot_cooldown=0
        self.start_t=pygame.time.get_ticks()/1000.0
        self.finish_time=0.0; self.won=False
        self.weather=WeatherSystem(cfg["theme"])
        play_bgm(cfg["theme"])

    def _make_buttons(self):
        cx=SW//2
        self.splash_btn=[Button(cx-110,SH//2+90,220,50,"Start",  (40,160,60),(60,200,80))]
        # char select buttons
        self.char_confirm_btn=Button(cx-120,SH-52,240,46,"Confirm & Play",
                                     (40,160,60),(60,200,80))
        self.char_back_btn   =Button(20,SH-52,130,46,"Back",
                                     (80,80,90),(120,120,130))
        self.map_back  =[Button(20,SH-60,140,44,"Back",          (80,80,90),(120,120,130))]
        # main map has a multiplayer button
        self.map_mp_btn=[Button(SW-200,SH-60,180,44,"Multiplayer",(50,100,200),(80,140,240))]
        self.pause_btns=[
            Button(cx-115,290,230,50,"Resume",       (40,160,60),(60,200,80)),
            Button(cx-115,354,230,50,"Restart Level",(50,100,200),(80,140,240)),
            Button(cx-115,418,230,50,"World Map",    (80,80,90),(120,120,130)),
        ]
        self.win_btns=[
            Button(cx-130,548,120,44,"Next Level",(40,160,60),(60,200,80)),
            Button(cx+10, 548,120,44,"World Map", (50,100,200),(80,140,240)),
        ]
        self.over_btns=[
            Button(cx-130,548,120,44,"Retry",    (40,160,60),(60,200,80)),
            Button(cx+10, 548,120,44,"World Map",(50,100,200),(80,140,240)),
        ]
        self.map_level_btns=[
            Button(lv["map_pos"][0]-28,lv["map_pos"][1]-28,56,56,"",
                   lv["map_col"],bright(lv["map_col"],40))
            for lv in LEVELS
        ]
        # multiplayer screens
        self.mp_menu_btns=[
            Button(cx-120,240,240,54,"Host a Room",  (40,160,60),(60,200,80)),
            Button(cx-120,308,240,54,"Join a Room",  (50,100,200),(80,140,240)),
            Button(cx-120,376,240,54,"Back",         (80,80,90),(120,120,130)),
        ]
        self.mp_host_btns=[
            Button(cx-200,560,160,48,"Start Game",(40,160,60),(60,200,80)),
            Button(cx-20, 560,160,48,"Copy Code", (50,100,200),(80,140,240)),
            Button(cx+160,560,120,48,"Cancel",    (180,40,40),(220,70,70)),
        ]
        self.mp_join_btns=[
            Button(cx-120,380,240,50,"Connect",   (50,100,200),(80,140,240)),
            Button(cx-120,444,240,50,"Back",      (80,80,90),(120,120,130)),
        ]
        self.mp_lobby_btns=[
            Button(cx-120,540,240,48,"Leave",     (180,40,40),(220,70,70)),
        ]
        self.mp_lobby_start_btn=Button(cx+10,540,160,48,"START",(40,160,60),(60,200,80))
        # approve/reject buttons (up to 3 pending requests shown)
        self.mp_approve_btns=[Button(cx+100,425+j*52,100,36,"Approve",(30,120,50),(50,180,70)) for j in range(3)]
        self.mp_reject_btns =[Button(cx+210,425+j*52,90, 36,"Reject", (140,30,30),(200,50,50)) for j in range(3)]

    def _burst(self,x,y,col,n=12):
        for _ in range(n): self.particles.append(Particle(x,y,col))

    def _confirm_char(self):
        name=self.char_name_input.strip() or "Hero"
        self.player_name=name
        self.player_char=CHARACTERS[self.char_sel_idx]
        self._init_level()
        self.state=GS.MAP

    def _mp_do_join(self):
        raw=self.mp_join_input.strip()
        if not raw:
            self.mp_join_error="Paste the invite code from your friend"; return
        code, host, port = parse_share(raw)
        if not code:
            self.mp_join_error="Invalid code format"; return
        self.mp_is_host=False
        name=self.player_name if hasattr(self,"player_name") else "Player"
        self.mp_client=MPClient(host, port, name)
        self.mp_client.connect(code)
        if not self.mp_client.connected:
            self.mp_join_error=self.mp_client.error or "Could not connect to relay"; return
        self.mp_join_error=""
        self.state=GS.MP_WAITING   # wait for host approval

    def _mp_cleanup(self):
        if self.mp_client:
            self.mp_client.disconnect(); self.mp_client=None
        if self.mp_server:
            self.mp_server.stop(); self.mp_server=None
        self.mp_is_host=False

    # ── events ────────────────────────────────────────────────────────────────
    def events(self):
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: return False

            if self.state==GS.SPLASH:
                if ev.type in(pygame.KEYDOWN,pygame.MOUSEBUTTONDOWN):
                    # pre-fill name input with current name
                    self.char_name_input=self.player_name if self.player_name!="Hero" else ""
                    self.state=GS.CHAR_SELECT

            elif self.state==GS.CHAR_SELECT:
                if ev.type==pygame.KEYDOWN:
                    if ev.key==pygame.K_RETURN:
                        self._confirm_char()
                    elif ev.key==pygame.K_BACKSPACE:
                        self.char_name_input=self.char_name_input[:-1]
                    elif ev.key==pygame.K_LEFT:
                        self.char_sel_idx=(self.char_sel_idx-1)%len(CHARACTERS)
                    elif ev.key==pygame.K_RIGHT:
                        self.char_sel_idx=(self.char_sel_idx+1)%len(CHARACTERS)
                    elif ev.key==pygame.K_ESCAPE:
                        self.state=GS.SPLASH
                    else:
                        if len(self.char_name_input)<16:
                            self.char_name_input+=ev.unicode
                elif ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                    # click on character cards
                    n=len(CHARACTERS); card_w=150; gap=18
                    total=n*card_w+(n-1)*gap; start_x=SW//2-total//2
                    for i in range(n):
                        cx2=start_x+i*(card_w+gap)
                        if cx2<=ev.pos[0]<=cx2+card_w and 165<=ev.pos[1]<=385:
                            self.char_sel_idx=i
                if self.char_confirm_btn.hit(ev): self._confirm_char()
                if self.char_back_btn.hit(ev):    self.state=GS.SPLASH

            elif self.state==GS.MAP:
                # hover detection
                mp=pygame.mouse.get_pos()
                self.map_hover=-1
                for i,lv in enumerate(LEVELS):
                    px,py=lv["map_pos"]
                    if math.hypot(mp[0]-px,mp[1]-py)<30:
                        self.map_hover=i
                for b in self.map_back:
                    if b.hit(ev): return False
                for b in self.map_mp_btn:
                    if b.hit(ev): self.state=GS.MP_MENU
                if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                    for i,lv in enumerate(LEVELS):
                        px,py=lv["map_pos"]
                        if math.hypot(ev.pos[0]-px,ev.pos[1]-py)<28 and i<=self.unlocked:
                            self.level=i; self._init_level()
                            self._start_transition(GS.PLAYING)

            elif self.state==GS.PLAYING:
                if ev.type==pygame.KEYDOWN and ev.key==pygame.K_ESCAPE:
                    self.state=GS.PAUSED

            elif self.state==GS.PAUSED:
                for i,b in enumerate(self.pause_btns):
                    if b.hit(ev):
                        if i==0: self.state=GS.PLAYING
                        elif i==1: self._init_level(); self.state=GS.PLAYING
                        else: self.state=GS.MAP; play_bgm("jungle")

            elif self.state==GS.MP_MENU:
                for i,b in enumerate(self.mp_menu_btns):
                    if b.hit(ev):
                        if i==0:   # Host
                            self.mp_server=MPServer()
                            self.mp_server.start()
                            self.mp_is_host=True
                            name=self.player_name if hasattr(self,"player_name") else "Host"
                            self.mp_client=MPClient("127.0.0.1", PORT, name)
                            self.mp_client.connect()
                            self.state=GS.MP_HOST
                        elif i==1: # Join
                            self.mp_join_input=""; self.mp_join_error=""
                            self.state=GS.MP_JOIN
                        else:
                            self.state=GS.MAP

            elif self.state==GS.MP_HOST:
                for i,b in enumerate(self.mp_host_btns):
                    if b.hit(ev):
                        if i==0:   # Start game
                            if self.mp_server:
                                self.mp_server.send_start(self.level)
                            self._init_level(); self.state=GS.MP_LOBBY
                        elif i==1: # Copy Code
                            if self.mp_server:
                                share=self.mp_server.share_string
                                try:
                                    pygame.scrap.init()
                                    pygame.scrap.put(pygame.SCRAP_TEXT, share.encode())
                                except Exception:
                                    pass
                                try:
                                    import pyperclip; pyperclip.copy(share)
                                except Exception:
                                    pass
                                self.mp_copied_timer[0]=120
                        else:      # Cancel
                            self._mp_cleanup(); self.state=GS.MP_MENU

            elif self.state==GS.MP_JOIN:
                if ev.type==pygame.KEYDOWN:
                    if ev.key==pygame.K_RETURN:
                        self._mp_do_join()
                    elif ev.key==pygame.K_BACKSPACE:
                        self.mp_join_input=self.mp_join_input[:-1]
                    elif ev.key==pygame.K_ESCAPE:
                        self.state=GS.MP_MENU
                    else:
                        if len(self.mp_join_input)<20:
                            self.mp_join_input+=ev.unicode
                for i,b in enumerate(self.mp_join_btns):
                    if b.hit(ev):
                        if i==0: self._mp_do_join()
                        else:    self.state=GS.MP_MENU

            elif self.state==GS.MP_LOBBY:
                # host start button
                if self.mp_is_host:
                    if self.mp_lobby_start_btn.hit(ev):
                        if self.mp_server:
                            self.mp_server.send_start(self.level)
                        self._init_level(); self.state=GS.MP_PLAYING
                    # approve/reject pending requests
                    if self.mp_server:
                        pending=self.mp_server.pending_requests
                        for j,req in enumerate(pending[:3]):
                            if self.mp_approve_btns[j].hit(ev):
                                self.mp_server.approve(req["pid"])
                            if self.mp_reject_btns[j].hit(ev):
                                self.mp_server.reject(req["pid"])
                for b in self.mp_lobby_btns:
                    if b.hit(ev):
                        self._mp_cleanup(); self.state=GS.MP_MENU

            elif self.state==GS.MP_WAITING:
                # joiner waiting for host approval
                if ev.type==pygame.KEYDOWN and ev.key==pygame.K_ESCAPE:
                    self._mp_cleanup(); self.state=GS.MP_MENU

            elif self.state==GS.MP_PLAYING:
                if ev.type==pygame.KEYDOWN and ev.key==pygame.K_ESCAPE:
                    self.state=GS.PAUSED

            elif self.state in(GS.LEVEL_WIN,GS.GAME_OVER):
                btns=self.win_btns if self.state==GS.LEVEL_WIN else self.over_btns
                for i,b in enumerate(btns):
                    if b.hit(ev):
                        if i==0:
                            if self.state==GS.LEVEL_WIN:
                                self.level=min(self.level+1,len(LEVELS)-1)
                            self._init_level(); self._start_transition(GS.PLAYING)
                        else:
                            self.state=GS.MAP; play_bgm("jungle")
        return True

    def _start_transition(self,target):
        self.trans_alpha=0; self.trans_dir=1; self.trans_target=target
        self.state=GS.TRANSITION

    # ── update ────────────────────────────────────────────────────────────────
    def update(self):
        self.tick+=1

        # MP_LOBBY: watch for server start signal
        if self.state==GS.MP_LOBBY:
            if self.mp_client and self.mp_client.started:
                self.level=self.mp_client.level
                self._init_level(); self.state=GS.MP_PLAYING
            return

        # MP_WAITING: joiner waiting for host approval
        if self.state==GS.MP_WAITING:
            if self.mp_client:
                if self.mp_client.rejected:
                    self._mp_cleanup(); self.state=GS.MP_MENU
                elif self.mp_client.approved:
                    self.state=GS.MP_LOBBY
                elif self.mp_client.started:
                    self.level=self.mp_client.level
                    self._init_level(); self.state=GS.MP_PLAYING
            return

        # MP_PLAYING: run normal game + sync
        if self.state==GS.MP_PLAYING:
            self._run_game_logic()
            if self.mp_client and self.mp_client.connected:
                p=self.player
                self.mp_client.send_update(p.x,p.y,p.score,p.lives,p.hp,p.energy,
                                           self.state==GS.LEVEL_WIN)
            return

        if self.state==GS.TRANSITION:
            self.trans_alpha+=self.trans_dir*8
            if self.trans_alpha>=255: self.trans_dir=-1; self.trans_alpha=255
            if self.trans_alpha<=0 and self.trans_dir==-1:
                self.trans_alpha=0; self.state=self.trans_target
            return

        if self.state==GS.PLAYING:
            self._run_game_logic()

    def _run_game_logic(self):
        cfg=LEVELS[self.level]
        keys=pygame.key.get_pressed()
        self.player.update(keys,self.platforms,self.world_w)
        self.weather.update(self.tick)

        # ── SHOOT  (F key or mouse click) ────────────────────────────────────
        if self.shoot_cooldown>0: self.shoot_cooldown-=1
        fire=(keys[pygame.K_f] or pygame.mouse.get_pressed()[0])
        if fire and self.shoot_cooldown==0 and self.ammo>0:
            bx=self.player.x+(Player.W if self.player.facing==1 else 0)
            by=self.player.y+Player.H//2-3
            self.bullets.append(Bullet(bx,by,self.player.facing))
            self.ammo-=1; self.shoot_cooldown=14
            play(SND_GUN)
            self._burst(int(bx),int(by),(255,220,80),4)

        # ── BULLETS ──────────────────────────────────────────────────────────
        for bl in self.bullets[:]:
            bl.update(self.world_w)
            if not bl.alive:
                self.bullets.remove(bl); continue
            # hit platforms
            for p in self.platforms:
                if bl.rect.colliderect(p.rect):
                    bl.alive=False
                    self._burst(int(bl.x),int(bl.y),(255,200,80),5)
                    break
            if not bl.alive:
                self.bullets.remove(bl); continue
            # hit animals
            for an in self.animals[:]:
                if an.alive and bl.rect.colliderect(an.rect):
                    an.take_hit()
                    bl.alive=False
                    self._burst(int(an.x+an.w//2),int(an.y+an.h//2),an.col,10)
                    if not an.alive:
                        self.player.score+=an.score_val
                        self._burst(int(an.x+an.w//2),int(an.y),GOLD,16)
                    break
            if not bl.alive and bl in self.bullets:
                self.bullets.remove(bl)
            # hit flying enemies
            for fe in self.enemies[:]:
                if bl.alive and bl.rect.colliderect(fe.rect):
                    fe.hp-=1; bl.alive=False
                    self._burst(int(fe.x),int(fe.y),PURPLE,8)
                    if fe.hp<=0:
                        self.enemies.remove(fe); self.player.score+=30
                    break

        # ── ANIMAL ENEMIES ───────────────────────────────────────────────────
        for an in self.animals[:]:
            if not an.alive: continue
            an.update(self.player.x,self.player.y,self.platforms,self.world_w)
            # body contact
            if self.player.rect.colliderect(an.rect):
                if self.player.take_damage(an.dmg):
                    self._burst(self.player.rect.centerx,self.player.rect.centery,RED,8)
            # dragon fireball contact
            for fb in an.fireballs:
                fbr=pygame.Rect(int(fb[0])-8,int(fb[1])-8,16,16)
                if self.player.rect.colliderect(fbr):
                    if self.player.take_damage(20):
                        self._burst(self.player.rect.centerx,self.player.rect.centery,(255,120,20),10)
                    fb[3]=0  # destroy fireball

        # camera
        tc=self.player.x-SW//2+Player.W//2
        tc=max(0,min(tc,self.world_w-SW))
        self.camera=lerp(self.camera,tc,0.13)

        # pit death — fall in = lose a life immediately
        for pit in self.pits:
            pr=pygame.Rect(pit.x,GROUND_Y,pit.w,200)
            if self.player.rect.colliderect(pr) and self.player.y+Player.H>GROUND_Y-5:
                if self.player.invincible==0:
                    self._burst(self.player.rect.centerx,GROUND_Y,RED,20)
                    self.player._lose_life()
                    if self.player.dead:
                        self.won=False; self.finish_time=0.0
                        self.state=GS.GAME_OVER; return

        # collectibles
        for it in self.collectibles[:]:
            if self.player.rect.colliderect(it.rect):
                if it.kind=="heart":
                    self.player.hp=min(Player.MAX_HP,self.player.hp+35)
                    self.player.energy=min(Player.MAX_EN,self.player.energy+25)
                    self.ammo=min(12,self.ammo+6)   # heart also restores 6 bullets
                elif it.kind=="shield":
                    self.player.shield=300
                else:
                    self.player.score+=it.val
                self.player.items.append(it.kind)
                self._burst(it.rect.centerx,it.rect.centery,ITEM_COL[it.kind])
                play(SND_COLLECT)
                self.collectibles.remove(it)

        # boulders
        for b in self.boulders:
            b.update()
            if self.player.rect.colliderect(b.rect):
                if self.player.take_damage(20):
                    self._burst(self.player.rect.centerx,self.player.rect.centery,RED,8)

        # spikes
        for sp in self.spikes:
            if self.player.rect.colliderect(sp.rect):
                if self.player.take_damage(15):
                    self._burst(self.player.rect.centerx,self.player.rect.centery,(255,100,100),6)

        # flying enemies
        for fe in self.enemies:
            fe.update()
            if self.player.rect.colliderect(fe.rect):
                if self.player.vy>2 and self.player.rect.bottom<fe.rect.centery+10:
                    fe.hp-=1; self.player.vy=-10
                    self._burst(int(fe.x),int(fe.y),PURPLE,10)
                    if fe.hp<=0: self.enemies.remove(fe); self.player.score+=30
                else:
                    if self.player.take_damage(12):
                        self._burst(self.player.rect.centerx,self.player.rect.centery,PURPLE,6)

        # particles
        for p in self.particles[:]:
            p.update()
            if p.life<=0: self.particles.remove(p)

        # death — all 3 lives used up → GAME OVER
        if self.player.dead:
            self.won=False; self.finish_time=0.0
            self.state=GS.GAME_OVER; return

        # timer
        elapsed=pygame.time.get_ticks()/1000.0-self.start_t
        time_left=max(0,cfg["time"]-elapsed)
        if time_left<=0:
            self.won=False; self.finish_time=elapsed; self.state=GS.GAME_OVER; return

        # finish
        if self.player.rect.colliderect(self.finish.zone):
            self.finish_time=elapsed; self.won=True
            self.total_score+=self.player.score
            self.unlocked=max(self.unlocked,self.level+1)
            self._burst(self.finish.x,GROUND_Y-80,GOLD,50)
            play(SND_FINISH)
            self.state=GS.LEVEL_WIN

    # ── draw ──────────────────────────────────────────────────────────────────
    def draw(self):
        cam=int(self.camera)
        cfg=LEVELS[self.level]
        elapsed=pygame.time.get_ticks()/1000.0-self.start_t
        time_left=max(0,cfg["time"]-elapsed)

        if self.state==GS.SPLASH:
            self._draw_splash(); return
        if self.state==GS.CHAR_SELECT:
            draw_char_select(screen,self.tick,self.char_name_input,
                             self.char_sel_idx,self.char_confirm_btn,
                             self.char_back_btn); return
        if self.state==GS.MAP:
            draw_map(screen,self.tick,self.unlocked,self.map_hover,
                     self.map_back+self.map_mp_btn); return
        if self.state==GS.MP_MENU:
            draw_mp_menu(screen,self.tick,self.mp_menu_btns); return
        if self.state==GS.MP_HOST:
            draw_mp_host(screen,self.tick,self.mp_server,self.mp_host_btns,
                         self.mp_qr_cache,self.mp_copied_timer); return
        if self.state==GS.MP_JOIN:
            draw_mp_join(screen,self.tick,self.mp_join_input,
                         self.mp_join_error,self.mp_join_btns); return
        if self.state==GS.MP_LOBBY:
            lobby=self.mp_server.player_list if self.mp_is_host else \
                  (self.mp_client.lobby_list if self.mp_client else [])
            my_id=self.mp_client.my_id if self.mp_client else 1
            pending=self.mp_server.pending_requests if self.mp_is_host and self.mp_server else []
            approve_btns=self.mp_approve_btns[:len(pending)] if self.mp_is_host else []
            reject_btns =self.mp_reject_btns[:len(pending)]  if self.mp_is_host else []
            extra=([self.mp_lobby_start_btn]+self.mp_lobby_btns+approve_btns+reject_btns) \
                  if self.mp_is_host else self.mp_lobby_btns
            draw_mp_lobby(screen,self.tick,lobby,self.mp_is_host,my_id,pending,extra); return
        if self.state==GS.MP_WAITING:
            code=self.mp_client._code if self.mp_client else ""
            name=self.player_name
            draw_mp_waiting(screen,self.tick,name,code); return
        if self.state==GS.TRANSITION:
            self._draw_game(cam,time_left)
            draw_transition(screen,self.level,self.trans_alpha); return
        if self.state==GS.PAUSED:
            self._draw_game(cam,time_left); self._draw_pause(); return
        if self.state in(GS.LEVEL_WIN,GS.GAME_OVER):
            self._draw_game(cam,time_left)
            btns=self.win_btns if self.state==GS.LEVEL_WIN else self.over_btns
            draw_scoreboard(screen,self.player,self.finish_time,self.level,
                            self.won,self.tick,btns); return
        if self.state==GS.MP_PLAYING:
            self._draw_game(cam,time_left)
            # draw remote players on top
            if self.mp_client:
                for idx,rp in enumerate(self.mp_client.other_players):
                    draw_remote_player(screen,cam,rp,idx)
            return
        self._draw_game(cam,time_left)

    def _draw_game(self,cam,time_left):
        draw_bg(screen,cam,self.level,self.tick)
        self.weather.draw(screen)
        for p in self.platforms: p.draw(screen,cam)
        for pit in self.pits:    pit.draw(screen,cam)
        for sp in self.spikes:   sp.draw(screen,cam,self.tick)
        for it in self.collectibles: it.draw(screen,cam,self.tick)
        for b in self.boulders:  b.draw(screen,cam)
        for fe in self.enemies:  fe.draw(screen,cam)
        for an in self.animals:  an.draw(screen,cam)
        for bl in self.bullets:  bl.draw(screen,cam)
        for pt in self.particles: pt.draw(screen,cam)
        self.finish.draw(screen,cam,self.tick)
        self.player.draw(screen,cam)
        draw_hud(screen,self.player,time_left,self.level,self.tick,
                 self.ammo,self.shoot_cooldown)

    def _draw_splash(self):
        grad(screen,(5,18,45),(18,55,25),pygame.Rect(0,0,SW,SH))
        self.splash_alpha=min(255,self.splash_alpha+3)
        for i in range(50):
            sx=(i*137+self.tick)%SW; sy=(i*97)%(SH//2)
            br=int(128+127*math.sin(self.tick*0.05+i))
            pygame.draw.circle(screen,(br,br,br),(sx,sy),1)
        t=F80.render("JUNGLE SURVIVAL",True,GOLD); t.set_alpha(self.splash_alpha)
        screen.blit(t,t.get_rect(center=(SW//2,SH//2-80)))
        s=F28.render("5 Levels  |  3 Lives  |  Survival Platformer",True,(170,225,170))
        s.set_alpha(self.splash_alpha); screen.blit(s,s.get_rect(center=(SW//2,SH//2)))
        if self.splash_alpha>200:
            blink=int(200+55*math.sin(self.tick*0.09))
            p=F28.render("Press any key to continue",True,(blink,blink,blink))
            screen.blit(p,p.get_rect(center=(SW//2,SH//2+70)))

    def _draw_pause(self):
        ov=pygame.Surface((SW,SH),pygame.SRCALPHA); ov.fill((0,0,0,170)); screen.blit(ov,(0,0))
        pr=pygame.Rect(SW//2-220,200,440,320)
        grad(screen,(10,22,52),(4,10,26),pr)
        pygame.draw.rect(screen,GOLD,pr,3,border_radius=16)
        shadow_text(screen,"PAUSED",F60,WHITE,SW//2-88,218,(0,0,0),3)
        for b in self.pause_btns: b.draw(screen)

    def run(self):
        running=True
        while running:
            running=self.events()
            self.update()
            self.draw()
            pygame.display.flip()
            clock.tick(FPS)
        pygame.quit()

if __name__=="__main__":
    Game().run()
