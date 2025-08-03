#!/bin/bash

# ===================================================================
# Database Backup Script - Advanced RAG Agent System
# ===================================================================
# This script backs up vector databases and document collections
# Usage: ./backup_db.sh [backup_name]
# ===================================================================

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Emojis
BACKUP="💾"
CHECK="✅"
WARNING="⚠️"
FOLDER="📁"

# Configuration
BACKUP_BASE_DIR="./backups"
CHROMA_DB_DIR="./chroma_db"
DOCUMENTS_DIR="./doccydocs"
CONFIG_FILES=(".env" "requirements-basic.txt" "openwebui-requirements.txt")

echo -e "${BLUE}${BACKUP} Database Backup Script${NC}"
echo -e "${BLUE}===========================${NC}"
echo ""

# Create backup directory if it doesn't exist
create_backup_dir() {
    if [ ! -d "$BACKUP_BASE_DIR" ]; then
        mkdir -p "$BACKUP_BASE_DIR"
        echo -e "${GREEN}${CHECK} Created backup directory: $BACKUP_BASE_DIR${NC}"
    fi
}

# Generate backup name with timestamp
generate_backup_name() {
    local custom_name=$1
    local timestamp=$(date +%Y%m%d_%H%M%S)
    
    if [ -n "$custom_name" ]; then
        echo "${custom_name}_${timestamp}"
    else
        echo "auto_backup_${timestamp}"
    fi
}

