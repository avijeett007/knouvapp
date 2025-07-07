#!/usr/bin/env bash
set -e

echo "🚀 Starting idempotent Ultravox server setup with NVIDIA driver 575..."

#############################################
# Update packages
#############################################

echo "🔄 Updating apt..."
sudo apt-get update -y
sudo apt-get upgrade -y

#############################################
# Install essential tools
#############################################

echo "🔧 Installing essential tools..."

sudo apt-get install -y \
    build-essential \
    curl \
    wget \
    lsb-release \
    software-properties-common \
    ca-certificates \
    gnupg

#############################################
# NVIDIA Driver 575
#############################################

echo "🖥️ Checking for NVIDIA driver..."

if nvidia-smi > /dev/null 2>&1; then
    echo "✅ NVIDIA driver already installed:"
    nvidia-smi
else
    echo "🔧 Installing NVIDIA driver 575..."

    # Add NVIDIA repo GPG key if missing
    if [ ! -f /etc/apt/keyrings/cuda-archive-keyring.gpg ]; then
        sudo mkdir -p /etc/apt/keyrings
        curl -fsSL https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/3bf863cc.pub | \
            sudo gpg --dearmor -o /etc/apt/keyrings/cuda-archive-keyring.gpg
    else
        echo "✅ NVIDIA keyring already exists."
    fi

    # Add CUDA repo if missing
    if [ ! -f /etc/apt/sources.list.d/cuda.list ]; then
        echo "deb [signed-by=/etc/apt/keyrings/cuda-archive-keyring.gpg] \
https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/ /" | \
            sudo tee /etc/apt/sources.list.d/cuda.list
    else
        echo "✅ CUDA repo already configured."
    fi

    sudo apt-get update

    # Install driver
    sudo apt-get install -y nvidia-driver-575

    # Install CUDA toolkit (without overwriting driver)
    sudo apt-get install -y cuda-toolkit-12-3

    # Add CUDA to PATH if not already in .bashrc
    if ! grep -q "/usr/local/cuda/bin" ~/.bashrc; then
        echo 'export PATH=/usr/local/cuda/bin:${PATH}' >> ~/.bashrc
    fi

    if ! grep -q "/usr/local/cuda/lib64" ~/.bashrc; then
        echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:${LD_LIBRARY_PATH}' >> ~/.bashrc
    fi

    echo "🔄 Reloading .bashrc..."
    source ~/.bashrc

    echo "✅ NVIDIA driver and CUDA toolkit installed."
fi

#############################################
# Docker
#############################################

echo "🐳 Checking for Docker..."

if command -v docker > /dev/null 2>&1; then
    echo "✅ Docker already installed: $(docker --version)"
else
    echo "🔧 Installing Docker..."

    sudo apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        software-properties-common

    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
      https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
fi

#############################################
# NVIDIA Container Toolkit
#############################################

echo "🔌 Checking for NVIDIA Container Toolkit..."

if dpkg -l | grep -q nvidia-container-toolkit; then
    echo "✅ NVIDIA Container Toolkit already installed."
else
    echo "🔧 Installing NVIDIA Container Toolkit..."

    distribution="ubuntu22.04"

    curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | \
        sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

    curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
        sed 's#deb #deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] #' | \
        sudo tee /etc/apt/sources.list.d/nvidia-docker.list

    sudo apt-get update
    sudo apt-get install -y nvidia-container-toolkit

    sudo nvidia-ctk runtime configure --runtime=docker
    sudo systemctl restart docker
fi

#############################################
# Check NVIDIA driver
#############################################

echo "🧪 Checking nvidia-smi outside Docker..."

if nvidia-smi > /dev/null 2>&1; then
    nvidia-smi
else
    echo "❌ nvidia-smi still failing. Please reboot or check driver installation."
    exit 1
fi

#############################################
# Test NVIDIA Docker
#############################################

echo "🧪 Testing nvidia-smi in Docker..."

if sudo docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi; then
    echo "✅ NVIDIA runtime in Docker is working!"
else
    echo "❌ NVIDIA runtime failed in Docker. Check driver versions or restart Docker daemon."
    exit 1
fi

#############################################
# Build Ultravox Docker image
#############################################

echo "🛠️ Checking if Ultravox Docker image already exists..."

if sudo docker images | grep -q ultravox-app; then
    echo "✅ Docker image 'ultravox-app' already exists."
else
    echo "🔧 Building Docker image..."
    sudo docker build -t ultravox-app .
fi

echo "✅ Ultravox server setup complete!"

echo ""
echo "✅ NEXT STEPS:"
echo ""
echo "1. Create your .env file (if not already done):"
echo ""
echo "   cp .env.example .env"
echo "   nano .env"
echo ""
echo "2. Run your container:"
echo ""
echo "   sudo docker run --rm --gpus all --env-file .env -p 8765:8765 ultravox-app"
echo ""
echo "3. Test your health endpoint:"
echo ""
echo "   curl http://localhost:8765/health"
echo ""
echo "🎉 Done!"