# 🛠️ Setup Instructions

This guide will help you set up the Advanced RAG Agent System on any computer.

## 📋 Prerequisites

### System Requirements
- **Operating System**: macOS, Linux, or Windows 10/11
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 10GB free space (for models and dependencies)
- **Internet**: Required for initial setup and model downloads

### Software Requirements
- **Python**: 3.9+ (3.11+ recommended for Open WebUI)
- **Git**: For cloning repository
- **Terminal/Command Prompt**: Basic command line knowledge helpful

## 🚀 Automated Setup (Recommended)

### 1. Clone Repository
```bash
git clone [your-repo-url]
cd langchain-rag-system
```

### 2. Run Setup Script
```bash
# Make script executable (macOS/Linux)
chmod +x setup.sh

# Run setup
./setup.sh
```

The setup script will:
- ✅ Check Python version compatibility
- ✅ Install Ollama (if needed)
- ✅ Create Python virtual environments
- ✅ Install all dependencies  
- ✅ Download essential AI models
- ✅ Set up configuration files
- ✅ Test all components

### 3. Start Services
```bash
./start_services.sh
```

## 🔧 Manual Setup (Alternative)

If the automated setup doesn't work, follow these manual steps:

### Step 1: Install Ollama
**macOS:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
Download and install from: https://ollama.ai/download

### Step 2: Install Python Dependencies

**For Basic RAG Agent:**
```bash
python -m venv rag-env
source rag-env/bin/activate  # On Windows: rag-env\Scripts\activate
pip install -r requirements-basic.txt
```

**For Full System (including Open WebUI):**
```bash
python3.11 -m venv openwebui-env
source openwebui-env/bin/activate  # On Windows: openwebui-env\Scripts\activate
pip install -r openwebui-requirements.txt
```

### Step 3: Download AI Models
```bash
# Start Ollama service
ollama serve &

# Download models (choose based on your hardware)
ollama pull mistral:7b          # Recommended (4.4GB)
ollama pull llama3.2:3b        # Balanced option (2.0GB)  
ollama pull llama3.2:1b        # Fast option (1.3GB)

# Download embedding models for vector search
ollama pull nomic-embed-text   # Best for RAG (274MB)
ollama pull all-minilm         # Alternative embedding (45MB)
```

### Step 4: Set Up Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit configuration (optional)
nano .env  # or use your preferred editor
```

### Step 5: Test Installation
```bash
# Test basic RAG agent
python rag_agent.py

# Test smart RAG agent (with vector DB)
source openwebui-env/bin/activate
python smart_rag_agent.py

# Test web interfaces
python app.py &                      # Advanced interface (port 8090)
open-webui serve --port 8000 &      # Professional interface (port 8000)
```

## 🌐 Port Configuration

The system uses several ports by default:

| Service | Port | Purpose |
|---------|------|---------|
| Ollama API | 11434 | LLM backend service |
| Open WebUI | 8000 | Professional ChatGPT-like interface |
| Advanced RAG | 8090 | Custom management interface |

### Changing Ports
Edit `.env` file to customize ports:
```bash
OPENWEBUI_PORT=8000
ADVANCED_PORT=8090
OLLAMA_PORT=11434
```

## 📁 Directory Structure After Setup

```
langchain-rag-system/
├── openwebui-env/           # Python 3.11 environment for Open WebUI
├── rag-env/                 # Python 3.9+ environment for basic agents
├── chroma_db/               # Vector database storage
├── doccydocs/               # Your document storage
│   ├── secsys.pdf          # Example documents
│   └── unisys.pdf
├── .env                     # Your configuration
└── [all project files]
```

## 🔍 Verification Steps

### 1. Check Ollama Installation
```bash
ollama --version
ollama list  # Should show downloaded models
```

### 2. Check Python Environments
```bash
# Basic environment
source rag-env/bin/activate
python -c "import langchain; print('✅ LangChain installed')"

# Full environment  
source openwebui-env/bin/activate
python -c "import open_webui; print('✅ Open WebUI installed')"
```

### 3. Check Services
```bash
# Check if Ollama is running
curl http://localhost:11434/api/version

# Check if web interfaces are accessible
curl http://localhost:8000  # Open WebUI
curl http://localhost:8090  # Advanced RAG
```

## 🆘 Troubleshooting

### Common Issues

**Python Version Error:**
```bash
# Install Python 3.11 (required for Open WebUI)
# macOS with Homebrew:
brew install python@3.11

# Ubuntu/Debian:
sudo apt update && sudo apt install python3.11 python3.11-venv
```

**Ollama Connection Failed:**
```bash
# Start Ollama service
ollama serve

# Check if running
ps aux | grep ollama
```

**Port Already in Use:**
```bash
# Find and kill process using port
lsof -i :8000
kill -9 [PID]

# Or use different ports in .env file
```

**Model Download Failed:**
```bash
# Check internet connection
ping ollama.ai

# Try downloading models individually
ollama pull mistral:7b
```

**Permission Denied (macOS/Linux):**
```bash
# Make scripts executable
chmod +x setup.sh start_services.sh

# Fix ownership if needed
sudo chown -R $USER:$USER ./
```

### Hardware-Specific Setup

**Low RAM (8GB or less):**
- Use smaller models: `ollama pull llama3.2:1b`
- Reduce context size in `.env`: `CONTEXT_SIZE=4096`
- Close other applications

**No GPU:**
- CPU-only mode is default
- Consider using faster/smaller models
- Increase timeout values in configuration

**Windows Specific:**
- Use PowerShell as Administrator
- Replace `source` with environment activation scripts
- Use `python` instead of `python3`

## ✅ Success Indicators

You'll know setup was successful when:

1. ✅ Ollama service starts without errors
2. ✅ Models download and list properly: `ollama list`
3. ✅ Python environments activate without errors
4. ✅ Web interfaces load at http://localhost:8000 and http://localhost:8090
5. ✅ You can chat with the AI and get responses
6. ✅ Document uploads work through web interface
7. ✅ Vector database creates and stores embeddings

## 🔄 Next Steps

After successful setup:

1. **Add Your Documents**: Upload PDFs/text files via web interface or copy to `doccydocs/`
2. **Customize Models**: Switch between different AI models based on your needs
3. **Configure Settings**: Modify `.env` for your specific requirements
4. **Explore Features**: Try different interfaces and RAG modes
5. **Scale Up**: Consider adding more powerful models if hardware allows

## 📚 Additional Resources

- **Ollama Documentation**: https://ollama.ai/docs
- **Open WebUI GitHub**: https://github.com/open-webui/open-webui
- **LangChain Documentation**: https://docs.langchain.com/
- **ChromaDB Documentation**: https://docs.trychroma.com/

For more help, see [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) or open an issue on GitHub.