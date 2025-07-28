import os, time, mimetypes, requests
from google.cloud import storage, translate_v2 as translate
from dotenv import load_dotenv

load_dotenv()
API, MID, BUCKET = os.getenv("FISH_API_KEY"), os.getenv("MODEL_ID"), os.getenv("GCP_BUCKET_NAME")
if not API or not BUCKET: exit("Env missing")

t = int(time.time())
LFILE, GFILE = f'cloned_{t}.wav', f'voices/out_{t}.wav'

def create_model(path, txt):
    r = requests.post("https://api.fish.audio/api/v1/train",
                      headers={"Authorization": f"Bearer {API}"},
                      data={"title": f"M_{t}", "transcript": txt, "type": "voice_sample", "train_mode": "default"},
                      files={"audio": (os.path.basename(path), open(path, "rb"), mimetypes.guess_type(path)[0])})
    return r.json().get("model_id") if r.ok else None

def clone_voice(mid, txt):
    r = requests.post("https://api.fish.audio/api/v1/clone",
                      headers={"Authorization": f"Bearer {API}", "Content-Type": "application/json"},
                      json={"model_id": mid, "text": txt, "format": "wav"})
    if r.ok: open(LFILE, 'wb').write(r.content)
    else: exit("Clone fail")

def upload_gcs(bucket, src, dest):
    storage.Client().bucket(bucket).blob(dest).upload_from_filename(src)

def signed_url(bucket, blob, exp=3600):
    return storage.Client().bucket(bucket).blob(blob).generate_signed_url(expiration=exp)

txt = input("Text: ")
if input("Translate? (y/n): ").lower() == 'y':
    txt = translate.Client().translate(txt, target_language=input("Lang code: "))['translatedText']

if not MID:
    MID = create_model(input("WAV path: "), input("Transcript: "))
    if not MID: exit("Model fail")

clone_voice(MID, txt)
upload_gcs(BUCKET, LFILE, GFILE)
print("URL:", signed_url(BUCKET, GFILE))
os.remove(LFILE)
