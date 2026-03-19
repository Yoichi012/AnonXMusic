# AnonXMusic — Setup Guide

> **Version 4.0.0 — Cookie-Less Hybrid Router Architecture**

---

## 1. Project Overview

### What is AnonXMusic?

AnonXMusic is a **Telegram music bot** built with [Kurigram](https://github.com/AnonXMusic/Kurigram) (Pyrogram fork) and [PyTgCalls](https://github.com/pytgcalls/pytgcalls). It streams audio and video directly into Telegram voice chats — no file downloads, no local storage.

### New Architecture: Cookie-Less Hybrid Router

The v4.0 architecture eliminates all dependency on **yt-dlp**, **cookies**, and **local media downloads**. Instead, it uses a **Smart Router** with two engines:

| Engine | Used For | Source |
|--------|----------|--------|
| **JioSaavn** (Engine A) | `/play <text query>` — searches by song name | [saavn.dev](https://saavn.dev) public API |
| **Cobalt** (Engine B) | `/play <URL>` or `/vplay` — YouTube, Spotify, SoundCloud URLs | Self-hosted [Cobalt](https://github.com/imputnet/cobalt) Docker container |

**How the Smart Router decides:**

```
/vplay <anything>       → Cobalt (video=True)
/play <yt/spotify URL>  → Cobalt (audio only)
/play <plain text>      → JioSaavn (320kbps audio)
```

**Key benefits:**
- ✅ No yt-dlp — no cookie expiry, no bot bans
- ✅ No downloads — direct stream URLs piped to PyTgCalls
- ✅ No Google auth — Cobalt handles YouTube extraction
- ✅ Self-hosted — full control, no third-party rate limits

---

## 2. Prerequisites

| Requirement | Minimum | Notes |
|-------------|---------|-------|
| **Python** | 3.11+ | `python3 --version` |
| **pip** | Latest | `pip3 install -U pip` |
| **ffmpeg** | 5.0+ | `ffmpeg -version` — required by PyTgCalls |
| **Docker** | 24+ | `docker --version` — for Cobalt container |
| **Docker Compose** | v2+ | `docker compose version` |
| **MongoDB** | Atlas (free tier) | [cloud.mongodb.com](https://cloud.mongodb.com) |
| **Telegram** | API_ID + API_HASH | [my.telegram.org/apps](https://my.telegram.org/apps) |
| **Pyrogram Session** | String session | From [@StringFatherBot](https://t.me/StringFatherBot) |
| **Bot Token** | From BotFather | [@BotFather](https://t.me/BotFather) |
| **Server** | 1 vCPU / 1 GB RAM | AWS EC2, Oracle, etc. |

---

## 3. Required `.env` Variables

Create a `.env` file in the project root (or copy `sample.env`):

```bash
cp sample.env .env
```

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `API_ID` | Telegram API ID from [my.telegram.org](https://my.telegram.org/apps) | `12345678` |
| `API_HASH` | Telegram API Hash from [my.telegram.org](https://my.telegram.org/apps) | `abcdef1234567890abcdef` |
| `BOT_TOKEN` | Bot token from [@BotFather](https://t.me/BotFather) | `123456:ABC-DEF1234ghIkl-...` |
| `MONGO_URL` | MongoDB Atlas connection string | `mongodb+srv://user:pass@cluster.mongodb.net/...` |
| `LOGGER_ID` | Telegram channel/group ID for logging | `-1001234567890` |
| `OWNER_ID` | Your Telegram user ID | `123456789` |
| `SESSION` | Pyrogram string session (assistant #1) | `BQF...AA` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SESSION2` | Pyrogram string session (assistant #2) | _(empty)_ |
| `SESSION3` | Pyrogram string session (assistant #3) | _(empty)_ |
| `COBALT_URL` | Cobalt API endpoint | `http://127.0.0.1:9000` |
| `JIOSAAVN_API_URL` | JioSaavn API endpoint | `https://saavn.dev` |
| `DURATION_LIMIT` | Maximum song duration in minutes | `60` |
| `QUEUE_LIMIT` | Maximum queue size per chat | `20` |
| `PLAYLIST_LIMIT` | Maximum playlist import size | `20` |
| `LANG_CODE` | Default language code | `en` |
| `AUTO_LEAVE` | Auto-leave VC when queue ends | `False` |
| `AUTO_END` | Auto-end stream when queue ends | `False` |
| `THUMB_GEN` | Generate thumbnails for now-playing | `True` |
| `VIDEO_PLAY` | Allow video playback | `True` |
| `SUPPORT_CHAT` | Support group link | `https://t.me/DevilsHeavenMF` |
| `SUPPORT_CHANNEL` | Support channel link | `https://t.me/FallenAssociation` |
| `DEFAULT_THUMB` | Default thumbnail URL | _(Telegraph URL)_ |
| `PING_IMG` | Image for `/ping` command | _(Catbox URL)_ |
| `START_IMG` | Image for `/start` command | _(Catbox URL)_ |

---

## 4. Docker Setup (Cobalt)

Cobalt is a **self-hosted YouTube/Spotify stream extractor** that runs as a Docker container. It replaces yt-dlp entirely.

### Start Cobalt

```bash
cd ~/AnonXMusic
sudo docker compose -f docker/cobalt-compose.yml up -d
```

### Verify Cobalt Is Running

```bash
# Check container status
sudo docker ps

# Test API endpoint
curl -X POST http://127.0.0.1:9000/api/json \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"url":"https://youtu.be/dQw4w9WgXcQ","isAudioOnly":true}'
```

**Expected response:**
```json
{"status":"stream","url":"https://..."}
```

### Restart Cobalt

```bash
sudo docker compose -f docker/cobalt-compose.yml restart
```

### Stop Cobalt

```bash
sudo docker compose -f docker/cobalt-compose.yml down
```

### View Cobalt Logs

```bash
sudo docker compose -f docker/cobalt-compose.yml logs -f
```

### Docker Daemon Fix (RHEL 10 / Amazon Linux)

If Docker fails with iptables errors on RHEL 10:

```bash
sudo tee /etc/docker/daemon.json <<EOF
{
  "iptables": false,
  "ip6tables": false
}
EOF
sudo systemctl restart docker
```

---

## 5. Bot Installation Steps

### Step 1: Clone the Repository

```bash
git clone https://github.com/Yoichi012/AnonXMusic.git ~/AnonXMusic
cd ~/AnonXMusic
```

### Step 2: Install System Dependencies

```bash
# RHEL / Amazon Linux
sudo dnf install -y python3.11 python3.11-pip ffmpeg git screen

# Ubuntu / Debian
sudo apt install -y python3.11 python3.11-pip ffmpeg git screen
```

### Step 3: Install Python Dependencies

```bash
pip3 install -U pip
pip3 install -U -r requirements.txt
```

### Step 4: Configure Environment

```bash
cp sample.env .env
nano .env   # Fill in all REQUIRED variables
```

Make sure these lines exist in `.env`:
```
COBALT_URL=http://127.0.0.1:9000
JIOSAAVN_API_URL=https://saavn.dev
```

### Step 5: Start Cobalt (if not already running)

```bash
sudo docker compose -f docker/cobalt-compose.yml up -d
```

### Step 6: Start the Bot

```bash
screen -S anonxmusic
bash start
```

Press `Ctrl+A` then `D` to detach from the screen session.

---

## 6. Bot Commands List

### 🎵 Music Commands (Group Only)

| Command | Description |
|---------|-------------|
| `/play <song name>` | Search & play from JioSaavn (320kbps audio) |
| `/play <YouTube/Spotify URL>` | Stream from URL via Cobalt |
| `/playforce <query/URL>` | Force-play (skip queue, play immediately) |
| `/vplay <query/URL>` | Play video in voice chat |
| `/vplayforce <query/URL>` | Force-play video |
| `/pause` | Pause current stream |
| `/resume` | Resume paused stream |
| `/skip` or `/next` | Skip to next track in queue |
| `/end` or `/stop` | Stop playback and clear queue |
| `/seek <seconds>` | Seek forward in current track |
| `/seekback <seconds>` | Seek backward in current track |
| `/loop <count>` | Loop current track N times |
| `/queue` or `/playing` | View current queue |

### ⚙️ Settings Commands (Group Only)

| Command | Description |
|---------|-------------|
| `/playmode` or `/settings` | Open playback settings panel |
| `/lang` or `/language` | Change bot language |
| `/auth <reply>` | Authorize a user to control the bot |
| `/unauth <reply>` | Remove user authorization |
| `/authlist` | List authorized users |
| `/admincache` or `/reload` | Refresh admin cache |

### 🛡️ Admin / Sudo Commands

| Command | Description | Access |
|---------|-------------|--------|
| `/broadcast` | Broadcast message to all chats | Sudo |
| `/stop_gcast` | Stop ongoing broadcast | Sudo |
| `/addsudo <reply/ID>` | Add a sudo user | Owner |
| `/delsudo <reply/ID>` | Remove a sudo user | Owner |
| `/listsudo` | List all sudo users | Anyone |
| `/blacklist <reply/ID>` | Block a user from using the bot | Sudo |
| `/unblacklist <reply/ID>` | Unblock a user | Sudo |
| `/ac` or `/activevc` | List active voice chats | Sudo |
| `/logs` | Get bot log file | Sudo |
| `/logger` | Toggle logging on/off | Sudo |
| `/restart` | Restart the bot | Sudo |

### 🔧 Utility Commands

| Command | Description |
|---------|-------------|
| `/start` | Start bot / show welcome |
| `/help` | Show help menu (PM only) |
| `/ping` or `/alive` | Check bot latency |
| `/stats` | Show bot statistics |
| `/eval` or `/exec` | Execute Python code (Owner only) |

---

## 7. Useful Commands

### Start Bot

```bash
cd ~/AnonXMusic
screen -S anonxmusic
bash start
# Detach: Ctrl+A then D
```

### Stop Bot

```bash
screen -r anonxmusic
# Press Ctrl+C to stop
# Then type: exit
```

### View Logs

```bash
# Live bot logs
tail -f ~/AnonXMusic/log.txt

# Or using screen
screen -r anonxmusic

# Cobalt logs
sudo docker compose -f docker/cobalt-compose.yml logs -f
```

### Restart Bot

```bash
screen -r anonxmusic
# Press Ctrl+C to stop
bash start
# Detach: Ctrl+A then D
```

### Check Cobalt Status

```bash
# Container status
sudo docker ps | grep cobalt

# Test API
curl -s -X POST http://127.0.0.1:9000/api/json \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"url":"https://youtu.be/dQw4w9WgXcQ","isAudioOnly":true}' | python3 -m json.tool
```

---

## 8. Troubleshooting

### Cobalt Not Working

| Symptom | Solution |
|---------|----------|
| `Cobalt API is not running` error | Run `sudo docker compose -f docker/cobalt-compose.yml up -d` |
| Container exits immediately | Check logs: `sudo docker compose -f docker/cobalt-compose.yml logs` |
| Port 9000 already in use | `sudo lsof -i :9000` then kill the process |
| `iptables` error on RHEL 10 | Apply the Docker daemon fix (see Section 4) |
| Cobalt returns `error` status | Update Cobalt image: `sudo docker compose -f docker/cobalt-compose.yml pull && sudo docker compose -f docker/cobalt-compose.yml up -d` |

### Bot Not Starting

| Symptom | Solution |
|---------|----------|
| `Missing required environment variables` | Check `.env` — all 7 required vars must be set |
| `ModuleNotFoundError` | Run `pip3 install -U -r requirements.txt` |
| `Connection refused` (MongoDB) | Verify `MONGO_URL` and whitelist your server IP in Atlas |
| `401 Unauthorized` (Telegram) | Regenerate `BOT_TOKEN` from BotFather or `SESSION` from StringFatherBot |
| `ffmpeg not found` | Install ffmpeg: `sudo dnf install ffmpeg` (RHEL) or `sudo apt install ffmpeg` (Ubuntu) |

### Stream Not Playing

| Symptom | Solution |
|---------|----------|
| Bot joins VC but no audio | Check ffmpeg is installed: `ffmpeg -version` |
| `/play <text>` returns "Not found" | JioSaavn API may be down — try with a URL instead |
| `/play <URL>` fails | Test Cobalt manually (see Section 4). Restart if needed |
| Audio stuttering/buffering | Check server bandwidth. Cobalt streams are 320kbps |
| Video not playing | Ensure `VIDEO_PLAY=True` in `.env` |

---

> **AnonXMusic v4.0.0** — Cookie-Less Hybrid Router  
> No yt-dlp • No cookies • No downloads • Pure streaming
