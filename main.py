import os
import sys
import time
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

# Check for maintenance mode
MAINTENANCE_MODE = os.getenv("MAINTENANCE_MODE", "false").lower() == "true"

if MAINTENANCE_MODE:
    print("🛠️ Container started in MAINTENANCE_MODE.")
    print("Sleeping indefinitely for debugging...")
    while True:
        time.sleep(3600)
    sys.exit(0)

# Try imports from pipecat
try:
    from pipecat.audio.vad.silero import SileroVADAnalyzer
    from pipecat.services.ultravox.stt import UltravoxSTTService
    from pipecat.services.cartesia.tts import CartesiaTTSService
    from pipecat.transports.services.daily import DailyParams, DailyTransport
    from pipecat.pipeline.pipeline import Pipeline
    from pipecat.pipeline.runner import PipelineRunner
    from pipecat.pipeline.task import PipelineTask, PipelineParams
except ImportError as e:
    logger.warning(f"Could not import some pipecat modules: {e}")
    UltravoxSTTService = None
    CartesiaTTSService = None
    DailyParams = None
    DailyTransport = None
    Pipeline = None
    PipelineRunner = None
    PipelineTask = None
    PipelineParams = None
    SileroVADAnalyzer = None

# Load secrets from environment
DAILY_TOKEN = os.environ.get("DAILY_TOKEN", "")
CARTESIA_API_KEY = os.environ.get("CARTESIA_API_KEY", "")
HF_TOKEN = os.environ.get("HF_TOKEN", "")

# Initialize FastAPI app
app = FastAPI()

# Initialize services
ultravox_processor = None
cartesia_service = None

logger.info("Checking required environment variables...")

missing_envs = []
if not HF_TOKEN:
    missing_envs.append("HF_TOKEN")
if not CARTESIA_API_KEY:
    missing_envs.append("CARTESIA_API_KEY")

if missing_envs:
    logger.error(f"Missing required environment variables: {missing_envs}")
else:
    try:
        logger.info("Initializing UltravoxSTTService...")
        ultravox_processor = UltravoxSTTService(
            model_name="fixie-ai/ultravox-v0_5-llama-3_1-8b",
            hf_token=HF_TOKEN,
        )
        logger.info("UltravoxSTTService initialized successfully.")

        logger.info("Initializing CartesiaTTSService...")
        cartesia_service = CartesiaTTSService(
            api_key=CARTESIA_API_KEY,
            voice_id="97f4b8fb-f2fe-444b-bb9a-c109783a857a",
        )
        logger.info("CartesiaTTSService initialized successfully.")

    except Exception as e:
        logger.exception(f"Exception while initializing services: {e}")
        ultravox_processor = None
        cartesia_service = None

@app.get("/")
async def root():
    return {"message": "Ultravox Pipeline API is running."}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/create-room")
def create_room():
    import requests

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DAILY_TOKEN}",
    }
    data = {
        "properties": {
            "exp": int(time.time()) + 300,
            "eject_at_room_exp": True,
        }
    }

    r = requests.post("https://api.daily.co/v1/rooms/", headers=headers, json=data)
    logger.debug(f"Daily room creation response: {r.status_code} {r.text}")

    if r.status_code != 200:
        return {
            "message": "Error creating room",
            "status_code": r.status_code,
        }

    room = r.json()
    token_resp = create_token(room["name"])
    room["token"] = token_resp.get("token") if token_resp else None
    return room

def create_token(room_name: str):
    import requests

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
    r = requests.post("https://api.daily.co/v1/meeting-tokens", headers=headers, json=data)
    logger.debug(f"Daily token creation response: {r.status_code} {r.text}")
    return r.json() if r.status_code == 200 else None

@app.post("/run")
async def run_pipeline(req: Request):
    missing = []
    if not ultravox_processor:
        missing.append("ultravox_processor")
    if not cartesia_service:
        missing.append("cartesia_service")
    if not Pipeline:
        missing.append("Pipeline")

    if missing:
        logger.error(f"Cannot run pipeline. Missing components: {missing}")
        return {"error": f"Required services or pipeline components not initialized: {missing}"}

    payload = await req.json()
    room_url = payload.get("room_url")
    token = payload.get("token")

    if not room_url or not token:
        logger.error("Missing room_url or token in /run payload.")
        return {"error": "room_url and token are required."}

    logger.info(f"Starting pipeline for room: {room_url}")

    # Setup Daily transport with Silero VAD
    try:
        transport_params = DailyParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
            room_url=room_url,
            token=token,
        )
        transport = DailyTransport(transport_params)
        logger.info("DailyTransport initialized successfully.")

    except Exception as e:
        logger.exception(f"Error creating Daily transport: {e}")
        return {"error": f"Failed to initialize DailyTransport: {e}"}

    try:
        pipeline = Pipeline(
            [
                transport.input(),
                ultravox_processor,
                cartesia_service,
                transport.output(),
            ]
        )
        logger.info("Pipeline initialized successfully.")

        task = PipelineTask(
            pipeline,
            params=PipelineParams(
                enable_metrics=True,
                enable_usage_metrics=True,
            )
        )

        @transport.event_handler("on_client_connected")
        async def on_client_connected(transport, client):
            logger.info("Client connected.")

        @transport.event_handler("on_client_disconnected")
        async def on_client_disconnected(transport, client):
            logger.info("Client disconnected.")
            await task.cancel()

        runner = PipelineRunner(handle_sigint=False)
        logger.info("PipelineRunner created. Running pipeline task...")

        await runner.run(task)
        logger.info("Pipeline run finished.")

        return {"status": "Pipeline run completed."}

    except Exception as e:
        logger.exception(f"Error running pipeline: {e}")
        return {"error": f"Failed to run pipeline: {e}"}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8765,
        reload=False,
    )