# Check if ChromaDB is in use
check_db_status() {
    local pids=$(pgrep -f "smart_rag_agent.py\|app.py" 2>/dev/null || true)
    
    if [ -n "$pids" ]; then
        echo -e "${YELLOW}${WARNING} RAG services are running. Consider stopping them for a clean backup.${NC}"
        echo "Running processes: $pids"
        echo ""
        read -p "Continue with backup anyway? (y/N): " continue_backup
        
        if [[ ! "$continue_backup" =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Backup cancelled${NC}"
            exit 0
        fi
    fi
}

# Backup ChromaDB
backup_chromadb() {
    local backup_name=$1
    local backup_path="${BACKUP_BASE_DIR}/${backup_name}"
    
    if [ -d "$CHROMA_DB_DIR" ]; then
        echo -e "${BLUE}Backing up ChromaDB...${NC}"
        
        # Create backup with compression
        tar -czf "${backup_path}/chromadb.tar.gz" -C "$(dirname "$CHROMA_DB_DIR")" "$(basename "$CHROMA_DB_DIR")"
        
        # Get backup size
        local size=$(du -h "${backup_path}/chromadb.tar.gz" | cut -f1)
        echo -e "${GREEN}${CHECK} ChromaDB backed up (${size})${NC}"
        
        # Create metadata
        echo "ChromaDB Backup" > "${backup_path}/chromadb.info"
        echo "Date: $(date)" >> "${backup_path}/chromadb.info"
        echo "Size: $size" >> "${backup_path}/chromadb.info"
        echo "Source: $CHROMA_DB_DIR" >> "${backup_path}/chromadb.info"
        
        # Count collections if possible
        if command -v python3 &> /dev/null && [ -f "smart_rag_agent.py" ]; then
            local collections=$(python3 -c "
import chromadb
try:
    client = chromadb.PersistentClient(path='$CHROMA_DB_DIR')
    collections = client.list_collections()
    print(f'Collections: {len(collections)}')
    for col in collections:
        print(f'  - {col.name}: {col.count()} documents')
except Exception as e:
    print(f'Could not read collections: {e}')
" 2>/dev/null || echo "Collections: Unable to read")
            echo "$collections" >> "${backup_path}/chromadb.info"
        fi
    else
        echo -e "${YELLOW}${WARNING} ChromaDB directory not found: $CHROMA_DB_DIR${NC}"
    fi
}

# Backup documents
backup_documents() {
    local backup_name=$1
    local backup_path="${BACKUP_BASE_DIR}/${backup_name}"
    
    if [ -d "$DOCUMENTS_DIR" ]; then
        echo -e "${BLUE}Backing up documents...${NC}"
        
        # Count files
        local file_count=$(find "$DOCUMENTS_DIR" -type f | wc -l)
        
        if [ "$file_count" -gt 0 ]; then
            # Create backup with compression
            tar -czf "${backup_path}/documents.tar.gz" -C "$(dirname "$DOCUMENTS_DIR")" "$(basename "$DOCUMENTS_DIR")"
            
            # Get backup size
            local size=$(du -h "${backup_path}/documents.tar.gz" | cut -f1)
            echo -e "${GREEN}${CHECK} Documents backed up (${file_count} files, ${size})${NC}"
            
            # Create metadata
            echo "Documents Backup" > "${backup_path}/documents.info"
            echo "Date: $(date)" >> "${backup_path}/documents.info"
            echo "Files: $file_count" >> "${backup_path}/documents.info"
            echo "Size: $size" >> "${backup_path}/documents.info"
            echo "Source: $DOCUMENTS_DIR" >> "${backup_path}/documents.info"
            echo "" >> "${backup_path}/documents.info"
            echo "File list:" >> "${backup_path}/documents.info"
            find "$DOCUMENTS_DIR" -type f -exec basename {} \; | sort >> "${backup_path}/documents.info"
        else
            echo -e "${YELLOW}${WARNING} No documents found in $DOCUMENTS_DIR${NC}"
        fi
    else
        echo -e "${YELLOW}${WARNING} Documents directory not found: $DOCUMENTS_DIR${NC}"
    fi
}

# Backup configuration files
backup_config() {
    local backup_name=$1
    local backup_path="${BACKUP_BASE_DIR}/${backup_name}"
    
    echo -e "${BLUE}Backing up configuration...${NC}"
    
    mkdir -p "${backup_path}/config"
    
    for config_file in "${CONFIG_FILES[@]}"; do
        if [ -f "$config_file" ]; then
            cp "$config_file" "${backup_path}/config/"
            echo -e "${GREEN}${CHECK} Backed up: $config_file${NC}"
        else
            echo -e "${YELLOW}${WARNING} Config file not found: $config_file${NC}"
        fi
    done
    
    # Backup Python environments info
    if [ -d "rag-env" ]; then
        pip list --format=freeze > "${backup_path}/config/rag-env-requirements.txt" 2>/dev/null || echo "# Could not generate requirements" > "${backup_path}/config/rag-env-requirements.txt"
    fi
    
    if [ -d "openwebui-env" ]; then
        source openwebui-env/bin/activate 2>/dev/null && pip list --format=freeze > "${backup_path}/config/openwebui-env-requirements.txt" && deactivate || echo "# Could not generate requirements" > "${backup_path}/config/openwebui-env-requirements.txt"
    fi
}

# Create backup summary
create_summary() {
    local backup_name=$1
    local backup_path="${BACKUP_BASE_DIR}/${backup_name}"
    
    echo -e "${BLUE}Creating backup summary...${NC}"
    
    cat > "${backup_path}/BACKUP_INFO.txt" << EOF
Advanced RAG Agent System - Backup Summary
==========================================

Backup Name: $backup_name
Created: $(date)
System: $(uname -a)
Backup Location: $backup_path

Contents:
EOF
    
    # List contents with sizes
    if [ -f "${backup_path}/chromadb.tar.gz" ]; then
        local chromadb_size=$(du -h "${backup_path}/chromadb.tar.gz" | cut -f1)
        echo "  ✅ ChromaDB Vector Database ($chromadb_size)" >> "${backup_path}/BACKUP_INFO.txt"
    else
        echo "  ❌ ChromaDB Vector Database (not found)" >> "${backup_path}/BACKUP_INFO.txt"
    fi
    
    if [ -f "${backup_path}/documents.tar.gz" ]; then
        local docs_size=$(du -h "${backup_path}/documents.tar.gz" | cut -f1)
        echo "  ✅ Document Collection ($docs_size)" >> "${backup_path}/BACKUP_INFO.txt"
    else
        echo "  ❌ Document Collection (not found)" >> "${backup_path}/BACKUP_INFO.txt"
    fi
    
    if [ -d "${backup_path}/config" ]; then
        echo "  ✅ Configuration Files" >> "${backup_path}/BACKUP_INFO.txt"
    else
        echo "  ❌ Configuration Files (not found)" >> "${backup_path}/BACKUP_INFO.txt"
    fi
    
    echo "" >> "${backup_path}/BACKUP_INFO.txt"
    echo "Total Backup Size: $(du -sh "$backup_path" | cut -f1)" >> "${backup_path}/BACKUP_INFO.txt"
    
    echo "" >> "${backup_path}/BACKUP_INFO.txt"
    echo "Restore Instructions:" >> "${backup_path}/BACKUP_INFO.txt"
    echo "===================" >> "${backup_path}/BACKUP_INFO.txt"
    echo "1. Extract ChromaDB: tar -xzf chromadb.tar.gz" >> "${backup_path}/BACKUP_INFO.txt"
    echo "2. Extract Documents: tar -xzf documents.tar.gz" >> "${backup_path}/BACKUP_INFO.txt"
    echo "3. Copy config files from config/ directory" >> "${backup_path}/BACKUP_INFO.txt"
    echo "4. Restart RAG services" >> "${backup_path}/BACKUP_INFO.txt"
}

# List existing backups
list_backups() {
    echo -e "${BLUE}${FOLDER} Existing Backups:${NC}"
    echo ""
    
    if [ -d "$BACKUP_BASE_DIR" ] && [ "$(ls -A "$BACKUP_BASE_DIR" 2>/dev/null)" ]; then
        for backup_dir in "$BACKUP_BASE_DIR"/*; do
            if [ -d "$backup_dir" ]; then
                local backup_name=$(basename "$backup_dir")
                local backup_size=$(du -sh "$backup_dir" | cut -f1)
                local backup_date=""
                
                if [ -f "$backup_dir/BACKUP_INFO.txt" ]; then
                    backup_date=$(grep "Created:" "$backup_dir/BACKUP_INFO.txt" | cut -d' ' -f2-)
                fi
                
                echo -e "  📦 $backup_name (${backup_size}) - $backup_date"
            fi
        done
    else
        echo -e "${YELLOW}  No backups found${NC}"
    fi
    echo ""
}

# Restore from backup
restore_backup() {
    local backup_name=$1
    local backup_path="${BACKUP_BASE_DIR}/${backup_name}"
    
    if [ ! -d "$backup_path" ]; then
        echo -e "${RED}❌ Backup not found: $backup_name${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}${WARNING} This will overwrite existing data!${NC}"
    echo -e "Backup to restore: $backup_name"
    echo ""
    
    read -p "Are you sure you want to continue? (y/N): " confirm
    
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Restore cancelled${NC}"
        return 0
    fi
    
    # Stop services
    echo -e "${BLUE}Stopping RAG services...${NC}"
    pkill -f "smart_rag_agent.py\|app.py" 2>/dev/null || true
    sleep 2
    
    # Restore ChromaDB
    if [ -f "${backup_path}/chromadb.tar.gz" ]; then
        echo -e "${BLUE}Restoring ChromaDB...${NC}"
        
        # Backup existing DB if it exists
        if [ -d "$CHROMA_DB_DIR" ]; then
            mv "$CHROMA_DB_DIR" "${CHROMA_DB_DIR}.backup.$(date +%s)"
        fi
        
        tar -xzf "${backup_path}/chromadb.tar.gz" -C "$(dirname "$CHROMA_DB_DIR")"
        echo -e "${GREEN}${CHECK} ChromaDB restored${NC}"
    fi
    
    # Restore documents
    if [ -f "${backup_path}/documents.tar.gz" ]; then
        echo -e "${BLUE}Restoring documents...${NC}"
        
        # Backup existing documents if they exist
        if [ -d "$DOCUMENTS_DIR" ]; then
            mv "$DOCUMENTS_DIR" "${DOCUMENTS_DIR}.backup.$(date +%s)"
        fi
        
        tar -xzf "${backup_path}/documents.tar.gz" -C "$(dirname "$DOCUMENTS_DIR")"
        echo -e "${GREEN}${CHECK} Documents restored${NC}"
    fi
    
    # Restore configuration
    if [ -d "${backup_path}/config" ]; then
        echo -e "${BLUE}Restoring configuration...${NC}"
        
        for config_file in "${CONFIG_FILES[@]}"; do
            if [ -f "${backup_path}/config/$config_file" ]; then
                # Backup existing config
                if [ -f "$config_file" ]; then
                    cp "$config_file" "${config_file}.backup.$(date +%s)"
                fi
                
                cp "${backup_path}/config/$config_file" "$config_file"
                echo -e "${GREEN}${CHECK} Restored: $config_file${NC}"
            fi
        done
    fi
    
    echo -e "${GREEN}${CHECK} Restore completed successfully!${NC}"
    echo -e "${BLUE}You can now restart your RAG services${NC}"
}

# Clean old backups
cleanup_old_backups() {
    local days=${1:-7}
    
    echo -e "${BLUE}Cleaning backups older than $days days...${NC}"
    
    if [ -d "$BACKUP_BASE_DIR" ]; then
        find "$BACKUP_BASE_DIR" -maxdepth 1 -type d -mtime +$days -exec rm -rf {} \;
        echo -e "${GREEN}${CHECK} Cleanup completed${NC}"
    else
        echo -e "${YELLOW}${WARNING} No backup directory found${NC}"
    fi
}

# Show help
show_help() {
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  backup [name]       - Create backup (optional custom name)"
    echo "  list               - List existing backups"
    echo "  restore <name>     - Restore from backup"
    echo "  cleanup [days]     - Remove backups older than N days (default: 7)"
    echo "  help               - Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 backup                    # Auto-named backup"
    echo "  $0 backup before_upgrade     # Custom named backup"
    echo "  $0 list                      # List all backups"
    echo "  $0 restore auto_backup_20240103_142530"
    echo "  $0 cleanup 14                # Remove backups older than 14 days"
}

# Main execution
main() {
    case ${1:-backup} in
        "backup")
            create_backup_dir
            check_db_status
            
            local backup_name=$(generate_backup_name "$2")
            local backup_path="${BACKUP_BASE_DIR}/${backup_name}"
            
            mkdir -p "$backup_path"
            
            echo -e "${BLUE}Creating backup: $backup_name${NC}"
            echo ""
            
            backup_chromadb "$backup_name"
            backup_documents "$backup_name"
            backup_config "$backup_name"
            create_summary "$backup_name"
            
            echo ""
            echo -e "${GREEN}${CHECK} Backup completed successfully!${NC}"
            echo -e "${BLUE}Backup location: $backup_path${NC}"
            echo -e "${BLUE}Total size: $(du -sh "$backup_path" | cut -f1)${NC}"
            ;;
        "list")
            list_backups
            ;;
        "restore")
            if [ -z "$2" ]; then
                echo -e "${RED}❌ Please specify backup name to restore${NC}"
                echo "Use '$0 list' to see available backups"
                exit 1
            fi
            restore_backup "$2"
            ;;
        "cleanup")
            cleanup_old_backups "$2"
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            echo -e "${RED}❌ Unknown command: $1${NC}"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"