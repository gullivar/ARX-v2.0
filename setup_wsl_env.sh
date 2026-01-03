#!/bin/bash
set -e
export DEBIAN_FRONTEND=noninteractive

echo "[WSL] Updating APT..."
apt-get update

echo "[WSL] Installing Core Packages..."
apt-get install -y git python3 python3-pip python3-venv curl wget unzip openssh-server

echo "[WSL] Configuring SSH Server..."
# Backup config
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak
# Ensure password authentication is enabled (convenience for initial setup)
sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
# Start SSH Service
service ssh start
echo "SSH Server started on port 22."

echo "[WSL] Preparing Project Directory..."
BASE_DIR="/root/project"
mkdir -p "$BASE_DIR"
cd "$BASE_DIR"

if [ -d "ARX-v2.0" ]; then
    echo "Updating Repo..."
    cd ARX-v2.0
    git pull origin main
else
    echo "Cloning Repo..."
    git clone https://github.com/gullivar/ARX-v2.0.git
    cd ARX-v2.0
fi

echo "[WSL] Restoring Data from Windows Host (E:)..."
# Windows E:\MyProject\ARX is mounted at /mnt/e/MyProject/ARX
WIN_SRC="/mnt/e/MyProject/ARX"
BACKEND_DIR="/root/project/ARX-v2.0/backend"
DATA_DIR="$BACKEND_DIR/data"
mkdir -p "$DATA_DIR"

if [ -f "$WIN_SRC/w_intel.db" ]; then
    echo " -> Restoring w_intel.db"
    cp -f "$WIN_SRC/w_intel.db" "$BACKEND_DIR/"
fi

if [ -f "$WIN_SRC/.env" ]; then
    echo " -> Restoring .env"
    cp -f "$WIN_SRC/.env" "$BACKEND_DIR/"
fi

# Handle ChromaDB (Folder or Archive)
if [ -f "$WIN_SRC/chroma_db.tar.gz" ]; then
    echo " -> Restoring ChromaDB Archive..."
    tar -xzf "$WIN_SRC/chroma_db.tar.gz" -C "$DATA_DIR/"
elif [ -d "$WIN_SRC/chroma_db" ]; then
    echo " -> Restoring ChromaDB Folder..."
    cp -rf "$WIN_SRC/chroma_db" "$DATA_DIR/"
fi

# Also check for 'chroma' folder
if [ -d "$WIN_SRC/chroma" ]; then
    echo " -> Restoring Chroma Data..."
    cp -rf "$WIN_SRC/chroma" "$DATA_DIR/"
fi

echo "[WSL] Setting up Python Environment..."
cd "$BACKEND_DIR"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip setuptools wheel

if [ -f "requirements.txt" ]; then
    if grep -q "uvloop" requirements.txt; then
        echo "Removing uvloop from requirements..."
        sed -i '/uvloop/d' requirements.txt
    fi
    pip install -r requirements.txt
fi

echo "[WSL] Installing Playwright Browsers..."
pip install playwright
playwright install --with-deps chromium

echo "[WSL-SETUP-FINISHED] Success. Repository is at $BACKEND_DIR"
