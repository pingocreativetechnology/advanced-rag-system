# app.py
from flask import Flask, request, Response, render_template_string, jsonify, redirect, url_for, flash
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
import os
import shutil
from datetime import datetime
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from rag_agent import SimpleRAGAgent  # Import simple RAG agent
from enhanced_rag_agent import ImprovedRAGAgent  # Import enhanced RAG agent

load_dotenv()

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # For flash messages

# File upload configuration
UPLOAD_FOLDER = 'doccydocs'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'md'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize Twilio client (optional for web interface)
try:
    client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
except:
    client = None
    print("Twilio credentials not found - running web interface only")

# Initialize your LangChain agent (simple or enhanced based on env variable)
if os.getenv("USE_ENHANCED_AGENT", "").lower() in ("1", "true", "yes"):
    agent = ImprovedRAGAgent()
    print("✅ Running Enhanced RAG Agent v2")
else:
    agent = SimpleRAGAgent()
    print("✅ Running Simple RAG Agent")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_stats():
    """Get statistics about files in the knowledge base"""
    stats = {
        'total_files': 0,
        'total_size': 0,
        'files': [],
        'last_updated': None
    }
    
    if not os.path.exists(UPLOAD_FOLDER):
        return stats
    
    for filename in os.listdir(UPLOAD_FOLDER):
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.isfile(filepath):
            file_stat = os.stat(filepath)
            file_info = {
                'name': filename,
                'type': filename.rsplit('.', 1)[1].lower() if '.' in filename else 'unknown',
                'size': file_stat.st_size,
                'size_mb': round(file_stat.st_size / (1024*1024), 2),
                'modified': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'active' if filename.endswith(('.txt', '.pdf')) else 'supported'
            }
            stats['files'].append(file_info)
            stats['total_files'] += 1
            stats['total_size'] += file_stat.st_size
    
    stats['total_size_mb'] = round(stats['total_size'] / (1024*1024), 2)
    stats['knowledge_base_size'] = len(agent.knowledge_base) if agent.knowledge_base else 0
    
    return stats

@app.route('/voice', methods=['POST'])
def handle_voice():
    """Handle incoming voice calls"""
    response = VoiceResponse()
    
    # Welcome message
    response.say("Hello! I'm your AI assistant. How can I help you today?")
    
    # Start gathering speech input
    gather = response.gather(
        input='speech',
        action='/process_speech',
        method='POST',
        speech_timeout='auto',
        language='en-US'
    )
    
    # Fallback if no speech detected
    response.say("I didn't hear anything. Please try calling again.")
    
    return Response(str(response), mimetype='text/xml')

@app.route('/process_speech', methods=['POST'])
def process_speech():
    """Process the speech input and generate response"""
    response = VoiceResponse()
    
    # Get the speech result from Twilio
    speech_result = request.form.get('SpeechResult', '')
    
    if speech_result:
        try:
            # Send user input to your LangChain agent
            agent_response = agent.run(speech_result)
            
            # Convert response to speech
            response.say(agent_response)
            
            # Continue conversation
            gather = response.gather(
                input='speech',
                action='/process_speech',
                method='POST',
                speech_timeout='auto',
                language='en-US'
            )
            
            # Timeout message
            response.say("Are you still there? Feel free to ask me anything else.")
            
        except Exception as e:
            response.say("I'm sorry, I encountered an error processing your request. Please try again.")
            print(f"Error: {e}")
    else:
        response.say("I didn't understand that. Could you please repeat your question?")
        response.redirect('/voice')
    
    return Response(str(response), mimetype='text/xml')

@app.route('/status', methods=['POST'])
def call_status():
    """Handle call status updates"""
    call_status = request.form.get('CallStatus')
    print(f"Call status: {call_status}")
    return Response('', mimetype='text/xml')

# Global mode state
app_mode = 'simple'  # 'simple' or 'advanced'

@app.route('/set-mode', methods=['POST'])
def set_mode():
    """Set application mode"""
    global app_mode
    data = request.get_json()
    new_mode = data.get('mode', 'simple')
    if new_mode in ['simple', 'advanced']:
        app_mode = new_mode
        return jsonify({'success': True, 'mode': app_mode})
    return jsonify({'success': False, 'error': 'Invalid mode'})

@app.route('/get-mode')
def get_mode():
    """Get current application mode"""
    return jsonify({'mode': app_mode})

