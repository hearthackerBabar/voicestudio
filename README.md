# 🎙 Voice Studio

> **A polished Text-to-Speech tool for Termux (Android) — powered by edge-tts.**
> No API key. No login. No signup. Just type and listen.

---

## ✨ Features

- **Text to Speech** — Convert any text to natural-sounding speech
- **Multiple Languages** — English, Urdu, Hindi with male & female voices
- **Custom Filenames** — Save MP3 with your own filename
- **Auto Playback** — Plays the generated MP3 automatically in Termux
- **Generation History** — Track all generated files with metadata
- **File Search** — Search generated files by name
- **Storage Info** — View total files count and disk usage
- **Delete & Cleanup** — Delete individual or all generated files, clear history
- **Stop Audio** — Stop currently playing audio anytime
- **Beautiful UI** — Modern colorful terminal interface with rich tables and spinners
- **Error Handling** — Friendly messages for all edge cases

---

## 📂 Project Structure

```
Voice-Studio/
├── app.py              # Main application (single file)
├── requirements.txt    # Python dependencies
├── README.md           # This file
├── output/             # Generated MP3 files are saved here
├── history/            # history.json is stored here
└── assets/             # Reserved for future assets
```

---

## 🚀 Installation (Termux)

Open Termux and run these commands one by one:

```bash
# 1. Update Termux packages
pkg update && pkg upgrade -y

# 2. Install Python and required tools
pkg install python -y
pkg install termux-api -y
pkg install git -y

# 3. Clone the project
git clone https://github.com/hearthackerBabar/voicestudio
cd Voice-Studio

# 4. Install Python dependencies
pip install -r requirements.txt
```

> **Note:** Make sure `termux-api` is installed both as a Termux package **and** the
> [Termux:API app](https://f-droid.org/en/packages/com.termux.api/) from F-Droid for
> audio playback to work.

---

## ▶️ Usage

```bash
cd voicestudio
python app.py
```

You will see a beautiful startup banner and a numbered menu:

| Option | Feature                          |
|--------|----------------------------------|
| 1      | Generate Speech from Text        |
| 2      | Preview Available Voices         |
| 3      | View Generation History          |
| 4      | Search Generated Files           |
| 5      | Delete Old Generated Files       |
| 6      | Clear Full History               |
| 7      | Stop Currently Playing Audio     |
| 8      | Show Total Generated Files Count |
| 9      | Show Total Storage Used          |
| 0      | Exit Voice Studio                |

### Generating Speech

1. Select option **1** from the menu
2. Type or paste your text
3. Choose a language (English / Urdu / Hindi)
4. Choose a voice gender (Male / Female)
5. Enter a custom filename
6. Wait for the spinner to finish — your MP3 is saved and auto-played!

---

## 🗣 Default Voices

| Language | Gender | Voice ID             |
|----------|--------|----------------------|
| English  | Female | en-US-AriaNeural     |
| English  | Male   | en-US-GuyNeural      |
| Urdu     | Female | ur-PK-UzmaNeural     |
| Urdu     | Male   | ur-PK-AsadNeural     |
| Hindi    | Female | hi-IN-SwaraNeural    |
| Hindi    | Male   | hi-IN-MadhurNeural   |

---

## 📸 Screenshots

> _Add your screenshots here._

| Screenshot | Description |
|------------|-------------|
| ![Banner](assets/screenshot_banner.png) | Startup banner |
| ![Menu](assets/screenshot_menu.png) | Main menu |
| ![Generate](assets/screenshot_generate.png) | Generating speech |

---

## 🛠 Requirements

- **Termux** on Android
- **Python 3.8+**
- **Internet connection** (edge-tts uses Microsoft's online TTS)
- **termux-api** package + Termux:API app (for audio playback)

### Python Packages

- `edge-tts` — Microsoft Edge TTS engine (no API key needed)
- `rich` — Beautiful terminal formatting
- `colorama` — Cross-platform colored text

---

## ❓ Troubleshooting

| Problem | Solution |
|---------|----------|
| `No internet connection` error | Check your WiFi / mobile data |
| Audio doesn't play | Install `termux-api` package AND Termux:API app |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| Permission denied | Run `termux-setup-storage` first |

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!
Feel free to open an issue or submit a pull request.

---

<p align="center">
  Made with ❤️ for Termux users
</p>
