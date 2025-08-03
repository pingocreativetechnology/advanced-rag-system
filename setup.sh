#!/bin/bash

# ===================================================================
# Advanced RAG Agent System - Automated Setup Script
# ===================================================================
# This script sets up the complete RAG system with all dependencies
# Usage: ./setup.sh
# ===================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Emojis for better UX
ROCKET="🚀"
CHECK="✅"
CROSS="❌"
WARNING="⚠️"
INFO="ℹ️"
GEAR="⚙️"
BRAIN="🧠"
FOLDER="📁"

echo -e "${CYAN}${ROCKET} Advanced RAG Agent System Setup${NC}"
echo -e "${CYAN}======================================${NC}"
echo ""

# Function to print colored output
print_status() {
    echo -e "${BLUE}${INFO} $1${NC}"
}

print_success() {
    echo -e "${GREEN}${CHECK} $1${NC}"
}

print_error() {
    echo -e "${RED}${CROSS} $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}${WARNING} $1${NC}"
}

print_section() {
    echo -e "\n${PURPLE}${GEAR} $1${NC}"
    echo -e "${PURPLE}$(printf '=%.0s' {1..50})${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check operating system
check_os() {
    print_section "Checking Operating System"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        print_success "Detected macOS"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        print_success "Detected Linux"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        OS="windows"
        print_success "Detected Windows (Git Bash/Cygwin)"
    else
        print_error "Unsupported operating system: $OSTYPE"
        exit 1
    fi
}

# Check Python version
check_python() {
    print_section "Checking Python Installation"
    
    # Check for Python 3.11+ (preferred for Open WebUI)
    if command_exists python3.11; then
        PYTHON311="python3.11"
        PYTHON311_VERSION=$($PYTHON311 --version 2>&1 | cut -d' ' -f2)
        print_success "Python 3.11 found: $PYTHON311_VERSION"
        HAS_PYTHON311=true
    else
        print_warning "Python 3.11 not found. Open WebUI features may be limited."
        HAS_PYTHON311=false
    fi
    
    # Check for Python 3.9+ (minimum requirement)
    if command_exists python3; then
        PYTHON3="python3"
        PYTHON3_VERSION=$($PYTHON3 --version 2>&1 | cut -d' ' -f2)
        PYTHON3_MAJOR=$(echo $PYTHON3_VERSION | cut -d'.' -f1)
        PYTHON3_MINOR=$(echo $PYTHON3_VERSION | cut -d'.' -f2)
        
        if [[ $PYTHON3_MAJOR -eq 3 && $PYTHON3_MINOR -ge 9 ]]; then
            print_success "Python 3 found: $PYTHON3_VERSION"
            HAS_PYTHON3=true
        else
            print_error "Python 3.9+ required, found: $PYTHON3_VERSION"
            exit 1
        fi
    elif command_exists python; then
        PYTHON3="python"
        PYTHON3_VERSION=$($PYTHON3 --version 2>&1 | cut -d' ' -f2)
        print_success "Python found: $PYTHON3_VERSION"
        HAS_PYTHON3=true
    else
        print_error "Python not found. Please install Python 3.9+ first."
        exit 1
    fi
}

# Install Ollama
install_ollama() {
    print_section "Installing Ollama"
    
    if command_exists ollama; then
        OLLAMA_VERSION=$(ollama --version 2>&1 | head -n1)
        print_success "Ollama already installed: $OLLAMA_VERSION"
        return
    fi
    
    print_status "Installing Ollama..."
    
    if [[ "$OS" == "macos" || "$OS" == "linux" ]]; then
        curl -fsSL https://ollama.ai/install.sh | sh
        if command_exists ollama; then
            print_success "Ollama installed successfully"
        else
            print_error "Ollama installation failed"
            exit 1
        fi
    else
        print_warning "Please install Ollama manually for Windows from: https://ollama.ai/download"
        print_status "Press Enter when Ollama is installed..."
        read
    fi
}

# Start Ollama service
start_ollama() {
    print_section "Starting Ollama Service"
    
    if pgrep -f "ollama serve" > /dev/null; then
        print_success "Ollama service already running"
        return
    fi
    
    print_status "Starting Ollama service..."
    ollama serve > /dev/null 2>&1 &
    
    # Wait for service to start
    sleep 3
    
    if curl -s http://localhost:11434/api/version > /dev/null; then
        print_success "Ollama service started successfully"
    else
        print_error "Failed to start Ollama service"
        exit 1
    fi
}

# Create Python environments
create_environments() {
    print_section "Creating Python Virtual Environments"
    
    # Basic RAG environment (Python 3.9+)
    if [[ ! -d "rag-env" ]]; then
        print_status "Creating basic RAG environment..."
        $PYTHON3 -m venv rag-env
        print_success "Basic RAG environment created"
    else
        print_success "Basic RAG environment already exists"
    fi
    
    # Open WebUI environment (Python 3.11+)
    if [[ "$HAS_PYTHON311" == true ]]; then
        if [[ ! -d "openwebui-env" ]]; then
            print_status "Creating Open WebUI environment..."
            $PYTHON311 -m venv openwebui-env
            print_success "Open WebUI environment created"
        else
            print_success "Open WebUI environment already exists"
        fi
    fi
}

# Install Python dependencies
install_dependencies() {
    print_section "Installing Python Dependencies"
    
    # Install basic RAG dependencies
    print_status "Installing basic RAG dependencies..."
    if [[ "$OS" == "windows" ]]; then
        source rag-env/Scripts/activate
    else
        source rag-env/bin/activate
    fi
    
    pip install --upgrade pip
    pip install -r requirements-basic.txt
    deactivate
    print_success "Basic RAG dependencies installed"
    
    # Install Open WebUI dependencies if Python 3.11 available
    if [[ "$HAS_PYTHON311" == true ]]; then
        print_status "Installing Open WebUI dependencies..."
        if [[ "$OS" == "windows" ]]; then
            source openwebui-env/Scripts/activate
        else
            source openwebui-env/bin/activate
        fi
        
        pip install --upgrade pip
        pip install -r openwebui-requirements.txt
        deactivate
        print_success "Open WebUI dependencies installed"
    fi
}

# Download AI models
download_models() {
    print_section "Downloading AI Models"
    
    print_status "Downloading essential models (this may take a while)..."
    
    # Download embedding models first (smaller)
    print_status "Downloading embedding models..."
    ollama pull nomic-embed-text
    print_success "Embedding model downloaded: nomic-embed-text"
    
    # Download primary LLM
    print_status "Downloading primary language model..."
    echo -e "${YELLOW}Choose your primary model based on your hardware:${NC}"
    echo "1) Llama 3.2 1B (1.3GB) - Fast, low memory"
    echo "2) Llama 3.2 3B (2.0GB) - Balanced performance"  
    echo "3) Mistral 7B (4.4GB) - Best quality (recommended)"
    echo "4) Skip model download (download manually later)"
    
    read -p "Enter choice (1-4) [default: 3]: " model_choice
    model_choice=${model_choice:-3}
    
    case $model_choice in
        1)
            ollama pull llama3.2:1b
            DEFAULT_MODEL="llama3.2:1b"
            print_success "Downloaded Llama 3.2 1B"
            ;;
        2)
            ollama pull llama3.2:3b
            DEFAULT_MODEL="llama3.2:3b"
            print_success "Downloaded Llama 3.2 3B"
            ;;
        3)
            ollama pull mistral:7b
            DEFAULT_MODEL="mistral:7b"
            print_success "Downloaded Mistral 7B"
            ;;
        4)
            print_warning "Skipping model download. You'll need to download models manually."
            DEFAULT_MODEL="mistral:7b"
            ;;
        *)
            print_warning "Invalid choice. Downloading Mistral 7B (default)"
            ollama pull mistral:7b
            DEFAULT_MODEL="mistral:7b"
            ;;
    esac
}

