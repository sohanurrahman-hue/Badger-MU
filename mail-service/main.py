# main.py
import os
import time
import json
import secrets
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from pydantic import BaseModel, EmailStr
import redis.asyncio as aioredis
from dotenv import load_dotenv
from mailgun.client import Client


load_dotenv()

# ---------------------------
# Config (from environment)
# ---------------------------
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
# Mail provider config (worker will use these)
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN", "")
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@manhattan.edu")
EMAIL_QUEUE_KEY = os.getenv("EMAIL_QUEUE_KEY", "email_queue")

# ---------------------------
# FastAPI app + CORS
# ---------------------------
from starlette.middleware.cors import CORSMiddleware

app = FastAPI(title="Email Verification API",
                description="API for sending and verifying email codes with rate-limiting and protections.",
                version="1.0.0"
              )

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS", "GET"],
    allow_headers=["*"],
)

# ---------------------------
# Redis client
# ---------------------------
redis_client: Optional[aioredis.Redis] = None

@app.on_event("startup")
async def startup_event():
    global redis_client
    redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)

@app.on_event("shutdown")
async def shutdown_event():
    global redis_client
    if redis_client:
        await redis_client.close()
        await redis_client.connection_pool.disconnect()

# ---------------------------
# Utility functions
# ---------------------------
key: str = os.environ["MAILGUN_API_KEY"]
client: Client = Client(auth=("api", key))
domain = os.getenv("MAILGUN_DOMAIN", "")

import os
from pathlib import Path
from mailgun.client import Client

key: str = os.environ["MAILGUN_API_KEY"]
client: Client = Client(auth=("api", key))
domain = os.getenv("MAILGUN_DOMAIN", "")


@app.post("/send_certificate")
async def send_certificate(
    email: EmailStr = Form(...), 
    subject: str = Form('Your Certificate'),
    body: str = Form('Please find your certificate attached.'),
    file: UploadFile = File(None)
    ):

    """
    Endpoint to send a certificate via email.
    
    Args:
        email (EmailStr): Recipient email address.
        subject (str): Subject of the email.
        body (str): Body of the email.
        file (UploadFile): Certificate file to attach.
    """
    data = {
        'from': FROM_EMAIL,
        "to": email,
        "subject": subject,
        "text": body,    
    }
    
    files = []

    if file:
        files.append(("attachment", (file.filename, await file.read(), file.content_type)))

    try:
        response = client.messages.create(data=data, domain=domain, files=files)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending email: {str(e)}")

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to send email.")
    
    
    return {"message": f"Certificate sent successfully.{response}"}




