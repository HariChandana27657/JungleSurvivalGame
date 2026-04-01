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

---

## 🌟 Conclusion

Jungle Survival is a complete mini-game ecosystem combining gameplay, design, sound, and networking. It serves as a strong foundation for building advanced games and experimenting with creative ideas.

---

⭐ Feel free to explore, modify, and expand this project!
