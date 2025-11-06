import os, json, time, io, base64
import redis
from mailgun.client import Client
from dotenv import load_dotenv
from typing import Any, Dict


load_dotenv()

REDIS_URL        = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
EMAIL_QUEUE_KEY  = os.getenv("EMAIL_QUEUE_KEY", "queue:email")
MAILGUN_DOMAIN   = os.getenv("MAILGUN_DOMAIN", "")
MAILGUN_API_KEY  = os.getenv("MAILGUN_API_KEY", "")


redis_client = redis.from_url(REDIS_URL, decode_responses=True)


Client = Client(auth=("api", MAILGUN_API_KEY))
domain = MAILGUN_DOMAIN


def get_all_files(job: Dict[str, Any]) -> list:
    files = []
    attachments = job.get("attachments", [])
    for attachment in job.get("attachments", []):
        filename = attachment.get("filename")
        content_b64 = attachment.get("content")
        if filename and content_b64:
            content_bytes = base64.b64decode(content_b64)
            file_obj = io.BytesIO(content_bytes)
            file_obj.name = filename
            files.append(("attachment", (filename, file_obj)))
    return files


def main():
    while True:
        item = redis_client.blpop(EMAIL_QUEUE_KEY, timeout=5)
        if not item:
            continue
        _, payload = item
        try:
            job = json.loads(payload)
        except Exception as e:
            print(f"Failed to parse job payload: {e}")
            continue



