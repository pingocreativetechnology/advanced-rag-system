# 🚀 Deployment Guide

This guide covers deploying the Advanced RAG Agent System in different environments.

## 📋 Deployment Options

### 1. Local Development (Recommended for Testing)
- ✅ Easy setup and debugging
- ✅ Full control over configuration
- ✅ No cloud costs
- ⚠️ Limited to single machine access

### 2. Cloud Deployment
- ✅ Scalable and accessible from anywhere
- ✅ Professional production environment
- ⚠️ Requires cloud infrastructure knowledge
- ⚠️ Ongoing costs

### 3. Docker Deployment
- ✅ Consistent across environments
- ✅ Easy scaling and management
- ⚠️ Requires Docker knowledge
- ⚠️ Additional complexity

## 🏠 Local Production Deployment

### Hardware Recommendations

**Minimum Requirements:**
- RAM: 8GB
- Storage: 20GB free space
- CPU: 4 cores
- Network: Stable internet for model downloads

**Recommended Configuration:**
- RAM: 16GB+
- Storage: 50GB+ SSD
- CPU: 8+ cores
- GPU: Optional (RTX 3060+ for faster inference)

### Setup for Production

1. **Clone and Setup:**
```bash
git clone [your-repo-url]
cd langchain-rag-system
chmod +x setup.sh
./setup.sh
```

2. **Production Configuration:**
```bash
# Edit .env for production
cp .env.example .env

# Key production settings:
DEVELOPMENT_MODE=false
FLASK_DEBUG=false
ENABLE_AUTH=true
USE_HTTPS=true
LOG_LEVEL=WARNING
```

3. **Security Hardening:**
```bash
# Generate secure secrets
FLASK_SECRET_KEY=$(openssl rand -hex 32)
OPENWEBUI_SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)

# Update .env with generated secrets
echo "FLASK_SECRET_KEY=$FLASK_SECRET_KEY" >> .env
echo "OPENWEBUI_SECRET_KEY=$OPENWEBUI_SECRET_KEY" >> .env
echo "JWT_SECRET=$JWT_SECRET" >> .env
```

4. **Start Production Services:**
```bash
./start_services.sh
```

### Process Management with systemd (Linux)

Create service files for automatic startup:

```bash
# Create service file
sudo nano /etc/systemd/system/rag-system.service
```

```ini
[Unit]
Description=Advanced RAG Agent System
After=network.target

[Service]
Type=forking
User=your-username
WorkingDirectory=/path/to/langchain-rag-system
ExecStart=/path/to/langchain-rag-system/start_services.sh
ExecStop=/path/to/langchain-rag-system/stop_services.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable rag-system
sudo systemctl start rag-system
sudo systemctl status rag-system
```

## ☁️ Cloud Deployment

### AWS Deployment

**Using EC2:**

1. **Launch EC2 Instance:**
```bash
# Recommended: Ubuntu 22.04 LTS
# Instance type: t3.large or larger
# Storage: 30GB+ EBS volume
```

2. **Security Group Configuration:**
```bash
# Inbound rules:
Port 22   (SSH)      - Your IP only
Port 8000 (Open WebUI) - Your IP range
Port 8090 (Advanced RAG) - Your IP range
Port 11434 (Ollama API) - Internal only
```

3. **Setup on EC2:**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip git -y

# Clone and setup
git clone [your-repo-url]
cd langchain-rag-system
./setup.sh
```

4. **Configure Domain (Optional):**
```bash
# Use Nginx as reverse proxy
sudo apt install nginx -y

# Create Nginx config
sudo nano /etc/nginx/sites-available/rag-system
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /advanced {
        proxy_pass http://127.0.0.1:8090;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Google Cloud Platform (GCP)

1. **Create Compute Engine Instance:**
```bash
gcloud compute instances create rag-system \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --machine-type=e2-standard-4 \
    --boot-disk-size=50GB \
    --tags=rag-system
```

2. **Configure Firewall:**
```bash
gcloud compute firewall-rules create allow-rag-system \
    --allow tcp:8000,tcp:8090 \
    --source-ranges=YOUR-IP-RANGE \
    --target-tags=rag-system
```

### Azure Deployment

1. **Create Virtual Machine:**
```bash
az vm create \
    --resource-group myResourceGroup \
    --name rag-system-vm \
    --image Ubuntu2204 \
    --size Standard_D2s_v3 \
    --generate-ssh-keys
```

2. **Open Ports:**
```bash
az vm open-port --port 8000 --resource-group myResourceGroup --name rag-system-vm
az vm open-port --port 8090 --resource-group myResourceGroup --name rag-system-vm
```

## 🐳 Docker Deployment

### Basic Docker Setup

1. **Create Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Copy requirements
COPY requirements-basic.txt openwebui-requirements.txt ./

# Install Python dependencies
RUN pip install -r openwebui-requirements.txt

# Copy application files
COPY . .

# Create directories
RUN mkdir -p doccydocs chroma_db logs backups data

# Expose ports
EXPOSE 8000 8090 11434

# Start script
CMD ["./start_services.sh"]
```

2. **Create docker-compose.yml:**
```yaml
version: '3.8'

services:
  rag-system:
    build: .
    ports:
      - "8000:8000"
      - "8090:8090"
      - "11434:11434"
    volumes:
      - ./doccydocs:/app/doccydocs
      - ./chroma_db:/app/chroma_db
      - ./logs:/app/logs
      - ollama_data:/root/.ollama
    environment:
      - DEVELOPMENT_MODE=false
      - LOG_LEVEL=INFO
    restart: unless-stopped

volumes:
  ollama_data:
```

3. **Deploy with Docker Compose:**
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🔒 Security Considerations

### Authentication Setup

1. **Enable Authentication:**
```bash
# In .env file
ENABLE_AUTH=true
JWT_SECRET=your-secure-jwt-secret
```

2. **HTTPS Configuration:**
```bash
# Generate SSL certificates (Let's Encrypt)
sudo apt install certbot -y
sudo certbot certonly --standalone -d your-domain.com

# Update .env
USE_HTTPS=true
SSL_CERT_PATH=/etc/letsencrypt/live/your-domain.com/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/your-domain.com/privkey.pem
```

3. **Firewall Configuration:**
```bash
# Ubuntu/Debian
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 8000/tcp
sudo ufw allow 8090/tcp

# Block Ollama API from external access
sudo ufw deny 11434/tcp
```

### Access Control

1. **Create User Management System:**
```python
# Add to app.py or create separate auth module
from werkzeug.security import generate_password_hash
import jwt

# Example user creation
users = {
    'admin': {
        'password': generate_password_hash('secure-password'),
        'role': 'admin'
    }
}
```

2. **API Key Protection:**
```bash
# In .env
API_KEY=your-secure-api-key

# Use in requests
curl -H "Authorization: Bearer your-secure-api-key" http://localhost:8090/api/chat
```

## 📊 Monitoring and Maintenance

### Log Management

1. **Log Rotation:**
```bash
# Create logrotate config
sudo nano /etc/logrotate.d/rag-system
```

```
/path/to/langchain-rag-system/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 your-username your-username
}
```

2. **Monitoring Script:**
```bash
#!/bin/bash
# monitor.sh - Simple monitoring script

