# RicePi

A fullscreen personal dashboard for Raspberry Pi — riced Linux desktop aesthetic with wallpaper-derived theming, floating widgets, pixel fonts, scanlines, and micro-animations.

![RicePi aesthetic: lofi/anime wallpaper with minimal floating widgets]

## Features

- **Auto-themed colors** extracted from your wallpaper at boot (`init_theme.py` + `colorthief`)
- **Clock** with colon pulse, minute digit flip, and random glitch effect
- **Weather** via Open-Meteo with animated Meteocons-style SVG icons
- **Calendar** grid with today glow and upcoming local events
- **Sysinfo** neofetch-style panel (OS, kernel, uptime, RAM, CPU temp)
- **Quotes** with terminal cursor blink and rotation
- **Animation player** for GIF/WebM files with crossfade cycling
- **CRT scanlines** and pixel-art borders across the entire screen

## Requirements

- Raspberry Pi OS (or any Linux with `/proc`, `/sys`)
- Python 3.11+
- Chromium for kiosk mode
- Network access for weather and Google Fonts

## Quick Start (Development)

```bash
cd ricepi
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Generate theme from wallpaper
python3 init_theme.py

# Run server
uvicorn main:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000` in a browser.

## Configuration

Edit `config.json` at the project root. The frontend loads it from `GET /api/config`.

Key options:

| Section | Purpose |
|---------|---------|
| `wallpaper` | Path to active wallpaper image |
| `theme` | Scanlines, pixel borders, glitch clock intervals, fallback colors |
| `location` | Lat/lon/city for Open-Meteo weather |
| `clock` | 12h/24h format, show seconds |
| `weather` | Metric/imperial, update interval |
| `calendar` | Local events source, upcoming count |
| `animation` | Folder, single/cycle mode, cycle interval |
| `quote` | Rotation interval, cursor blink |
| `sysinfo` | Which stats to show |

Reload without restart:

```bash
curl -X POST http://localhost:8000/api/reload
```

This re-reads `config.json` and regenerates `theme.css`.

## Customization

### Wallpaper

Replace `static/wallpapers/current.jpg` with your image (1920×1080 recommended), then:

```bash
python3 init_theme.py
# or
curl -X POST http://localhost:8000/api/reload
```

### Animations

Drop `.gif` or `.webm` files into `static/animations/`.

Set in `config.json`:

```json
"animation": {
  "folder": "static/animations/",
  "mode": "cycle",
  "current": "",
  "cycle_every_mins": 5
}
```

- `loop_single` — plays one file (first available, or `current` if set)
- `cycle` — crossfades through all files every N minutes

### Quotes & Events

- Quotes: edit `data/quotes.json`
- Calendar events: edit `data/events.json` (when `calendar.source` is `"local"`)

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Dashboard UI |
| GET | `/api/config` | Config (+ available animation files) |
| POST | `/api/reload` | Reload config and regenerate theme |
| GET | `/api/weather` | Cached weather data |
| GET | `/api/sysinfo` | Live system stats |
| GET | `/api/quotes` | Quote bank |
| GET | `/api/events` | Calendar events |

## Raspberry Pi Boot Setup

### 1. Install project

```bash
cd ~
git clone https://github.com/sh4shv4t/RicePi
cd ricepi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 init_theme.py
```

### 2. Install systemd services

```bash
sudo cp systemd/ricepi-server.service /etc/systemd/system/
sudo cp systemd/ricepi-kiosk.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ricepi-server.service
sudo systemctl enable ricepi-kiosk.service
sudo systemctl start ricepi-server.service
sudo systemctl start ricepi-kiosk.service
```

Check status:

```bash
sudo systemctl status ricepi-server
sudo systemctl status ricepi-kiosk
journalctl -u ricepi-server -f
```

### 3. Autologin + desktop (if not already configured)

Enable desktop autologin via `raspi-config` → System Options → Boot / Auto Login.

Ensure Chromium is installed:

```bash
sudo apt install chromium-browser
```

## Project Structure

```
ricepi/
├── main.py              # FastAPI app
├── init_theme.py        # Wallpaper color extraction → theme.css
├── scheduler.py         # Weather fetch (APScheduler)
├── sysinfo.py           # /proc and /sys readers
├── config.json          # User configuration
├── theme.css            # Auto-generated — do not edit manually
├── requirements.txt
├── static/
│   ├── index.html
│   ├── style.css
│   ├── animations.css
│   ├── *.js             # Widget modules
│   ├── wallpapers/current.jpg
│   └── animations/      # Your GIF/WebM files
├── data/
│   ├── quotes.json
│   ├── events.json
│   └── weather_cache.json
└── systemd/
    ├── ricepi-server.service
    └── ricepi-kiosk.service
```

## Design Notes

- All colors come from CSS variables in `theme.css` — never hardcoded in `style.css`
- Module backgrounds stay at ≤12% opacity so the wallpaper stays visible
- Center of the screen is intentionally empty
- `border-radius: 0` everywhere — no rounded corners
- Scanline overlay covers the entire display including the animation player

## License

MIT — Meteocons-inspired weather SVGs are inline derivatives for animation hooks.
