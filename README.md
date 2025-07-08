# 🎤 Knouvapp - Self-Hosted Voice AI Agent Platform

<div align="center">
  <img src="knouvapp-icon.svg" alt="Knouvapp Logo" width="120" height="120">
  
  **A cutting-edge self-hosted Voice AI Agent platform powered by Ultravox and Cartesia**
  
  [![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
  [![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://www.python.org/)
  [![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
  
  *Made with ❤️ by [Kno2gether](https://www.youtube.com/@kno2gether)*
</div>

## 🚀 What is Knouvapp?

Knouvapp is a sophisticated **self-hosted** Voice AI Agent platform that seamlessly integrates **Ultravox** (Speech-to-Text), **Cartesia** (Text-to-Speech), and **Daily.co** (Real-time Communication) to create intelligent voice conversations. Built with FastAPI and designed for scalability, it enables you to run your own real-time voice AI agents on your infrastructure with complete control and privacy.

## ✨ Key Features

- 🎯 **Real-time Voice Processing**: Powered by Ultravox v0.5 with Llama 3.1-8B model
- 🔊 **High-Quality TTS**: Cartesia's advanced text-to-speech synthesis
- 📞 **Live Communication**: Daily.co integration for seamless voice calls
- 🛡️ **Voice Activity Detection**: Silero VAD for intelligent conversation flow
- ⚡ **Pipeline Architecture**: Modular and extensible processing pipeline
- 🐳 **Docker Ready**: Containerized deployment for easy scaling
- 🔧 **Environment Optimized**: Pre-configured for optimal performance

---

## 🚀 **Scale Your Voice AI Business**

> **Building a Voice Agent is one thing, but selling the agent under your own brand is a different challenge.**

If you want to take this to the next level and start selling Voice AI Agents whether self-hosted or from another provider like VAPI, Retell, or Ultravox, check out **[Knotie AI Pro](https://knotie-ai.pro)**.

### 🎯 **Made for agencies to scale up the Voice AI Business**
Knotie AI Pro provides the tools and infrastructure you need to commercialize and scale your voice AI solutions.

---

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Daily.co      │    │   Ultravox      │    │   Cartesia      │
│   Transport     │───▶│   STT Service   │───▶│   TTS Service   │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                                                      │
         │                                                      │
         └──────────────────────────────────────────────────────┘
                              Pipeline Flow
```

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- Docker (optional)
- CUDA-compatible GPU (recommended for Ultravox)

### Environment Variables

Create a `.env` file in the root directory:

```env
# Required API Keys
HF_TOKEN=your_huggingface_token
DAILY_TOKEN=your_daily_co_token
CARTESIA_API_KEY=your_cartesia_api_key

# Optional Ultravox Optimization (recommended)
VLLM_MAX_MODEL_LEN=2048
VLLM_MAX_NUM_SEQS=1
VLLM_GPU_MEMORY_UTILIZATION=0.5
VLLM_DISABLE_CUSTOM_ALL_REDUCE=true
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:16
```

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd knouvapp
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment**
   ```bash
   chmod +x setup-knouv.sh
   ./setup-knouv.sh
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

### Docker Deployment

```bash
docker build -t ultravox-app .
docker run --rm -it --gpus all -p 8765:8765 --env-file .env ultravox-app
```

## 💰 Affordable GPU Resources

Looking for a cheap provider to rent your GPU VM for running Ultravox and other AI models? **[Massed Compute](https://vm.massedcompute.com/signup?referral=dbESKKG8Ju)** is undoubtedly the cheapest option you can get in the market today.

**Get 50% OFF on your next GPU Rented VM:**
- **Affiliate Link**: [https://vm.massedcompute.com/signup?referral=dbESKKG8Ju](https://vm.massedcompute.com/signup?referral=dbESKKG8Ju)
- **Discount Code**: `KNO2GETHERLABS` (50% OFF)

Perfect for self-hosting your Voice AI agents with powerful GPU acceleration at an affordable price.

## 🎮 Usage

### API Endpoints

#### Health Check
```bash
GET /health
```

#### Create Room
```bash
POST /create-room
```
Creates a new Daily.co room with a 5-minute expiration and returns room details with access token.

#### Run Pipeline
```bash
POST /run
Content-Type: application/json

{
  "room_url": "https://your-domain.daily.co/room-name",
  "token": "your-daily-token",
  "bot_name": "YourAIAgent"
}
```

### Example Usage

```python
import requests

# Create a room
response = requests.post("http://localhost:8000/create-room")
room_data = response.json()

# Start the voice AI agent
payload = {
    "room_url": room_data["url"],
    "token": room_data["token"],
    "bot_name": "VoiceAssistant"
}
requests.post("http://localhost:8000/run", json=payload)
```

## 🎯 Features in Detail

### Voice Processing Pipeline
- **Audio Input**: Captures voice through Daily.co transport
- **VAD**: Silero Voice Activity Detection with 0.2s stop detection
- **STT**: Ultravox processes speech to text with 150 token limit
- **TTS**: Cartesia converts responses to natural speech
- **Audio Output**: Delivers response through Daily.co

### Performance Optimizations
- GPU memory utilization capped at 50%
- Custom CUDA memory allocation for stability
- Eager execution for faster inference
- Interrupt handling for natural conversations

## 🔧 Configuration

### Ultravox Settings
- **Model**: `fixie-ai/ultravox-v0_5-llama-3_1-8b`
- **Max Tokens**: 150
- **Execution Mode**: Eager (for faster response)

### Cartesia Voice
- **Voice ID**: `97f4b8fb-f2fe-444b-bb9a-c109783a857a`
- **Quality**: High-fidelity neural voice synthesis

### Daily.co Integration
- **Room Expiration**: 5 minutes
- **Auto-eject**: Enabled
- **VAD**: Enabled with audio passthrough

## 📊 Monitoring

The application includes:
- Health check endpoint for monitoring
- Structured logging with Loguru
- Pipeline metrics collection
- Error handling and reporting

## 🤝 Contributing

We welcome contributions! Please feel free to submit issues, feature requests, or pull requests.

## 🎥 Learn More

**Subscribe to [Kno2gether](https://www.youtube.com/@kno2gether) on YouTube** for tutorials, updates, and voice AI content!

## 💬 Support & Self-Hosting

Want to self-host Ultravox on your own infrastructure and run your own Voice AI Agent? 

**Contact us at:** support@kno2gether.com

We provide:
- Custom deployment solutions
- Infrastructure setup assistance
- Performance optimization
- Technical support

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Ultravox](https://github.com/fixie-ai/ultravox) - Advanced speech-to-text processing
- [Cartesia](https://cartesia.ai/) - High-quality text-to-speech synthesis
- [Daily.co](https://daily.co/) - Real-time communication platform
- [Pipecat](https://github.com/pipecat-ai/pipecat) - Pipeline framework

---

<div align="center">
  <strong>Made with ❤️ by <a href="https://www.youtube.com/@kno2gether">Kno2gether</a></strong>
  <br>
  <em>Don't forget to subscribe to our YouTube channel!</em>
</div> 
