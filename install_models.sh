#!/bin/bash

# ===================================================================
# Model Installation Script - Advanced RAG Agent System
# ===================================================================
# This script downloads and manages AI models for the RAG system
# Usage: ./install_models.sh [model_type]
# ===================================================================

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Emojis
ROCKET="🚀"
CHECK="✅"
BRAIN="🧠"
DOWNLOAD="⬇️"

echo -e "${BLUE}${ROCKET} AI Model Installation Script${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# Check if Ollama is installed and running
check_ollama() {
    if ! command -v ollama &> /dev/null; then
        echo -e "${RED}❌ Ollama not found. Please install Ollama first.${NC}"
        echo "Visit: https://ollama.ai/download"
        exit 1
    fi
    
    # Start Ollama if not running
    if ! pgrep -f "ollama serve" > /dev/null; then
        echo -e "${YELLOW}⚠️ Starting Ollama service...${NC}"
        ollama serve > /dev/null 2>&1 &
        sleep 3
    fi
    
    # Verify Ollama is responding
    if ! curl -s http://localhost:11434/api/version > /dev/null; then
        echo -e "${RED}❌ Ollama service not responding${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}${CHECK} Ollama service ready${NC}"
}

# Display available models
show_models() {
    echo -e "${BLUE}${BRAIN} Available Models:${NC}"
    echo ""
    echo -e "${YELLOW}LANGUAGE MODELS (LLM):${NC}"
    echo "1) llama3.2:1b      - 1.3GB - Fastest, good for development"
    echo "2) llama3.2:3b      - 2.0GB - Balanced performance and quality"
    echo "3) mistral:7b       - 4.4GB - Best quality (recommended)"
    echo "4) llama3.1:8b      - 4.7GB - High quality, instruct-tuned"
    echo "5) llama3.1:8b-instruct-q4_K_M - 4.9GB - Optimized version"
    echo ""
    echo -e "${YELLOW}EMBEDDING MODELS (Vector Search):${NC}"
    echo "e1) nomic-embed-text - 274MB - Best for RAG applications"
    echo "e2) all-minilm       - 45MB  - Lightweight alternative"
    echo ""
    echo -e "${YELLOW}PRESET COMBINATIONS:${NC}"
    echo "fast)     - llama3.2:1b + nomic-embed-text (1.6GB total)"
    echo "balanced) - llama3.2:3b + nomic-embed-text (2.3GB total)"
    echo "quality)  - mistral:7b + nomic-embed-text (4.7GB total)"
    echo "all)      - Download all recommended models"
    echo ""
}

# Download a single model
download_model() {
    local model=$1
    local description=$2
    
    echo -e "${BLUE}${DOWNLOAD} Downloading $model ($description)...${NC}"
    
    if ollama list | grep -q "^$model"; then
        echo -e "${GREEN}${CHECK} $model already installed${NC}"
        return 0
    fi
    
    if ollama pull "$model"; then
        echo -e "${GREEN}${CHECK} Successfully downloaded $model${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to download $model${NC}"
        return 1
    fi
}

# Install embedding models
install_embedding_models() {
    echo -e "${BLUE}Installing embedding models...${NC}"
    download_model "nomic-embed-text" "274MB - RAG optimized"
    download_model "all-minilm" "45MB - Lightweight"
}

# Install language models based on choice
install_llm_models() {
    local choice=$1
    
    case $choice in
        1|"llama3.2:1b")
            download_model "llama3.2:1b" "1.3GB - Fast"
            ;;
        2|"llama3.2:3b")
            download_model "llama3.2:3b" "2.0GB - Balanced"
            ;;
        3|"mistral:7b")
            download_model "mistral:7b" "4.4GB - Quality"
            ;;
        4|"llama3.1:8b")
            download_model "llama3.1:8b" "4.7GB - High quality"
            ;;
        5|"llama3.1:8b-instruct-q4_K_M")
            download_model "llama3.1:8b-instruct-q4_K_M" "4.9GB - Optimized"
            ;;
        *)
            echo -e "${RED}❌ Invalid model choice: $choice${NC}"
            return 1
            ;;
    esac
}