LOG_FILE="/path/to/logs/monitor.log"

check_service() {
    if pgrep -f "$1" > /dev/null; then
        echo "$(date): $1 is running" >> $LOG_FILE
        return 0
    else
        echo "$(date): $1 is NOT running - restarting" >> $LOG_FILE
        return 1
    fi
}

# Check Ollama
if ! check_service "ollama serve"; then
    ollama serve > /dev/null 2>&1 &
fi

# Check web interfaces
if ! check_service "app.py"; then
    cd /path/to/langchain-rag-system
    python app.py > logs/advanced_rag.log 2>&1 &
fi

if ! check_service "open-webui"; then
    cd /path/to/langchain-rag-system
    source openwebui-env/bin/activate
    open-webui serve --port 8000 > logs/openwebui.log 2>&1 &
fi
```

3. **Setup Monitoring Cron:**
```bash
# Add to crontab
crontab -e

# Check every 5 minutes
*/5 * * * * /path/to/monitor.sh
```

### Backup Strategy

1. **Automated Backup Script:**
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup vector database
tar -czf $BACKUP_DIR/chroma_db_$DATE.tar.gz chroma_db/

# Backup documents
tar -czf $BACKUP_DIR/documents_$DATE.tar.gz doccydocs/

# Backup configuration
cp .env $BACKUP_DIR/env_$DATE.backup

# Cleanup old backups (keep 7 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.backup" -mtime +7 -delete
```

2. **Schedule Backups:**
```bash
# Daily backup at 2 AM
crontab -e
0 2 * * * /path/to/backup.sh
```

## 🔧 Performance Optimization

### Model Optimization

1. **Choose Right Model for Hardware:**
```bash
# Low RAM (8GB): Use smaller models
ollama pull llama3.2:1b

# Medium RAM (16GB): Balanced models  
ollama pull llama3.2:3b

# High RAM (32GB+): Full models
ollama pull llama3.1:8b-instruct-q4_K_M
```

2. **GPU Acceleration:**
```bash
# Check GPU availability
nvidia-smi

# Configure for GPU in .env
OLLAMA_GPU_LAYERS=35  # Adjust based on your GPU memory
```

### Database Optimization

1. **ChromaDB Performance:**
```python
# In .env
CHUNK_SIZE=500          # Smaller chunks for better retrieval
SIMILARITY_SEARCH_K=5   # More results for better context
```

2. **Regular Database Maintenance:**
```bash
# Optimize database
python -c "
import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
client.heartbeat()  # Check health
"
```

## 🆘 Troubleshooting Deployment

### Common Issues

**Service Won't Start:**
```bash
# Check logs
tail -f logs/*.log

# Check ports
netstat -tulpn | grep -E '8000|8090|11434'

# Restart services
./stop_services.sh
./start_services.sh
```

**High Memory Usage:**
```bash
# Monitor memory
htop
free -h

# Reduce model size or context window
# Edit .env: CONTEXT_WINDOW=4096
```

**Connection Issues:**
```bash
# Test connectivity
curl http://localhost:11434/api/version
curl http://localhost:8000
curl http://localhost:8090

# Check firewall
sudo ufw status
```

### Performance Issues

**Slow Response Times:**
1. Use smaller models for faster inference
2. Reduce context window size
3. Optimize vector database chunk size
4. Add more RAM or use GPU acceleration

**High CPU Usage:**
1. Limit concurrent requests in .env
2. Use process management tools
3. Consider horizontal scaling

## 📈 Scaling Considerations

### Horizontal Scaling

1. **Load Balancer Setup:**
```nginx
upstream rag_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    location / {
        proxy_pass http://rag_backend;
    }
}
```

2. **Database Replication:**
- Use shared storage for ChromaDB
- Consider PostgreSQL with pgvector for production
- Implement database clustering for high availability

### Vertical Scaling

1. **Resource Monitoring:**
```bash
# Monitor resource usage
iostat -x 1
vmstat 1
```

2. **Optimize Resource Allocation:**
```bash
# In .env
MAX_CONCURRENT_REQUESTS=10
MAX_MEMORY_USAGE_GB=16
```

This completes the deployment guide covering local, cloud, and Docker deployments with security, monitoring, and scaling considerations.