# Create configuration files
create_config() {
    print_section "Creating Configuration Files"
    
    # Create .env file if it doesn't exist
    if [[ ! -f ".env" ]]; then
        print_status "Creating .env configuration file..."
        cp .env.example .env
        
        # Update default model in .env
        if [[ -n "$DEFAULT_MODEL" ]]; then
            if [[ "$OS" == "macos" ]]; then
                sed -i '' "s/DEFAULT_MODEL=mistral:7b/DEFAULT_MODEL=$DEFAULT_MODEL/" .env
            else
                sed -i "s/DEFAULT_MODEL=mistral:7b/DEFAULT_MODEL=$DEFAULT_MODEL/" .env
            fi
        fi
        
        print_success ".env configuration created"
    else
        print_success ".env configuration already exists"
    fi
    
    # Create necessary directories
    print_status "Creating required directories..."
    
    directories=("doccydocs" "chroma_db" "logs" "backups" "data")
    for dir in "${directories[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            print_success "Created directory: $dir"
        fi
    done
}

# Create startup script
create_startup_script() {
    print_section "Creating Service Startup Script"
    
    cat > start_services.sh << 'EOF'
#!/bin/bash

# Advanced RAG Agent System - Service Startup Script
# This script starts all necessary services

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting Advanced RAG Agent System...${NC}"

# Start Ollama if not running
if ! pgrep -f "ollama serve" > /dev/null; then
    echo -e "${GREEN}✅ Starting Ollama service...${NC}"
    ollama serve > /dev/null 2>&1 &
    sleep 3
else
    echo -e "${GREEN}✅ Ollama service already running${NC}"
fi

# Start Advanced RAG interface (port 8090)
echo -e "${GREEN}✅ Starting Advanced RAG interface on port 8090...${NC}"
python app.py > logs/advanced_rag.log 2>&1 &

# Start Open WebUI if environment exists (port 8000)
if [ -d "openwebui-env" ]; then
    echo -e "${GREEN}✅ Starting Open WebUI on port 8000...${NC}"
    source openwebui-env/bin/activate
    open-webui serve --port 8000 > logs/openwebui.log 2>&1 &
    deactivate
fi

sleep 5

echo -e "${BLUE}🌐 Services started! Access via:${NC}"
echo -e "   📱 Open WebUI (Professional): http://127.0.0.1:8000"
echo -e "   🔧 Advanced RAG (Management): http://127.0.0.1:8090"
echo -e "   💻 Command Line: python smart_rag_agent.py"
echo ""
echo -e "${BLUE}📋 To stop services: ./stop_services.sh${NC}"
EOF

    chmod +x start_services.sh
    print_success "Startup script created: start_services.sh"
    
    # Create stop script too
    cat > stop_services.sh << 'EOF'
#!/bin/bash

# Stop all RAG system services

echo "🛑 Stopping Advanced RAG Agent System..."

# Kill web interfaces
pkill -f "app.py" 2>/dev/null || true
pkill -f "open-webui" 2>/dev/null || true

# Kill Ollama (optional - comment out if you want to keep it running)
# pkill -f "ollama serve" 2>/dev/null || true

echo "✅ Services stopped"
EOF

    chmod +x stop_services.sh
    print_success "Stop script created: stop_services.sh"
}

