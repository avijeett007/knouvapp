#!/usr/bin/env bash
set -e

echo "🚀 Starting Ultravox server setup..."

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
# Install NVIDIA drivers + CUDA
#############################################

echo "🖥️ Installing NVIDIA drivers and CUDA..."

distribution=$(. /etc/os-release;echo $ID$VERSION_ID) 
curl -fsSL https://developer.download.nvidia.com/compute/cuda/repos/${distribution}/x86_64/cuda-${distribution}.pin | sudo tee /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/repos/${distribution}/x86_64/cuda-repo-${distribution}_12.3.2-1_amd64.deb
sudo dpkg -i cuda-repo-${distribution}_12.3.2-1_amd64.deb
sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/${distribution}/x86_64/3bf863cc.pub
sudo apt-get update
sudo apt-get -y install cuda

# Add CUDA to PATH
echo 'export PATH=/usr/local/cuda/bin:${PATH}' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:${LD_LIBRARY_PATH}' >> ~/.bashrc

source ~/.bashrc

#############################################
# Install Docker
#############################################

echo "🐳 Installing Docker..."

sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common

# Add Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repo
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

#############################################
# Install NVIDIA Container Toolkit
#############################################

echo "🔌 Installing NVIDIA Container Toolkit..."

distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | \
    sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sed 's#deb #deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] #' | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Configure Docker to use NVIDIA runtime
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

#############################################
# Test NVIDIA Docker
#############################################

echo "🧪 Testing nvidia-smi in Docker..."
sudo docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

#############################################
# Build Docker image
#############################################

echo "🛠️ Building Docker image..."

sudo docker build -t ultravox-app .

echo "✅ Ultravox server setup complete!"

echo ""
echo "✅ NEXT STEPS:"
echo ""
echo "1. Run your container:"
echo ""
echo "   sudo docker run --rm --gpus all --env-file .env -p 8765:8765 ultravox-app"
echo ""
echo "2. Check health endpoint:"
echo ""
echo "   curl http://localhost:8765/health"
echo ""
echo "🎉 Done!"
