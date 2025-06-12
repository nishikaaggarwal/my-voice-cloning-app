# my-voice-cloning-app
this project includes a voice cloning app that clones user's voice and translate text into speech 
 🗣️ Voice Cloning & Text-to-Speech Web Tool

This project uses the [Fish Speech API](https://fish.audio) for **free voice cloning**, supports **translation**, and stores generated audio in **Google Cloud Storage** with temporary access links.

---

## ⚙️ Features

- Clone voice from a short 10-second sample
- Convert text to speech using the cloned voice
- Optional text translation via Google Translate API
- Upload generated audio to Google Cloud Storage
- Generate signed public URLs
- Deletes temporary local files automatically

---

## 🔧 Requirements

- Python 3.10 or later
- Google Cloud project with GCS bucket
- Fish Speech API key (free to start)

Install dependencies:

```bash
pip install -r requirements.txt
