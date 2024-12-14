#!/bin/bash

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "Performing initial setup..."
    
    # Update and upgrade the system
    sudo apt update && sudo apt upgrade -y

    # Install essential tools and libraries
    sudo apt install -y apt-transport-https ca-certificates curl software-properties-common \
        git vim nano tmux neofetch htop tree unzip wget \
        build-essential python3 python3-pip nodejs npm 

    # Install Docker
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg.tmp
    sudo mv -f /usr/share/keyrings/docker-archive-keyring.gpg.tmp /usr/share/keyrings/docker-archive-keyring.gpg

    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    sudo apt update 
    sudo apt install -y docker-ce docker-ce-cli containerd.io

    # Add user to docker group
    sudo usermod -aG docker $USER

    # Install Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose

    # Install cloudflared
    sudo mkdir -p --mode=0755 /usr/share/keyrings
    curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null

    echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflared.list

    sudo apt-get update && sudo apt-get install cloudflared

    # Setup a basic .tmux.conf file
    echo "set -g mouse on" > ~/.tmux.conf
    echo "set -g history-limit 10000" >> ~/.tmux.conf

    # Verify installations
    echo "Docker version:"
    docker --version
    echo "Docker Compose version:"
    docker-compose --version
    echo "Python version:"
    python3 --version
    echo "cloudflared version:"
    cloudflared --version

    # Run neofetch to display system info
    neofetch

    echo "Setup complete! Please log out and log back in for all changes to take effect."
else
    echo "Initial setup already done (cloudflared is installed), skipping..."
fi

# Rest of your script continues here...
rm -rf ./cloudflared_8989.log

# Function to start a cloudflared tunnel and extract the URL
start_tunnel() {
    local port=$1
    local log_file="cloudflared_${port}.log"
    cloudflared tunnel --url http://localhost:$port > $log_file 2>&1 &
    local pid=$!
    
    # Wait for the URL to appear in the log file (timeout after 30 seconds)
    local timeout=30
    local url=""
    while [ $timeout -gt 0 ] && [ -z "$url" ]; do
        url=$(grep -o 'https://.*\.trycloudflare.com' $log_file)
        if [ -z "$url" ]; then
            sleep 1
            ((timeout--))
        fi
    done

    if [ -n "$url" ]; then
        echo "$url:$pid"
    else
        echo "Failed to get URL:$pid"
    fi
}

# Stop specific Docker containers
echo "Stopping Docker containers..."
docker stop prompt-store

# Remove specific Docker containers
echo "Removing Docker containers..."
docker rm prompt-store

# Remove associated Docker images
echo "Removing Docker images..."
docker rmi -f prompt-store

# Remove unused Docker volumes
echo "Removing unused Docker volumes..."
docker volume prune -f

# Remove unused Docker networks
echo "Removing unused Docker networks..."
docker network prune -f

# Prune unused Docker resources
echo "Pruning unused Docker resources..."
docker system prune -a -f --volumes

# docker network create self-host

# Build and start the containers
docker compose up --build -d

# Print the status of the running containers
docker compose ps

# Start backend tunnel
echo "Starting backend tunnel..."
backend_result=$(start_tunnel 8989)
backend_pid=$(echo $backend_result | cut -d':' -f2)

echo "Backend cloudflared : $backend_pid"