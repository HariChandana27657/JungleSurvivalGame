# 🌴 Jungle Survival — Game Project


## 🎮 Overview

**Jungle Survival** is a feature-rich **2D arcade survival game** built using Python and Pygame. It combines fast-paced gameplay, multiple themed levels, procedural sound design, animations, and a multiplayer system where players can join via a shared invite link.

The game is designed to demonstrate **game development concepts, UI/UX design, multiplayer networking, and creative sound/animation systems** in a single project.

---

## 🚀 Features

### 🧩 Core Game

* 2-file structure:

  * `game.py` → Main gameplay
  * `multiplayer.py` → Networking system
* Run using:

```bash
python -B game.py
```

---

## 🎯 Game Flow

1. Splash Screen (animated stars + fade-in title)
2. Character Selection (enter name + choose avatar)
3. World Map (select levels)
4. Gameplay (5 unique levels)
5. Scoreboard (result + grade)

---

## 🌍 Levels

| Level | Theme        | Width  | Time | Difficulty |
| ----- | ------------ | ------ | ---- | ---------- |
| 1     | Jungle Dawn  | 3000px | 100s | Easy       |
| 2     | Lava Cavern  | 3600px | 85s  | Medium     |
| 3     | Ice Peaks    | 4000px | 70s  | Hard       |
| 4     | Storm Ruins  | 4600px | 60s  | Very Hard  |
| 5     | Shadow Abyss | 5000px | 50s  | Extreme    |

Each level includes:

* Unique backgrounds
* Weather effects
* Increasing difficulty

---

## 🌦 Weather System

* 🌧 Jungle → Rain
* ⛈ Storm → Lightning + heavy rain
* ❄ Ice → Snowfall
* 🔥 Lava → Embers + lava animation
* 🌌 Abyss → Mist + void effects

---

## 👤 Player System

* 3 lives system
* HP bar + Energy bar
* Energy affects speed and jumping
* Shield (temporary invincibility)
* Heart pickup restores HP + energy + ammo
* Warning effects for low HP and energy

---

## 🧍 Characters

| Character | Ability           |
| --------- | ----------------- |
| Boy       | Fast              |
| Girl      | High jump         |
| Grandpa   | High durability   |
| Grandma   | Better collection |
| Officer   | Shield bonus      |

---

## ⚔ Obstacles & Enemies

### Obstacles

* Rolling boulders
* Spike traps
* Flying bats
* Pitfalls

### Animal Enemies

| Animal | HP     | Special      |
| ------ | ------ | ------------ |
| Cat    | Low    | Ground chase |
| Dog    | Medium | Jumping      |
| Dragon | High   | Fire attacks |

---

## 🔫 Gun System

* Shoot using `F` or mouse click
* 12 ammo per life
* Bullets destroy enemies
* Ammo restored via pickups

---

## 🎮 Controls

| Key       | Action |
| --------- | ------ |
| A / D     | Move   |
| SPACE / W | Jump   |
| F / Click | Shoot  |
| ESC       | Pause  |

---

## 📊 HUD System

* Lives (hearts)
* HP bar
* Energy bar
* Score display
* Ammo indicator
* Timer bar
* Level name

---

## 🎁 Collectibles

| Item   | Points        |
| ------ | ------------- |
| Candy  | +10           |
| Basket | +25           |
| Stick  | +5            |
| Gem    | +60           |
| Heart  | Restore       |
| Shield | Invincibility |

---

## 🎵 Sound System

All sounds are **procedurally generated (no external files)**:

* Jump sound
* Collect chime
* Hit sound
* Gunshot
* Death tone
* Background music
* Finish fanfare

---

## 🏆 Scoreboard System

* Displays:

  * Item breakdown
  * Time taken
  * Total score
  * Grade (S / A / B / C)
* Animated UI effects

---

## 🗺 World Map

* Unlockable levels
* Interactive nodes
* Hover info panels
* Click to play

---

## 🌐 Multiplayer System

### 👥 Features

* Supports up to 4 players
* Online play using invite link

### 🔗 How it Works

* Host creates room
* Game generates:

  * Invite code
  * QR code
