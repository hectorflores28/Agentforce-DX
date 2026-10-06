# Update your package list
sudo apt update

# Install the official Docker engine and compose plugin
sudo apt install -y docker.io docker-buildx docker-compose-v2

# Add your user to the docker group to avoid using 'sudo' every time
sudo usermod -aG docker $USER
