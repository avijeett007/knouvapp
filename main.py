import os
import time
import requests
import asyncio

from fastapi import FastAPI, Request
from dotenv import load_dotenv
from pipecat import Task, PipelineRunner
from pipecat.services.ultravox import UltravoxSTTService
from pipecat.services.cartesia import CartesiaTTSService
from pipecat.transports.daily import DailyWebRTCAudioTransport
from loguru import logger

load_dotenv()

DAILY_TOKEN = os.environ.get("DAILY_TOKEN")
CARTESIA_API_KEY = os.environ.get("CARTESIA_API_KEY")
HF_TOKEN = os.environ.get("HF_TOKEN")

app = FastAPI()

# Initialize Ultravox service - loads on container startup
ultravox_service = UltravoxSTTService(
    hf_token=HF_TOKEN,
    model_id="ultravox/ultravox-8b-v1",
    gpu=True
)

# Initialize Cartesia TTS
cartesia_service = CartesiaTTSService(
    api_key=CARTESIA_API_KEY,
    voice="charlie"
)

@app.get("/")
async def root():
    return {"message": "Ultravox API running"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/create-room")
def create_room():
    url = "https://api.daily.co/v1/rooms/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DAILY_TOKEN}",
    }
    data = {
        "properties": {
            "exp": int(time.time()) + 60 * 5,
            "eject_at_room_exp": True,
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        room_info = response.json()
        token = create_token(room_info["name"])
        if token and "token" in token:
            room_info["token"] = token["token"]
        else:
            print("Failed to create token")
            return {
                "message": "There was an error creating your room",
                "status_code": 500,
            }
        return room_info
    else:
        data = response.json()
        if data.get("error") == "invalid-request-error" and "rooms reached" in data.get("info", ""):
            print("We are currently at capacity for this demo. Please try again later.")
            return {
                "message": "We are currently at capacity for this demo. Please try again later.",
                "status_code": 429,
            }
        print(f"Failed to create room: {response.status_code}")
        return {"message": "There was an error creating your room", "status_code": 500}

def create_token(room_name: str):
    url = "https://api.daily.co/v1/meeting-tokens"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DAILY_TOKEN}",
    }
    data = {
        "properties": {
            "room_name": room_name,
            "is_owner": True,
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to create token: {response.status_code}")
        return None

@app.post("/run")
async def run_pipeline(request: Request):
    payload = await request.json()
    room_url = payload["room_url"]
    token = payload["token"]

    # Create the audio transport for Daily
    audio_transport = DailyWebRTCAudioTransport(
        room_url=room_url,
        token=token,
        enable_metrics=True,
    )

    # Define a single task with Ultravox and Cartesia
    task = Task(
        audio_transport=audio_transport,
        stt_service=ultravox_service,
        tts_service=cartesia_service,
    )

    runner = PipelineRunner()
    logger.info("Starting pipeline...")

    # run() is a long-lived coroutine
    await runner.run(task)

    return {"status": "Pipeline started"}
