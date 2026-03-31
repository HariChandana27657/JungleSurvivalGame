# Jungle Survival Game

A feature-rich 2D survival platformer built with Python and Pygame.

## Features
- 5 themed levels (Jungle, Lava, Ice, Storm, Abyss)
- 3 lives system, energy bar, gun with ammo
- Animal enemies: Cat, Dog, Dragon (with fireballs)
- 5 playable characters: Boy, Girl, Grandpa, Grandma, Officer
- Online multiplayer (up to 4 players) via relay server
- Host approval lobby, QR code invite, copy-code sharing
- Weather effects, procedural sound, world map

## Run Locally

```bash
pip install -r requirements.txt
python -B game.py
```

## Controls

| Key | Action |
|-----|--------|
| A / D or Arrow Keys | Move |
| SPACE / W / Up | Jump |
| F or Left Click | Shoot |
| ESC | Pause |

## Multiplayer Setup

1. Deploy `relay_server.py` to Railway (see deploy instructions)
2. Update `RELAY_HOST` in `multiplayer.py` with your Railway domain
3. Host creates a room, shares the 6-character code
4. Friends paste the code in Join Room and connect

## Files

| File | Purpose |
|------|---------|
| `game.py` | Main game |
| `multiplayer.py` | Networking client/server |
| `relay_server.py` | Deploy to Railway for online play |
| `requirements.txt` | Python dependencies |
| `Procfile` | Railway start command |
