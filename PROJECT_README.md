# 🤖 Advanced RAG Agent System

A comprehensive Retrieval-Augmented Generation (RAG) system with multiple AI interfaces, vector database integration, and document management capabilities.

## 🚀 Features

### Multiple AI Interfaces
- **Open WebUI**: Professional ChatGPT-like interface on port 8000
- **Advanced RAG App**: Custom management interface on port 8090  
- **Smart RAG Agent**: Command-line interface with vector database

### Intelligence Levels
1. **Basic RAG**: Simple keyword matching
2. **Smart RAG**: Vector database with semantic search using ChromaDB
3. **Advanced RAG**: Multi-agent coordination and context management

### Supported Models
- **Mistral 7B**: Primary reasoning model
- **Llama 3.2 (1B/3B)**: Fast lightweight options
- **Llama 3.1 8B**: Advanced reasoning (optional)
- **Embedding Models**: nomic-embed-text, all-minilm

### Document Processing
- PDF and TXT file support
- Automatic document chunking
- Semantic similarity search
- Source attribution
- File upload/management interface

## 📋 Prerequisites

- Python 3.11+ (required for Open WebUI)
- Python 3.9+ (minimum for basic functionality)
- [Ollama](https://ollama.ai) for local LLM serving
- 8GB+ RAM recommended
- 10GB+ disk space for models

## 🔧 Quick Start

### 1. Clone Repository
```bash
git clone [your-repo-url]
cd langchain-rag-system
```

### 2. Run Setup Script
```bash
chmod +x setup.sh
./setup.sh
```

### 3. Start Services
```bash
# Start all services
./start_services.sh

# Or start individually:
ollama serve &                    # AI backend
python app.py &                   # Advanced interface (port 8090)
open-webui serve --port 8000 &   # Professional interface (port 8000)
```

### 4. Access Interfaces
- **Open WebUI**: http://127.0.0.1:8000 (Recommended)
- **Advanced RAG**: http://127.0.0.1:8090
- **Command Line**: `python smart_rag_agent.py`

## 📁 Project Structure

```
langchain-rag-system/
├── PROJECT_README.md        # This file
├── SETUP.md                 # Detailed setup instructions
├── DEPLOYMENT.md            # Deployment guide
├── DEVELOPMENT.md           # Development history and context
├── setup.sh                # Automated setup script
├── start_services.sh       # Service startup script
├── requirements.txt         # Basic Python dependencies
├── requirements-full.txt    # Complete dependencies with versions
├── openwebui-requirements.txt # Open WebUI specific requirements
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore file
│
├── agents/                 # Core AI agents
│   ├── rag_agent.py       # Basic RAG agent
│   ├── enhanced_rag_agent.py # Enhanced multi-agent system
│   └── smart_rag_agent.py # Vector database RAG agent
│
├── interfaces/             # Web interfaces
│   ├── app.py             # Advanced management interface
│   ├── simple_agent.py    # Simple agent interface
│   └── chat_agent.py      # Basic chat interface
│
├── docs/                  # Documentation
│   ├── API.md            # API documentation
│   ├── MODELS.md         # Model information
│   └── TROUBLESHOOTING.md # Common issues and solutions
│
├── doccydocs/             # Document storage
│   ├── secsys.pdf        # Security system documentation
│   └── unisys.pdf        # Unisys documentation
│
├── chroma_db/             # Vector database storage
├── data/                  # Additional data files
└── scripts/               # Utility scripts
    ├── install_models.sh  # Download AI models
    └── backup_db.sh       # Backup vector database
```

## 🔄 Usage Examples

### Open WebUI (Recommended)
1. Open http://127.0.0.1:8000
2. Create account on first visit
3. Select model from dropdown (Mistral 7B recommended)
4. Start chatting with your documents

### Smart RAG Agent (Command Line)
```bash
source openwebui-env/bin/activate
python smart_rag_agent.py

> What are the main security concerns?
🤖 Based on your documents, the main security concerns include...

> quit
```

### Advanced Management Interface
1. Open http://127.0.0.1:8090
2. Upload documents via "File Management" tab
3. View statistics and technical details
4. Switch between Simple/Advanced modes

## 🔧 Configuration

### Environment Variables
Copy `.env.example` to `.env` and customize:
```bash
# Model Configuration
USE_ENHANCED_AGENT=true
DEFAULT_MODEL=mistral:7b
EMBEDDING_MODEL=nomic-embed-text

# Vector Database
CHROMA_PERSIST_DIRECTORY=./chroma_db
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Web Interface
OPENWEBUI_PORT=8000
ADVANCED_PORT=8090
```

### Adding Documents
1. **Via Web Interface**: Use upload buttons in any web interface
2. **Direct Copy**: Place files in `doccydocs/` folder
3. **Command Line**: Use `python smart_rag_agent.py` and call `add_document()`

## 🚀 Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions including:
- Docker deployment
- Cloud deployment (AWS, GCP, Azure)
- Production configurations
- SSL setup
- Reverse proxy configuration

## 🛠️ Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for:
- Development history
- Architecture decisions
- Extension points
- Contributing guidelines

## 📊 Performance

### Model Comparison
| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| Llama 3.2 1B | 1.3GB | ⚡⚡⚡ | ⭐⭐ | Quick responses |
| Llama 3.2 3B | 2.0GB | ⚡⚡ | ⭐⭐⭐ | Balanced |
| Mistral 7B | 4.4GB | ⚡ | ⭐⭐⭐⭐ | Best quality |
| Llama 3.1 8B | 4.9GB | ⚡ | ⭐⭐⭐⭐⭐ | Advanced reasoning |

### Hardware Requirements
- **Minimum**: 8GB RAM, 4 CPU cores
- **Recommended**: 16GB RAM, 8 CPU cores, SSD storage
- **Optimal**: 32GB RAM, GPU acceleration

## 🆘 Troubleshooting

### Common Issues
1. **"Connection refused"** → Start Ollama: `ollama serve`
2. **"Port already in use"** → Kill processes: `pkill -f app.py`
3. **"Model not found"** → Download models: `./scripts/install_models.sh`
4. **Slow responses** → Use faster model or reduce context size

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for detailed solutions.

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai) for local LLM serving
- [Open WebUI](https://github.com/open-webui/open-webui) for the professional interface
- [LangChain](https://langchain.com) for RAG framework
- [ChromaDB](https://www.trychroma.com) for vector database

---

**Built with ❤️ by pingomatic © 2025**

For questions or support, please open an issue on GitHub.