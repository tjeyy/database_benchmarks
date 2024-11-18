sudo apt-get update
sudo apt-get install --no-install-recommends -y \
    bison \
    flex \
    iputils-ping \
    iproute2 \
    libbz2-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    libxerces-c-dev \
    libzstd-dev \
    numactl \
    pkg-config \
    rsync \
    time \
    ca-certificates \
    curl

# Install docker for Umbra. Taken from: https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y