# Web interface routes
@app.route('/')
def home():
    """Web interface for testing the RAG agent"""
    stats = get_file_stats()
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>RAG Agent Management</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
        <style>
            :root {
                /* Bauhaus-inspired minimal palette */
                --bg-primary: #fafafa;
                --bg-secondary: #ffffff;
                --bg-accent: #f5f5f5;
                --text-primary: #1a1a1a;
                --text-secondary: #525252;
                --text-muted: #737373;
                --accent-primary: #0070f3;
                --accent-secondary: #005cc5;
                --success: #00c851;
                --warning: #ffb900;
                --danger: #dc3545;
                --border: #e0e0e0;
                --border-subtle: #f0f0f0;
                --shadow: rgba(0,0,0,0.04);
                --shadow-medium: rgba(0,0,0,0.08);
                --radius: 6px;
                --radius-sm: 4px;
                --spacing-xs: 4px;
                --spacing-sm: 8px;
                --spacing-md: 16px;
                --spacing-lg: 24px;
                --spacing-xl: 32px;
            }
            
            [data-theme="dark"] {
                --bg-primary: #0a0a0a;
                --bg-secondary: #1a1a1a;
                --bg-accent: #252525;
                --text-primary: #fafafa;
                --text-secondary: #a3a3a3;
                --text-muted: #737373;
                --accent-primary: #0084ff;
                --accent-secondary: #0070f3;
                --success: #00d564;
                --warning: #ffc107;
                --danger: #ff3838;
                --border: #2a2a2a;
                --border-subtle: #1f1f1f;
                --shadow: rgba(0,0,0,0.3);
                --shadow-medium: rgba(0,0,0,0.5);
            }

            /* Advanced Mode Styles */
            [data-mode="simple"] .advanced-only {
                display: none !important;
            }

            [data-mode="advanced"] .advanced-only {
                display: block;
            }

            [data-mode="advanced"] {
                --advanced-accent: #9c27b0;
                --advanced-bg: linear-gradient(135deg, var(--bg-secondary) 0%, rgba(156, 39, 176, 0.1) 100%);
            }

            #advanced-controls {
                background: var(--advanced-bg, var(--bg-secondary));
                border: 2px solid var(--advanced-accent, var(--accent-secondary));
                border-radius: 8px;
                padding: 1rem;
                margin-bottom: 1rem;
                box-shadow: var(--shadow-medium);
                transition: all 0.3s ease;
            }

            #advanced-controls h4 {
                color: var(--advanced-accent, var(--accent-secondary));
                margin: 0 0 0.5rem 0;
                font-size: 1.1rem;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }

            #advanced-controls label {
                color: var(--text-secondary);
                font-size: 0.9rem;
                font-weight: 500;
                display: block;
                margin-bottom: 0.25rem;
            }

            #advanced-controls input[type="range"] {
                width: 100%;
                height: 6px;
                border-radius: 3px;
                background: var(--bg-accent);
                outline: none;
                -webkit-appearance: none;
                margin: 0.25rem 0;
            }

            #advanced-controls input[type="range"]::-webkit-slider-thumb {
                -webkit-appearance: none;
                appearance: none;
                width: 16px;
                height: 16px;
                border-radius: 50%;
                background: var(--advanced-accent, var(--accent-secondary));
                cursor: pointer;
                box-shadow: var(--shadow);
            }

            #advanced-controls input[type="range"]::-moz-range-thumb {
                width: 16px;
                height: 16px;
                border-radius: 50%;
                background: var(--advanced-accent, var(--accent-secondary));
                cursor: pointer;
                border: none;
                box-shadow: var(--shadow);
            }

            #advanced-controls select {
                width: 100%;
                padding: 0.5rem;
                border: 1px solid var(--border);
                border-radius: 6px;
                background: var(--bg-accent);
                color: var(--text-primary);
                font-size: 0.9rem;
                margin-top: 0.25rem;
            }

            #advanced-controls select:focus {
                outline: none;
                border-color: var(--advanced-accent, var(--accent-secondary));
                box-shadow: 0 0 0 2px rgba(156, 39, 176, 0.2);
            }

            /* Advanced mode header indicator */
            [data-mode="advanced"] .header {
                border-bottom: 3px solid var(--advanced-accent, var(--accent-secondary));
            }

            [data-mode="advanced"] #mode-toggle {
                background: var(--advanced-accent, var(--accent-secondary));
                color: white;
                box-shadow: var(--shadow-medium);
            }

            /* Advanced mode message styling */
            [data-mode="advanced"] .message.agent {
                border-left: 4px solid var(--advanced-accent, var(--accent-secondary));
            }

            /* Advanced mode animations */
            @keyframes advanced-pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.7; }
            }

            [data-mode="advanced"] .thinking {
                animation: advanced-pulse 1.5s ease-in-out infinite;
            }
            
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body { 
                font-family: 'Inter', 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
                font-weight: 400;
                font-size: 14px;
                max-width: 1200px; 
                margin: 0 auto; 
                padding: var(--spacing-xl); 
                background: var(--bg-primary);
                color: var(--text-primary);
                transition: background 0.2s ease, color 0.2s ease;
                line-height: 1.5;
                letter-spacing: -0.01em;
            }
            
            .header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: var(--spacing-xl);
                padding-bottom: var(--spacing-lg);
                border-bottom: 1px solid var(--border);
            }
            
            h1 {
                font-size: 20px;
                font-weight: 600;
                letter-spacing: -0.02em;
                color: var(--text-primary);
            }
            
            .theme-toggle {
                background: var(--bg-secondary);
                border: 1px solid var(--border);
                color: var(--text-secondary);
                padding: var(--spacing-sm) var(--spacing-md);
                border-radius: var(--radius);
                cursor: pointer;
                transition: all 0.15s ease;
                font-size: 12px;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            
            .theme-toggle:hover {
                background: var(--bg-accent);
                border-color: var(--accent-primary);
                color: var(--accent-primary);
            }
            
            .tabs { 
                display: flex; 
                background: var(--bg-secondary);
                border: 1px solid var(--border);
                border-radius: var(--radius);
                padding: var(--spacing-xs);
                margin-bottom: var(--spacing-xl);
                gap: var(--spacing-xs);
            }
            
            .tab { 
                flex: 1;
                padding: var(--spacing-md) var(--spacing-lg); 
                cursor: pointer; 
                background: transparent;
                border: none; 
                color: var(--text-secondary);
                border-radius: var(--radius);
                transition: all 0.15s ease;
                font-weight: 500;
                font-size: 13px;
                text-align: center;
            }
            
            .tab.active { 
                background: var(--accent-primary); 
                color: white;
            }
            
            .tab:hover:not(.active) {
                background: var(--bg-accent);
                color: var(--text-primary);
            }
            
            .tab-content { display: none; }
            .tab-content.active { display: block; }
            
            .chat-container { 
                border: 1px solid var(--border); 
                height: 350px; 
                overflow-y: scroll; 
                padding: 20px; 
                margin: 20px 0; 
                background: var(--bg-secondary);
                border-radius: var(--radius);
                box-shadow: inset 0 2px 4px var(--shadow);
            }
            
            .message { 
                margin: 15px 0; 
                padding: 15px 20px; 
                border-radius: 18px;
                max-width: 80%;
                box-shadow: 0 2px 8px var(--shadow);
            }
            
            .user { 
                background: var(--accent-primary); 
                color: white; 
                margin-left: auto;
                border-bottom-right-radius: 4px;
            }
            
            .agent { 
                background: var(--success); 
                color: white;
                margin-right: auto;
                border-bottom-left-radius: 4px;
            }
            
            .system {
                background: var(--accent-primary);
                color: white;
                margin: 0 auto;
                text-align: center;
                font-size: 12px;
                padding: 8px 16px;
                border-radius: 20px;
                max-width: 60%;
                opacity: 0.9;
            }
            
            .input-group {
                display: flex;
                gap: 10px;
                margin-top: 20px;
            }
            
            input[type="text"] { 
                flex: 1;
                padding: 15px 20px; 
                font-size: 16px;
                border: 2px solid var(--border);
                border-radius: var(--radius);
                background: var(--bg-primary);
                color: var(--text-primary);
                transition: all 0.3s ease;
            }
            
            input[type="text"]:focus {
                outline: none;
                border-color: var(--accent-primary);
                box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
            }
            
            button { 
                padding: var(--spacing-md) var(--spacing-lg); 
                font-size: 13px; 
                background: var(--accent-primary); 
                color: white; 
                border: none; 
                cursor: pointer; 
                margin: var(--spacing-xs);
                border-radius: var(--radius);
                transition: background-color 0.15s ease;
                font-weight: 500;
            }
            
            button:hover { 
                background: var(--accent-secondary);
                box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
            }
            
            button.danger { 
                background: var(--danger); 
                padding: 8px 16px;
                font-size: 14px;
            }
            
            button.danger:hover { 
                background: #c0392b;
                box-shadow: 0 4px 12px rgba(231, 76, 60, 0.3);
            }
            
            .status { 
                margin: 20px 0; 
                color: var(--text-secondary);
                background: var(--bg-secondary);
                padding: 15px 20px;
                border-radius: var(--radius);
                border-left: 4px solid var(--accent-primary);
            }
            
            .stats-grid { 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); 
                gap: var(--spacing-lg); 
                margin: var(--spacing-xl) 0; 
            }
            
            .stat-card { 
                background: var(--bg-secondary); 
                padding: var(--spacing-lg); 
                border-radius: var(--radius);
                border: 1px solid var(--border);
                transition: border-color 0.15s ease;
            }
            
            .stat-card:hover {
                border-color: var(--accent-primary);
            }
            
            .stat-card h3 {
                color: var(--text-secondary);
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                margin-bottom: var(--spacing-md);
            }
            
            .stat-card h2 {
                color: var(--text-primary);
                font-size: 24px;
                font-weight: 600;
                margin-bottom: var(--spacing-xs);
            }
            
            .stat-card small {
                color: var(--text-muted);
                font-size: 11px;
            }
            
            .tech-stats {
                background: var(--bg-secondary);
                border-radius: var(--radius);
                padding: 20px;
                margin: 20px 0;
                border: 1px solid var(--border);
            }
            
            .tech-row {
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                border-bottom: 1px solid var(--border);
            }
            
            .tech-row:last-child {
                border-bottom: none;
            }
            
            .tech-label {
                font-weight: 500;
                color: var(--text-secondary);
            }
            
            .tech-value {
                color: var(--text-primary);
                font-family: 'Monaco', 'Menlo', monospace;
                font-size: 14px;
            }
            
            .file-table { 
                width: 100%; 
                border-collapse: collapse; 
                margin: 20px 0;
                background: var(--bg-secondary);
                border-radius: var(--radius);
                overflow: hidden;
                box-shadow: 0 4px 16px var(--shadow); 
            }
            
            .file-table th, .file-table td { 
                padding: 15px 20px; 
                text-align: left; 
                border-bottom: 1px solid var(--border); 
            }
            
            .file-table th { 
                background: var(--bg-tertiary);
                font-weight: 600;
                color: var(--text-secondary);
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .file-table tr:hover {
                background: var(--bg-tertiary);
            }
            
            .status-badge { 
                padding: 4px 12px; 
                border-radius: 20px; 
                font-size: 12px; 
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .status-active { 
                background: rgba(46, 204, 113, 0.2); 
                color: var(--success);
                border: 1px solid var(--success);
            }
            
            .status-supported { 
                background: rgba(241, 196, 15, 0.2); 
                color: var(--warning);
                border: 1px solid var(--warning);
            }
            
            .upload-area { 
                border: 2px dashed var(--border); 
                padding: 40px 20px; 
                text-align: center; 
                margin: 20px 0;
                border-radius: var(--radius);
                background: var(--bg-secondary);
                transition: all 0.3s ease;
            }
            
            .upload-area.dragover { 
                border-color: var(--accent-primary); 
                background: rgba(52, 152, 219, 0.1);
                transform: scale(1.02);
            }
            
            .model-indicator {
                display: inline-flex;
                align-items: center;
                gap: var(--spacing-sm);
                background: var(--bg-secondary);
                color: var(--text-primary);
                border: 1px solid var(--border);
                padding: var(--spacing-sm) var(--spacing-md);
                border-radius: var(--radius);
                font-size: 12px;
                font-weight: 600;
            }
            
            #model-params {
                background: rgba(255, 255, 255, 0.2);
                padding: 2px 6px;
                border-radius: 10px;
                font-weight: 700;
                font-size: 11px;
                margin-left: 4px;
            }
            
            .model-tags {
                display: flex;
                gap: 8px;
                align-items: center;
            }
            
            .tag {
                background: #2c3e50;
                color: #e9ecef;
                border: 1px solid #6c757d;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 10px;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                transition: all 0.3s ease;
            }
            
            [data-theme="dark"] .tag {
                background: #1a1a1a;
                color: #ced4da;
                border: 1px solid #495057;
            }
            
            .tag:hover {
                background: #34495e;
                border-color: #adb5bd;
                transform: translateY(-1px);
            }
            
            [data-theme="dark"] .tag:hover {
                background: #2d2d2d;
                border-color: #6c757d;
            }
            
            .model-indicator.loading {
                background: var(--warning);
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.7; }
                100% { opacity: 1; }
            }
            
            h1 {
                color: var(--text-primary);
                font-weight: 700;
                font-size: 28px;
            }
            
            h2 {
                color: var(--text-primary);
                margin-bottom: 20px;
                font-weight: 600;
            }
            
            @media (max-width: 768px) {
                body { padding: 15px; }
                .header { flex-direction: column; gap: 15px; }
                .header > div { flex-direction: column; align-items: flex-start; gap: 10px; }
                .model-tags { flex-wrap: wrap; }
                .tag { font-size: 9px; padding: 3px 6px; }
                .stats-grid { grid-template-columns: 1fr; }
                .message { max-width: 95%; }
                .input-group { flex-direction: column; }
            }
        </style>
    </head>
    <body>
        <!-- SECTION: 1-header-section -->
        <div class="header" id="1-main-header" data-section-id="1-header-section" data-section-name="Main Header Navigation">
            <div id="2-header-left" data-section-id="2-header-left-section" data-section-name="Header Left Content">
                <h1>🤖 RAG Agent Management System</h1>
                <div id="3-model-info-container" data-section-id="3-model-info-section" data-section-name="Model Information Display" style="display: flex; align-items: center; gap: 12px;">
                    <span class="model-indicator" id="4-model-status" data-section-id="4-model-status-section" data-section-name="Model Status Indicator">
                        <span id="5-model-brain-icon">🧠</span>
                        <span id="6-current-model">Mistral</span>
                        <span id="7-model-params">7B</span>
                    </span>
                    <div class="model-tags" id="8-model-tags" data-section-id="5-model-tags-section" data-section-name="Model Capability Tags">
                        <span class="tag">Superior Reasoning</span>
                        <span class="tag">Versatile</span>
                        <span class="tag">Advanced</span>
                    </div>
                </div>
            </div>
            <div id="9-header-right" data-section-id="6-header-right-section" data-section-name="Header Right Controls">
                <button class="theme-toggle" id="mode-toggle" onclick="toggleMode()">
                    <span id="mode-icon">🔰</span>
                    <span id="mode-text">Simple</span>
                </button>
                <button class="theme-toggle" onclick="toggleTheme()">
                    <span id="10-theme-icon">🌙</span>
                    <span id="11-theme-text">Dark Mode</span>
                </button>
            </div>
        </div>
        
        <div class="tabs" id="12-main-tabs">
            <button class="tab active" id="13-chat-tab-btn" onclick="openTab(event, 'chat-tab')">💬 Chat</button>
            <button class="tab" id="14-files-tab-btn" onclick="openTab(event, 'files-tab')">📁 File Management</button>
            <button class="tab" id="15-stats-tab-btn" onclick="openTab(event, 'stats-tab')">📊 Statistics</button>
            <button class="tab" id="16-technical-tab-btn" onclick="openTab(event, 'technical-tab')">⚙️ Technical</button>
        </div>

        <!-- Chat Tab -->
        <div id="chat-tab" class="tab-content active">
            <div class="status" id="17-chat-status">
                Knowledge base: <strong>{{ stats.knowledge_base_size }}</strong> characters from <strong>{{ stats.total_files }}</strong> files
            </div>
            <div id="chat-container" class="chat-container"></div>
            <div class="input-group" id="18-chat-input-group">
                <input type="text" id="message-input" placeholder="Ask me anything about your knowledge base..." onkeypress="if(event.key==='Enter') sendMessage()">
                <button id="19-send-button" onclick="sendMessage()">Send</button>
            </div>
        </div>

        <!-- Files Tab -->
        <div id="files-tab" class="tab-content">
            <div id="20-files-header">
                <h2>📁 Knowledge Base Files</h2>
            </div>
            
            <div class="upload-area" id="21-upload-area">
                <div id="22-upload-content">
                    <h3>📤 Upload New Files</h3>
                    <p>Drag and drop files here or click to browse</p>
                    <form id="23-upload-form" enctype="multipart/form-data">
                        <input type="file" id="file-input" name="file" multiple accept=".txt,.pdf,.doc,.docx,.md" style="display: none;">
                        <button type="button" id="24-choose-files-btn" onclick="document.getElementById('file-input').click()">Choose Files</button>
                        <p><small>Supported: .txt, .pdf, .doc, .docx, .md (Max 16MB each)</small></p>
                    </form>
                </div>
            </div>

            <div id="25-files-table-container">
                <table class="file-table" id="26-files-table">
                    <thead id="27-files-table-head">
                        <tr>
                            <th>📄 File Name</th>
                            <th>📏 Type</th>
                            <th>💾 Size</th>
                            <th>🕒 Last Modified</th>
                            <th>⚡ Status</th>
                            <th>🛠️ Actions</th>
                        </tr>
                    </thead>
                    <tbody id="28-files-table-body">
                        {% for file in stats.files %}
                        <tr id="29-file-row-{{ loop.index }}">
                            <td>{{ file.name }}</td>
                            <td>{{ file.type.upper() }}</td>
                            <td>{{ file.size_mb }} MB</td>
                            <td>{{ file.modified }}</td>
                            <td><span class="status-badge status-{{ file.status }}">{{ file.status.upper() }}</span></td>
                            <td>
                                <button class="danger" id="30-delete-btn-{{ loop.index }}" onclick="deleteFile('{{ file.name }}')">🗑️ Delete</button>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Stats Tab -->
        <div id="stats-tab" class="tab-content">
            <div id="31-stats-header">
                <h2>📊 Knowledge Base Statistics</h2>
            </div>
            
            <div class="stats-grid" id="32-stats-grid">
                <div class="stat-card" id="33-files-stat-card">
                    <h3>📁 Total Files</h3>
                    <h2>{{ stats.total_files }}</h2>
                </div>
                <div class="stat-card" id="34-size-stat-card">
                    <h3>💾 Total Size</h3>
                    <h2>{{ stats.total_size_mb }} MB</h2>
                </div>
                <div class="stat-card" id="35-knowledge-stat-card">
                    <h3>🧠 Knowledge Base</h3>
                    <h2>{{ stats.knowledge_base_size }}</h2>
                    <small>Characters processed</small>
                </div>
                <div class="stat-card" id="36-model-stat-card">
                    <h3>🤖 Model Status</h3>
                    <h2 id="model-display">Mistral 7B</h2>
                    <small>Active AI Model</small>
                </div>
            </div>
            
            <div id="37-stats-actions">
                <button id="38-reload-kb-btn" onclick="reloadKnowledgeBase()">🔄 Reload Knowledge Base</button>
            </div>
        </div>

        <!-- Technical Tab -->
        <div id="technical-tab" class="tab-content">
            <h2>⚙️ Technical Configuration</h2>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>🧠 Model Parameters</h3>
                    <div class="tech-stats">
                        <div class="tech-row">
                            <span class="tech-label">Model</span>
                            <span class="tech-value" id="tech-model">mistral:7b</span>
                        </div>
                        <div class="tech-row">
                            <span class="tech-label">Temperature</span>
                            <span class="tech-value">0.3</span>
                        </div>
                        <div class="tech-row">
                            <span class="tech-label">Top P</span>
                            <span class="tech-value">0.9</span>
                        </div>
                        <div class="tech-row">
                            <span class="tech-label">Repeat Penalty</span>
                            <span class="tech-value">1.1</span>
                        </div>
                        <div class="tech-row">
                            <span class="tech-label">Context Length</span>
                            <span class="tech-value">16384</span>
                        </div>
                    </div>
                </div>
                
                <div class="stat-card">
                    <h3>🌐 System Information</h3>
                    <div class="tech-stats">
                        <div class="tech-row">
                            <span class="tech-label">Backend</span>
                            <span class="tech-value">Ollama</span>
                        </div>
                        <div class="tech-row">
                            <span class="tech-label">Framework</span>
                            <span class="tech-value">LangChain</span>
                        </div>
                        <div class="tech-row">
                            <span class="tech-label">Server</span>
                            <span class="tech-value">Flask</span>
                        </div>
                        <div class="tech-row">
                            <span class="tech-label">Port</span>
                            <span class="tech-value">8090</span>
                        </div>
                        <div class="tech-row">
                            <span class="tech-label">Status</span>
                            <span class="tech-value">🟢 Active</span>
                        </div>
                    </div>
                </div>

                <div class="stat-card">
                    <h3>📋 RAG Configuration</h3>
                    <div class="tech-stats">
                        <div class="tech-row">
                            <span class="tech-label">Search Type</span>
                            <span class="tech-value">Semantic + Keyword</span>
                        </div>
                        <div class="tech-row">
                            <span class="tech-label">Context Lines</span>
                            <span class="tech-value">±3</span>
                        </div>
                        <div class="tech-row">
                            <span class="tech-label">Max Results</span>
                            <span class="tech-value">3</span>
                        </div>
                        <div class="tech-row">
                            <span class="tech-label">Supported Formats</span>
                            <span class="tech-value">PDF, TXT</span>
                        </div>
                        <div class="tech-row">
                            <span class="tech-label">Auto Reload</span>
                            <span class="tech-value">✅ Enabled</span>
                        </div>
                    </div>
                </div>

                <div class="stat-card">
                    <h3>🔄 Model Management</h3>
                    <div class="tech-stats">
                        <div class="tech-row">
                            <span class="tech-label">Available Models</span>
                            <span class="tech-value" id="available-models">Loading...</span>
                        </div>
                        <div class="tech-row">
                            <span class="tech-label">Download Status</span>
                            <span class="tech-value" id="download-status">Mistral:7B (Downloading...)</span>
                        </div>
                    </div>
                    <button onclick="checkModelStatus()" style="margin-top: 15px;">🔄 Refresh Model Status</button>
                    <button onclick="switchModel()" style="margin-top: 15px;">🔄 Switch Model</button>
                </div>
            </div>
        </div>
        
        <script>
            function openTab(evt, tabName) {
                var i, tabcontent, tabs;
                tabcontent = document.getElementsByClassName("tab-content");
                for (i = 0; i < tabcontent.length; i++) {
                    tabcontent[i].classList.remove("active");
                }
                tabs = document.getElementsByClassName("tab");
                for (i = 0; i < tabs.length; i++) {
                    tabs[i].classList.remove("active");
                }
                document.getElementById(tabName).classList.add("active");
                evt.currentTarget.classList.add("active");
            }

            // Chat functionality
            async function sendMessage() {
                const input = document.getElementById('message-input');
                const message = input.value.trim();
                if (!message) return;
                
                addMessage(message, 'user');
                input.value = '';
                
                const thinkingId = addMessage('🤔 Agent is thinking...', 'agent');
                
                try {
                    // Get current mode
                    const modeResponse = await fetch('/get-mode');
                    const modeData = await modeResponse.json();
                    const currentMode = modeData.mode;
                    
                    // Prepare request payload
                    let requestPayload = {
                        message: message,
                        mode: currentMode
                    };
                    
                    // Add advanced parameters if in advanced mode
                    if (currentMode === 'advanced') {
                        const tempSlider = document.getElementById('temp-slider');
                        const contextSlider = document.getElementById('context-slider');
                        const promptStrategy = document.getElementById('prompt-strategy');
                        const responseMode = document.getElementById('response-mode');
                        
                        if (tempSlider && contextSlider && promptStrategy && responseMode) {
                            requestPayload.temperature = parseFloat(tempSlider.value);
                            requestPayload.max_context = parseInt(contextSlider.value);
                            requestPayload.prompt_strategy = promptStrategy.value;
                            requestPayload.response_mode = responseMode.value;
                        }
                    }
                    
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(requestPayload)
                    });
                    const data = await response.json();
                    
                    document.getElementById(thinkingId).remove();
                    addMessage(data.response, 'agent');
                } catch (error) {
                    document.getElementById(thinkingId).remove();
                    addMessage('Error: Could not get response', 'agent');
                }
            }
            
            function addMessage(text, sender) {
                const container = document.getElementById('chat-container');
                const messageDiv = document.createElement('div');
                const messageId = 'msg-' + Date.now();
                messageDiv.id = messageId;
                messageDiv.className = 'message ' + sender;
                messageDiv.textContent = text;
                container.appendChild(messageDiv);
                container.scrollTop = container.scrollHeight;
                return messageId;
            }

            // File upload functionality
            document.getElementById('file-input').addEventListener('change', uploadFiles);
            
            const uploadArea = document.getElementById('upload-area');
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });
            
            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });
            
            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                const files = e.dataTransfer.files;
                uploadFiles({target: {files: files}});
            });

            async function uploadFiles(event) {
                const files = event.target.files;
                for (let file of files) {
                    const formData = new FormData();
                    formData.append('file', file);
                    
                    try {
                        const response = await fetch('/upload', {
                            method: 'POST',
                            body: formData
                        });
                        
                        if (response.ok) {
                            alert(`✅ ${file.name} uploaded successfully!`);
                            location.reload();
                        } else {
                            alert(`❌ Failed to upload ${file.name}`);
                        }
                    } catch (error) {
                        alert(`❌ Error uploading ${file.name}: ${error.message}`);
                    }
                }
            }

            async function deleteFile(filename) {
                if (!confirm(`Are you sure you want to delete ${filename}?`)) return;
                
                try {
                    const response = await fetch(`/delete/${filename}`, {method: 'DELETE'});
                    if (response.ok) {
                        alert(`✅ ${filename} deleted successfully!`);
                        location.reload();
                    } else {
                        alert(`❌ Failed to delete ${filename}`);
                    }
                } catch (error) {
                    alert(`❌ Error deleting ${filename}: ${error.message}`);
                }
            }

            async function reloadKnowledgeBase() {
                try {
                    const response = await fetch('/reload', {method: 'POST'});
                    if (response.ok) {
                        alert('✅ Knowledge base reloaded successfully!');
                        location.reload();
                    } else {
                        alert('❌ Failed to reload knowledge base');
                    }
                } catch (error) {
                    alert(`❌ Error reloading: ${error.message}`);
                }
            }

            // Theme toggle functionality
            function toggleTheme() {
                const body = document.body;
                const themeIcon = document.getElementById('10-theme-icon');
                const themeText = document.getElementById('11-theme-text');
                
                if (body.getAttribute('data-theme') === 'dark') {
                    body.removeAttribute('data-theme');
                    themeIcon.textContent = '🌙';
                    themeText.textContent = 'Dark Mode';
                    localStorage.setItem('theme', 'light');
                } else {
                    body.setAttribute('data-theme', 'dark');
                    themeIcon.textContent = '☀️';
                    themeText.textContent = 'Light Mode';
                    localStorage.setItem('theme', 'dark');
                }
            }

            // Mode switching functionality
            function toggleMode() {
                fetch('/get-mode')
                    .then(response => response.json())
                    .then(data => {
                        const newMode = data.mode === 'simple' ? 'advanced' : 'simple';
                        
                        fetch('/set-mode', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ mode: newMode })
                        })
                        .then(response => response.json())
                        .then(result => {
                            if (result.success) {
                                updateModeUI(result.mode);
                                // Show mode change notification
                                addMessage('system', `Switched to ${result.mode.charAt(0).toUpperCase() + result.mode.slice(1)} Mode`);
                            }
                        })
                        .catch(error => {
                            console.error('Error switching mode:', error);
                            addMessage('error', 'Failed to switch mode');
                        });
                    });
            }

            function updateModeUI(mode) {
                const modeIcon = document.getElementById('mode-icon');
                const modeText = document.getElementById('mode-text');
                
                if (mode === 'advanced') {
                    modeIcon.textContent = '🔬';
                    modeText.textContent = 'Advanced';
                    document.body.setAttribute('data-mode', 'advanced');
                    
                    // Show advanced features
                    showAdvancedFeatures();
                } else {
                    modeIcon.textContent = '🔰';
                    modeText.textContent = 'Simple';
                    document.body.setAttribute('data-mode', 'simple');
                    
                    // Hide advanced features
                    hideAdvancedFeatures();
                }
                
                // Save mode preference
                localStorage.setItem('mode', mode);
            }

            function showAdvancedFeatures() {
                // Add advanced mode features to the UI
                const advancedElements = document.querySelectorAll('.advanced-only');
                advancedElements.forEach(el => el.style.display = 'block');
                
                // Add advanced prompt controls to chat tab
                addAdvancedPromptControls();
            }

            function hideAdvancedFeatures() {
                // Hide advanced mode features
                const advancedElements = document.querySelectorAll('.advanced-only');
                advancedElements.forEach(el => el.style.display = 'none');
                
                // Remove advanced prompt controls
                removeAdvancedPromptControls();
            }

            function addAdvancedPromptControls() {
                const chatTab = document.getElementById('chat-tab');
                const chatStatus = document.getElementById('17-chat-status');
                
                if (!document.getElementById('advanced-controls')) {
                    const advancedControls = document.createElement('div');
                    advancedControls.id = 'advanced-controls';
                    advancedControls.className = 'advanced-only';
                    advancedControls.innerHTML = `
                        <h4>🔬 Advanced AI Controls</h4>
                        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; margin-top: 0.5rem;">
                            <div>
                                <label>Temperature: <span id="temp-value">0.3</span></label>
                                <input type="range" id="temp-slider" min="0" max="1" step="0.1" value="0.3" onchange="updateParameter('temperature', this.value)">
                                <small style="color: var(--text-muted);">Creativity level</small>
                            </div>
                            <div>
                                <label>Max Context: <span id="context-value">16384</span></label>
                                <input type="range" id="context-slider" min="2048" max="32768" step="2048" value="16384" onchange="updateParameter('context', this.value)">
                                <small style="color: var(--text-muted);">Memory size</small>
                            </div>
                            <div>
                                <label>Response Mode:</label>
                                <select id="response-mode" onchange="updateResponseMode(this.value)">
                                    <option value="standard">Standard</option>
                                    <option value="fast">Fast & Light</option>
                                    <option value="detailed">Detailed & Deep</option>
                                </select>
                                <small style="color: var(--text-muted);">Speed vs quality</small>
                            </div>
                        </div>
                        <div style="margin-top: 1rem;">
                            <label>Prompt Strategy:</label>
                            <select id="prompt-strategy" onchange="updatePromptStrategy(this.value)">
                                <option value="simple">Simple RAG - Direct answers</option>
                                <option value="enhanced">Enhanced Context - Comprehensive analysis</option>
                                <option value="analytical">Analytical - Structured reasoning</option>
                                <option value="creative">Creative - Innovative thinking</option>
                            </select>
                            <small style="color: var(--text-muted);">How the AI approaches your question</small>
                        </div>
                        <div style="margin-top: 1rem; padding: 0.5rem; background: rgba(156, 39, 176, 0.1); border-radius: 4px; border-left: 3px solid var(--advanced-accent, var(--accent-secondary));">
                            <small><strong>Advanced Mode Active:</strong> Enhanced reasoning, configurable parameters, and specialized prompt strategies.</small>
                        </div>
                    `;
                    
                    // Insert after the status div
                    chatStatus.insertAdjacentElement('afterend', advancedControls);
                }
            }

            function removeAdvancedPromptControls() {
                const advancedControls = document.getElementById('advanced-controls');
                if (advancedControls) {
                    advancedControls.remove();
                }
            }

            function updateParameter(param, value) {
                document.getElementById(`${param === 'temperature' ? 'temp' : 'context'}-value`).textContent = value;
            }

            function updatePromptStrategy(strategy) {
                console.log('Prompt strategy changed to:', strategy);
                // Visual feedback for strategy change
                const select = document.getElementById('prompt-strategy');
                select.style.borderColor = 'var(--advanced-accent, var(--accent-secondary))';
                setTimeout(() => {
                    select.style.borderColor = '';
                }, 500);
            }

            function updateResponseMode(mode) {
                console.log('Response mode changed to:', mode);
                const select = document.getElementById('response-mode');
                
                // Update UI based on mode
                if (mode === 'fast') {
                    select.style.background = 'rgba(0, 200, 81, 0.2)';
                    addMessage('🚀 Fast mode enabled - Optimized for speed', 'system');
                } else if (mode === 'detailed') {
                    select.style.background = 'rgba(156, 39, 176, 0.2)';
                    addMessage('🔬 Detailed mode enabled - Enhanced analysis', 'system');
                } else {
                    select.style.background = '';
                    addMessage('⚖️ Standard mode enabled - Balanced response', 'system');
                }
            }

            // Load saved mode
            function loadMode() {
                const savedMode = localStorage.getItem('mode') || 'simple';
                fetch('/set-mode', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ mode: savedMode })
                })
                .then(response => response.json())
                .then(result => {
                    if (result.success) {
                        updateModeUI(result.mode);
                    }
                });
            }

            // Load saved theme
            function loadTheme() {
                const savedTheme = localStorage.getItem('theme');
                if (savedTheme === 'dark') {
                    document.body.setAttribute('data-theme', 'dark');
                    document.getElementById('10-theme-icon').textContent = '☀️';
                    document.getElementById('11-theme-text').textContent = 'Light Mode';
                }
            }

            // Model management functions
            async function checkModelStatus() {
                try {
                    const response = await fetch('/model-status');
                    const data = await response.json();
                    document.getElementById('available-models').textContent = data.models.join(', ');
                    document.getElementById('download-status').textContent = data.download_status;
                } catch (error) {
                    console.error('Error checking model status:', error);
                }
            }

            async function switchModel() {
                try {
                    const response = await fetch('/switch-model', {method: 'POST'});
                    const data = await response.json();
                    if (response.ok) {
                        alert('✅ ' + data.message);
                        const modelName = data.new_model.split(' ')[0];
                        const modelParam = data.new_model.split(' ')[1] || '';
                        document.getElementById('6-current-model').textContent = modelName;
                        document.getElementById('7-model-params').textContent = modelParam;
                        document.getElementById('model-display').textContent = data.new_model;
                        document.getElementById('tech-model').textContent = data.new_model.toLowerCase().replace(' ', ':');
                        
                        // Update model tags based on the model
                        updateModelTags(modelName, modelParam);
                    } else {
                        alert('❌ ' + data.error);
                    }
                } catch (error) {
                    alert(`❌ Error switching model: ${error.message}`);
                }
            }

            // Update model tags based on current model
            function updateModelTags(modelName, modelParam) {
                const tagsContainer = document.getElementById('8-model-tags');
                let tags = [];
                
                // Define tags for different models
                if (modelName.toLowerCase().includes('llama')) {
                    if (modelParam === '3B') {
                        tags = ['Better Reasoning', 'Nimble', 'Efficient'];
                    } else if (modelParam === '1B') {
                        tags = ['Fast', 'Lightweight', 'Basic'];
                    }
                } else if (modelName.toLowerCase().includes('mistral')) {
                    if (modelParam === '7B') {
                        tags = ['Superior Reasoning', 'Versatile', 'Advanced'];
                    }
                } else if (modelName.toLowerCase().includes('qwen')) {
                    if (modelParam === '72B') {
                        tags = ['Expert Reasoning', 'Comprehensive', 'Enterprise'];
                    }
                }
                
                // Update the tags HTML
                tagsContainer.innerHTML = tags.map(tag => 
                    `<span class="tag">${tag}</span>`
                ).join('');
            }

            // Initialize on page load
            document.addEventListener('DOMContentLoaded', function() {
                loadTheme();
                loadMode();
                checkModelStatus();
                updateModelTags('Mistral', '7B'); // Initialize with current model
            });
        </script>
        
        <footer style="margin-top: 3rem; padding: 2rem 0; text-align: center; border-top: 1px solid var(--border); color: var(--text-muted); font-size: 0.85rem;">
            <p>Made by <strong style="color: var(--accent-primary);">pingomatic</strong> © 2025</p>
        </footer>
    </body>
    </html>
    """
    return render_template_string(html, stats=stats)

@app.route('/chat', methods=['POST'])
def chat():
    """API endpoint for chat interface with mode-aware processing"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        mode = data.get('mode', 'simple')
        
        if not user_message:
            return jsonify({'response': 'Please provide a message.'})
        
        # Handle different modes  
        global agent
        
        if mode == 'advanced' and hasattr(agent, 'run_advanced'):
            # Extract advanced parameters
            temperature = data.get('temperature', 0.3)
            max_context = data.get('max_context', 16384)
            prompt_strategy = data.get('prompt_strategy', 'simple')
            response_mode = data.get('response_mode', 'standard')
            
            # Create fast agent if requested
            if response_mode == 'fast' and not getattr(agent, 'fast_mode', False):
                agent = SimpleRAGAgent(fast_mode=True)
            elif response_mode == 'standard' and getattr(agent, 'fast_mode', False):
                agent = SimpleRAGAgent(fast_mode=False)

            # Use advanced agent processing if supported
            response = agent.run_advanced(
                user_message,
                temperature=temperature,
                max_context=max_context,
                prompt_strategy=prompt_strategy
            )
        else:
            # Use simple mode processing or fallback when advanced not available
            response = agent.run(user_message)
        
        return jsonify({'response': response})
        
    except Exception as e:
        print(f"Chat error: {str(e)}")
        return jsonify({'response': f'Error: {str(e)}'})

