import os
import time
import requests

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.ultravox.stt import UltravoxSTTService
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask, PipelineParams
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.transports.services.daily import DailyParams, DailyTransport

# Load .env
load_dotenv(override=True)

# Recommended environment variables for Ultravox 8B:
os.environ.setdefault("VLLM_MAX_MODEL_LEN", "2048")
os.environ.setdefault("VLLM_MAX_NUM_SEQS", "1")
os.environ.setdefault("VLLM_GPU_MEMORY_UTILIZATION", "0.5")
os.environ.setdefault("VLLM_DISABLE_CUSTOM_ALL_REDUCE", "true")
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True,max_split_size_mb:16")

# Verify env vars
for var in ["HF_TOKEN", "DAILY_TOKEN", "CARTESIA_API_KEY"]:
    if not os.getenv(var):
        raise EnvironmentError(f"Environment variable {var} not set!")

app = FastAPI()

ultravox_processor = None
cartesia_service = None

try:
    logger.info("Initializing UltravoxSTTService...")

    ultravox_processor = UltravoxSTTService(
        model_name="fixie-ai/ultravox-v0_5-llama-3_1-8b",
        hf_token=os.getenv("HF_TOKEN"),
        enforce_eager=True,
        max_tokens=150,
    )

    logger.info("UltravoxSTTService initialized successfully.")

    logger.info("Initializing CartesiaTTSService...")
    cartesia_service = CartesiaTTSService(
        api_key=os.environ.get("CARTESIA_API_KEY"),
        voice_id="97f4b8fb-f2fe-444b-bb9a-c109783a857a",
    )
    logger.info("CartesiaTTSService initialized successfully.")

except Exception as e:
    logger.error(f"Exception while initializing services: {e}")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/create-room")
async def create_room():
    url = "https://api.daily.co/v1/rooms/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ.get('DAILY_TOKEN')}",
    }
    data = {
        "properties": {
            "exp": int(time.time()) + 60 * 5,
            "eject_at_room_exp": True,
        }
    }

    response = requests.post(url, headers=headers, json=data)
    logger.debug(f"Daily room creation response: {response.status_code} {response.text}")

    if response.status_code == 200:
        room_info = response.json()
        token_resp = create_token(room_info["name"])
        if token_resp and "token" in token_resp:
            room_info["token"] = token_resp["token"]
        else:
            return JSONResponse(status_code=500, content={"message": "Failed to create token"})
        return room_info
    else:
        return JSONResponse(status_code=500, content={"message": "Error creating room"})

def create_token(room_name):
    url = "https://api.daily.co/v1/meeting-tokens"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ.get('DAILY_TOKEN')}",
    }
    data = {
        "properties": {
            "room_name": room_name,
            "is_owner": True,
        }
    }

    response = requests.post(url, headers=headers, json=data)
    logger.debug(f"Daily token creation response: {response.status_code} {response.text}")
    return response.json() if response.status_code == 200 else None

@app.post("/run")
async def run_pipeline(request: Request):
    data = await request.json()
    room_url = data.get("room_url")
    token = data.get("token")
    bot_name = data.get("bot_name")

    if not (room_url and token and bot_name):
        return JSONResponse(
            status_code=400,
            content={"error": "Missing room_url, token, or bot_name in request payload."}
        )

    if not ultravox_processor or not cartesia_service:
        return JSONResponse(
            status_code=500,
            content={"error": "Required services or pipeline components not initialized."}
        )

    transport = DailyTransport(
        room_url,
        token,
        bot_name,
        DailyParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            transcription_enabled=False,
            vad_enabled=True,
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.2)),
            vad_audio_passthrough=True,
        )
    )

    pipeline = Pipeline([
        transport.input(),
        ultravox_processor,
        cartesia_service,
        transport.output(),
    ])

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,
            enable_metrics=True,
        ),
    )

    runner = PipelineRunner()

    try:
        logger.info("Starting pipeline runner...")
        await runner.run(task)
    except Exception as e:
        logger.exception(f"Pipeline error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

    return JSONResponse(content={"status": "pipeline completed"})