* Players join using:

  * Code or QR scan
* Lobby shows all players
* Host starts game

### ⚙️ Tech Used

* `socket` + `threading`
* SSH tunnel via serveo.net
* QR code system

---

## 🛠 Tech Stack

* Python 3
* Pygame
* NumPy
* qrcode + Pillow
* pyperclip
* socket programming

---

## 📁 Project Structure

```
JungleSurvival/
│
├── game.py
├── multiplayer.py
├── assets/
├── sounds/
├── ui/
└── data/
```

---

## ▶️ How to Run

1. Install dependencies:

```bash
pip install pygame numpy pillow qrcode pyperclip
```

2. Run the game:

```bash
python -B game.py
```

---

## 🎯 Learning Objectives

This project demonstrates:

* Game development using Pygame
* UI/UX design principles
* Multiplayer networking
* Procedural sound generation
* Animation and physics systems

---

## ⚠️ Disclaimer

This project is developed **for educational purposes only**.

It is intended for:

* Learning game development concepts
* Exploring UI/UX design
* Understanding multiplayer systems
* Adapting and experimenting with new ideas

This project is **not intended for commercial use**.

# 🚀 Future Enhancements & Improvements

## 🌐 Live Game

You can play and download the deployed version of the game here:
👉 [https://jungle-survival-game-x82b.vercel.app/](https://jungle-survival-game-x82b.vercel.app/)

---

## 🟪 Multiplayer Improvements

To enhance the multiplayer experience, future updates will focus on:

* Real-time synchronization improvements for smoother gameplay
* Dedicated server hosting instead of SSH tunnels for better stability
* Player matchmaking system (auto-join rooms)
* In-game voice/chat communication between players
* Cross-platform support (PC + mobile browsers)
* Anti-lag and latency optimization
* Player profiles and persistent progress tracking

---

## 🟪 Level Upgrades

To make gameplay more engaging and challenging:

* Add more levels beyond Level 5
* Introduce dynamic difficulty scaling
* Create boss levels with unique mechanics
* Add hidden bonus levels and secret paths
* Introduce moving platforms and interactive terrain
* Add environmental hazards like quicksand, collapsing bridges, and traps

---

## 🟪 New Threats & Enemies

Future versions will include:

* New animal enemies with special abilities
* Smarter AI (pathfinding, coordinated attacks)
* Flying and underground enemies
* Boss enemies (giant dragon, jungle beast, shadow monster)
* Trap-based enemies (camouflage predators, ambush attacks)

---

## 🟪 Theme Expansion

The game will expand with new visual themes:

* Desert Storm 🌵
* Ocean Depths 🌊
* Sky Islands ☁
* Cyber Jungle 🤖
* Ancient Temple 🏛

Each theme will include:

* Unique background design
* Weather effects
* Custom soundtracks
* Theme-based enemies

---

## 🟪 Dashboard & UI Enhancements

To improve user experience:

* Theme-based dashboard (changes based on selected level/theme)
* Advanced leaderboard with rankings and stats
* Player performance analytics (accuracy, survival time, efficiency)
* Animated UI transitions and effects
* Customizable UI themes (dark mode, neon mode, etc.)

---

## 🟪 Gameplay Enhancements

* Power-ups (speed boost, double score, magnet collector)
* Skill upgrades per character
* Inventory system
* Achievements and rewards system
* Daily challenges and missions

---

## 🟪 Audio & Visual Upgrades

* Enhanced procedural sound system
* Dynamic background music based on gameplay intensity
* Improved animations and particle effects
* Character-specific sound effects
* Cinematic transitions

---

## 🟪 Long-Term Vision

The long-term goal is to evolve *Jungle Survival* into a **fully interactive multiplayer arcade platform** with:

* Global leaderboard system
* Online tournaments
* Cloud-based player data
* Mobile and web compatibility
* Community-driven content and mod support

---

## 🌟 Conclusion

These future enhancements aim to transform the game into a more immersive, competitive, and scalable experience while maintaining its core arcade-style fun. The focus remains on improving multiplayer interaction, expanding gameplay depth, and introducing creative new themes and challenges.

