# tera-dl

A minimal CLI downloader for Terabox files. Fetches direct links, supports resume, progress bars, retries, and proxy fallbacks.

## Features
- Resumable downloads with ETA/speed tracking.
- Auto-retries on timeouts (3x with backoff).
- Proxy option for stability.
- Colored, clean output with CLI tips.

## Setup
To authenticate with Terabox, you need the `ndus` cookie. Edit the script after getting it.

1. **Install Cookie Editor**:
   - Chrome: [Cookie-Editor Extension](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm)
   - Firefox: [Cookie-Editor Add-on](https://addons.mozilla.org/en-US/firefox/addon/cookie-editor/)
   - Install and restart your browser.

2. **Get `ndus` Cookie**:
   - Open [1024terabox.com](https://1024terabox.com) in your browser.
   - Log in if needed (for private shares).
   - Click the Cookie Editor icon → View all cookies → Find `ndus` → Copy its value (e.g., `YSj9BCeteHuiXfBtS...........`).

3. **Edit Script**:
   - Open `tera-dl.py`.
   - Find line {24} : `COOKIES = "ndus=YourValueHere"`
   - Replace with: `COOKIES = "ndus=YOUR_COPIED_VALUE"`
   - Save.

## Install
```bash
git clone https://github.com/eyeblech/tera-dl.git
cd tera-dl
pip install tqdm requests
```

## Usage
```bash
python tera-dl.py https://1024terabox.com/s/1ABC1.....
```
- Enter for direct download (default).
- `1` for proxy.

**Sample Output**:
```
Fetching direct download link...

══════════════════════════════════════════════════════════════════════
File Name: video.mp4 | Size: 310 MB | Fetched: 2030-12-14 10:30
──────────────────────────────────────────────────────────────────────
Direct: https://d.1024terabox.com/file/...? (copy-paste ready)
Proxy: https://terabox.ashlynn.workers.dev/proxy?...

CLI: aria2c --continue=true "direct-link" | wget -c -O "video.mp4" "direct-link"
══════════════════════════════════════════════════════════════════════

What next? 0 (Enter) - Direct | 1 - Proxy
Enter choice [0]: 
```

Download starts with progress bar; resumes if interrupted.

## Acknowledgments
Huge thanks to [@Itz-Ashlynn](https://github.com/Itz-Ashlynn) for [Terabox-Web](https://github.com/Itz-Ashlynn/Terabox-Web)—the API that makes this all possible. Star the repo if it helps! 🌟

## License
MIT—see [LICENSE](LICENSE).