# Install preset combinations
install_preset() {
    local preset=$1
    
    case $preset in
        "fast")
            echo -e "${BLUE}Installing FAST preset (llama3.2:1b + embeddings)...${NC}"
            download_model "llama3.2:1b" "1.3GB - Fast"
            download_model "nomic-embed-text" "274MB - RAG optimized"
            ;;
        "balanced")
            echo -e "${BLUE}Installing BALANCED preset (llama3.2:3b + embeddings)...${NC}"
            download_model "llama3.2:3b" "2.0GB - Balanced"
            download_model "nomic-embed-text" "274MB - RAG optimized"
            ;;
        "quality")
            echo -e "${BLUE}Installing QUALITY preset (mistral:7b + embeddings)...${NC}"
            download_model "mistral:7b" "4.4GB - Quality"
            download_model "nomic-embed-text" "274MB - RAG optimized"
            ;;
        "all")
            echo -e "${BLUE}Installing ALL recommended models...${NC}"
            download_model "llama3.2:1b" "1.3GB - Fast"
            download_model "llama3.2:3b" "2.0GB - Balanced"  
            download_model "mistral:7b" "4.4GB - Quality"
            download_model "nomic-embed-text" "274MB - RAG optimized"
            download_model "all-minilm" "45MB - Lightweight"
            ;;
        *)
            echo -e "${RED}❌ Invalid preset: $preset${NC}"
            return 1
            ;;
    esac
}

# List currently installed models
list_installed() {
    echo -e "${BLUE}${BRAIN} Currently Installed Models:${NC}"
    echo ""
    ollama list
    echo ""
}

# Remove a model
remove_model() {
    local model=$1
    
    echo -e "${YELLOW}⚠️ Removing model: $model${NC}"
    
    if ollama list | grep -q "^$model"; then
        if ollama rm "$model"; then
            echo -e "${GREEN}${CHECK} Successfully removed $model${NC}"
        else
            echo -e "${RED}❌ Failed to remove $model${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️ Model $model not found${NC}"
    fi
}

# Interactive mode
interactive_mode() {
    while true; do
        echo ""
        echo -e "${BLUE}Choose an action:${NC}"
        echo "1) Show available models"
        echo "2) Install language model"
        echo "3) Install embedding models"
        echo "4) Install preset combination"
        echo "5) List installed models"
        echo "6) Remove model"
        echo "7) Exit"
        echo ""
        
        read -p "Enter choice (1-7): " action
        
        case $action in
            1)
                show_models
                ;;
            2)
                show_models
                echo ""
                read -p "Enter model choice (1-5): " model_choice
                install_llm_models "$model_choice"
                ;;
            3)
                install_embedding_models
                ;;
            4)
                show_models
                echo ""
                read -p "Enter preset (fast/balanced/quality/all): " preset
                install_preset "$preset"
                ;;
            5)
                list_installed
                ;;
            6)
                list_installed
                echo ""
                read -p "Enter model name to remove: " model_name
                remove_model "$model_name"
                ;;
            7)
                echo -e "${GREEN}${CHECK} Goodbye!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}❌ Invalid choice${NC}"
                ;;
        esac
    done
}

# Main execution
main() {
    check_ollama
    
    if [ $# -eq 0 ]; then
        # No arguments - run interactive mode
        interactive_mode
    else
        # Command line arguments
        case $1 in
            "list")
                list_installed
                ;;
            "embedding"|"embeddings")
                install_embedding_models
                ;;
            "fast"|"balanced"|"quality"|"all")
                install_preset "$1"
                ;;
            "remove")
                if [ -n "$2" ]; then
                    remove_model "$2"
                else
                    echo -e "${RED}❌ Please specify model to remove${NC}"
                    echo "Usage: $0 remove <model_name>"
                fi
                ;;
            *)
                # Try to install as individual model
                if [[ "$1" =~ ^[1-5]$|^llama|^mistral ]]; then
                    install_llm_models "$1"
                else
                    echo -e "${RED}❌ Unknown command: $1${NC}"
                    echo ""
                    echo "Usage: $0 [command]"
                    echo "Commands:"
                    echo "  (no args)           - Interactive mode"
                    echo "  list                - List installed models"
                    echo "  embeddings          - Install embedding models"
                    echo "  fast                - Install fast preset"
                    echo "  balanced            - Install balanced preset"
                    echo "  quality             - Install quality preset"
                    echo "  all                 - Install all models"
                    echo "  remove <model>      - Remove a model"
                    echo "  <model_name>        - Install specific model"
                fi
                ;;
        esac
    fi
}

# Run main function
main "$@"