# Test installation
test_installation() {
    print_section "Testing Installation"
    
    # Test Ollama
    if curl -s http://localhost:11434/api/version > /dev/null; then
        print_success "Ollama API responding"
    else
        print_error "Ollama API not responding"
        return 1
    fi
    
    # Test Python environments
    if [[ "$OS" == "windows" ]]; then
        source rag-env/Scripts/activate
    else
        source rag-env/bin/activate
    fi
    
    if python -c "import langchain; print('✅ LangChain OK')" 2>/dev/null; then
        print_success "Basic RAG environment working"
    else
        print_error "Basic RAG environment has issues"
    fi
    deactivate
    
    # Test Open WebUI environment if available
    if [[ "$HAS_PYTHON311" == true ]]; then
        if [[ "$OS" == "windows" ]]; then
            source openwebui-env/Scripts/activate
        else
            source openwebui-env/bin/activate
        fi
        
        if python -c "import open_webui; print('✅ Open WebUI OK')" 2>/dev/null; then
            print_success "Open WebUI environment working"
        else
            print_warning "Open WebUI environment has issues"
        fi
        deactivate
    fi
}

# Final instructions
show_completion() {
    print_section "Setup Complete!"
    
    echo -e "${GREEN}${CHECK} Installation completed successfully!${NC}"
    echo ""
    echo -e "${CYAN}${ROCKET} Quick Start:${NC}"
    echo -e "  1. Start services: ${YELLOW}./start_services.sh${NC}"
    echo -e "  2. Open browser to: ${YELLOW}http://127.0.0.1:8000${NC} (Open WebUI)"
    echo -e "  3. Or visit: ${YELLOW}http://127.0.0.1:8090${NC} (Advanced RAG)"
    echo ""
    echo -e "${CYAN}${FOLDER} Your documents go in: ${YELLOW}doccydocs/${NC}"
    echo -e "${CYAN}${BRAIN} Available models:${NC}"
    ollama list
    echo ""
    echo -e "${CYAN}📖 For more information, see:${NC}"
    echo -e "  - ${YELLOW}PROJECT_README.md${NC} - Project overview"
    echo -e "  - ${YELLOW}SETUP.md${NC} - Detailed setup instructions" 
    echo -e "  - ${YELLOW}DEPLOYMENT.md${NC} - Deployment guide"
    echo ""
    echo -e "${GREEN}Happy chatting with your AI! 🤖${NC}"
}

# Main execution
main() {
    check_os
    check_python
    install_ollama
    start_ollama
    create_environments
    install_dependencies
    download_models
    create_config
    create_startup_script
    test_installation
    show_completion
}

# Run main function
main "$@"