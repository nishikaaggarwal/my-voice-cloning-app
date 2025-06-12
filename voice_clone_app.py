import os
import time
import mimetypes
import requests
from google.cloud import storage
from google.cloud import translate_v2 as translate
from dotenv import load_dotenv

# === LOAD ENV VARIABLES ===
load_dotenv()
FISH_API_KEY = os.getenv("FISH_API_KEY")
MODEL_ID = os.getenv("MODEL_ID")
GCP_BUCKET_NAME = os.getenv("GCP_BUCKET_NAME")

if not FISH_API_KEY or not GCP_BUCKET_NAME:
    print("❌ Environment variables missing. Please set FISH_API_KEY and GCP_BUCKET_NAME in your .env file.")
    exit()

# === DYNAMIC FILENAME USING TIMESTAMP ===
timestamp = int(time.time())
LOCAL_FILENAME = f'cloned_output_{timestamp}.wav'
GCP_DESTINATION_BLOB = f'cloned_voices/output_{timestamp}.wav'


# === FUNCTION: Create Fish Voice Model ===
def create_fish_model(audio_path, transcript):
    url = "https://api.fish.audio/api/v1/train"
    headers = {
        "Authorization": f"Bearer {FISH_API_KEY}",
    }
    data = {
        "title": f"Model_{timestamp}",
        "transcript": transcript,
        "type": "voice_sample",
        "train_mode": "default",
    }

    with open(audio_path, "rb") as f:
        files = {
            "audio": (os.path.basename(audio_path), f, mimetypes.guess_type(audio_path)[0]),
        }
        response = requests.post(url, headers=headers, data=data, files=files)

    if response.status_code == 200:
        print("✅ Voice model created successfully.")
        model_id = response.json().get("model_id")
        print(f"🧠 Model ID: {model_id}")
        return model_id
    else:
        print(f"❌ Failed to create voice model: {response.status_code}")
        print(response.text)
        return None


# === FUNCTION: Clone Voice with Fish ===
def clone_voice_with_fish(model_id, text):
    url = f"https://api.fish.audio/api/v1/clone"
    headers = {
        "Authorization": f"Bearer {FISH_API_KEY}",
        "Content-Type": "application/json"
    }
    json_data = {
        "model_id": model_id,
        "text": text,
        "format": "wav"
    }

    response = requests.post(url, headers=headers, json=json_data)
    if response.status_code == 200:
        with open(LOCAL_FILENAME, 'wb') as f:
            f.write(response.content)
        print(f"✅ Cloned audio saved as {LOCAL_FILENAME}")
    else:
        print(f"❌ Voice cloning failed: {response.status_code}")
        print(response.text)
        exit()


# === FUNCTION: Upload to Google Cloud Storage ===
def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name)
        print(f"✅ Uploaded to GCS: gs://{bucket_name}/{destination_blob_name}")
    except Exception as e:
        print(f"❌ GCS Upload failed: {e}")
        exit()


# === FUNCTION: Generate Signed URL ===
def get_signed_url(bucket_name, blob_name, expiration=3600):
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        url = blob.generate_signed_url(expiration=expiration)
        print(f"\n🔗 Public URL (valid for {expiration} seconds):\n{url}\n")
    except Exception as e:
        print(f"❌ Failed to generate signed URL: {e}")


# === STEP 1: Get user input ===
user_text = input("Enter the text you want to convert to speech: ")
print(f"User text received: {user_text}")

translate_choice = input("Do you want to translate this text? (yes/no): ").strip().lower()
if translate_choice == 'yes':
    target_lang = input("Enter target language code (e.g., 'hi' for Hindi): ").strip()
    translate_client = translate.Client()
    result = translate_client.translate(user_text, target_language=target_lang)
    print(f"✅ Translated text: {result['translatedText']}")
    user_text = result['translatedText']


# === STEP 2: Check or create voice model ===
if not MODEL_ID:
    print("🎤 Creating a new voice model.")
    audio_path = input("Enter path to a short WAV audio sample of your voice (10s): ").strip()
    transcript = input("Enter the exact transcript of the audio: ").strip()

    MODEL_ID = create_fish_model(audio_path, transcript)

    if not MODEL_ID:
        print("❌ Could not create a voice model. Exiting.")
        exit()


# === STEP 3: Clone voice ===
clone_voice_with_fish(MODEL_ID, user_text)

# === STEP 4: Upload cloned audio to GCS ===
upload_to_gcs(GCP_BUCKET_NAME, LOCAL_FILENAME, GCP_DESTINATION_BLOB)

# === STEP 5: Share public signed URL ===
get_signed_url(GCP_BUCKET_NAME, GCP_DESTINATION_BLOB)

# === STEP 6: Delete local file ===
if os.path.exists(LOCAL_FILENAME):
    os.remove(LOCAL_FILENAME)
    print(f"🧹 Deleted local file: {LOCAL_FILENAME}")