@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload files to the knowledge base"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        # Ensure upload folder exists
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Check if file already exists
        if os.path.exists(filepath):
            return jsonify({'error': f'File {filename} already exists'}), 400
        
        file.save(filepath)
        
        # Reload the knowledge base to include the new file
        global agent
        agent = SimpleRAGAgent()
        
        return jsonify({'message': f'File {filename} uploaded successfully'})
    
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    """Delete a file from the knowledge base"""
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        os.remove(filepath)
        
        # Reload the knowledge base after deletion
        global agent
        agent = SimpleRAGAgent()
        
        return jsonify({'message': f'File {filename} deleted successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reload', methods=['POST'])
def reload_knowledge_base():
    """Reload the knowledge base"""
    try:
        global agent
        agent = SimpleRAGAgent()
        
        stats = get_file_stats()
        return jsonify({
            'message': 'Knowledge base reloaded successfully',
            'stats': stats
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/model-status', methods=['GET'])
def model_status():
    """Get available models and download status"""
    try:
        # Check available models
        result = os.popen('ollama list').read()
        models = []
        for line in result.split('\n')[1:]:  # Skip header
            if line.strip():
                model_name = line.split()[0]
                if model_name:
                    models.append(model_name)
        
        # Check if Mistral:7B is available
        download_status = "Mistral:7B (Available)" if "mistral:7b" in models else "Mistral:7B (Downloading...)"
        
        return jsonify({
            'models': models,
            'download_status': download_status,
            'current_model': 'mistral:7b'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/switch-model', methods=['POST'])
def switch_model():
    """Switch to a different model"""
    try:
        # Check if Mistral:7B is available
        result = os.popen('ollama list').read()
        if "mistral:7b" in result.lower():
            # Update the RAG agent to use Mistral:7B
            global agent
            agent.llm.model = "mistral:7b"
            return jsonify({
                'message': 'Successfully switched to Mistral 7B',
                'new_model': 'Mistral 7B'
            })
        else:
            return jsonify({'error': 'Mistral:7B is not available yet. Please wait for download to complete.'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting RAG Agent Management System on http://127.0.0.1:8090")
    print("📚 Knowledge base loaded with", len(agent.knowledge_base), "characters")
    print("🌐 Access the web interface at:")
    print("   - Local: http://127.0.0.1:8090")
    app.run(debug=False, port=8090, host='127.0.0.1', threaded=True)
