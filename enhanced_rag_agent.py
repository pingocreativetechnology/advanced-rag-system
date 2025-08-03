"""
Enhanced RAG Agent v2

Features:
  - Multi-agent coordination (AgentManager)
  - Improved document processing (DocumentProcessor)
  - Context window management (ContextManager)
  - Performance monitoring and logging decorators
  - Configuration management via environment variables
"""
import os
import time
import logging
from typing import List, Dict, Any, Callable
from dataclasses import dataclass, field
from collections import deque

try:
    from rag_agent import SimpleRAGAgent
except ImportError as e:
    logging.error(f"Could not import SimpleRAGAgent: {e}")
    # Create a mock agent for testing
    class SimpleRAGAgent:
        def __init__(self):
            self.knowledge_base = "Mock knowledge base for testing"
        def run(self, query):
            return f"Mock response to: {query}"

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def timeit(func: Callable) -> Callable:
    """Decorator to measure execution time of methods"""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logging.info(f"{func.__name__} executed in {elapsed:.3f}s")
        return result
    return wrapper


@dataclass
class Config:
    """Configuration for enhanced RAG agent loaded from environment"""
    AGENT_TYPES: List[str] = field(default_factory=lambda: os.getenv("AGENT_TYPES", "default").split(","))
    CONTEXT_WINDOW: int = int(os.getenv("CONTEXT_WINDOW", "5"))
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))


@dataclass
class DocumentProcessor:
    """Split documents into overlapping chunks for retrieval"""
    chunk_size: int = Config.CHUNK_SIZE
    overlap: int = Config.CHUNK_OVERLAP

    @timeit
    def process_document(self, text: str) -> List[str]:
        """Return list of text chunks with specified overlap"""
        if not text:
            return []
        tokens = text.split()
        chunks: List[str] = []
        step = self.chunk_size - self.overlap
        for i in range(0, max(len(tokens) - self.overlap, 0), step):
            chunk = tokens[i : i + self.chunk_size]
            chunks.append(" ".join(chunk))
        return chunks


@dataclass
class ContextManager:
    """Manage rolling context window for conversation history"""
    window_size: int = Config.CONTEXT_WINDOW
    history: deque = field(default_factory=lambda: deque(maxlen=Config.CONTEXT_WINDOW))

    def manage_context(self, conversation_history: List[str]) -> str:
        """Add messages to context window and return concatenated context"""
        for msg in conversation_history:
            self.history.append(msg)
        return "\n".join(self.history)


@dataclass
class AgentManager:
    """Coordinate routing between multiple agents based on query"""
    agents: Dict[str, SimpleRAGAgent] = field(default_factory=dict)

    def route_query(self, query: str) -> SimpleRAGAgent:
        """Select an agent based on simple keyword routing"""
        q = query.lower()
        # Example routing logic: choose specialized agent if keyword present
        for key, agent in self.agents.items():
            if key in q:
                logging.info(f"Routing to agent '{key}' for query")
                return agent
        # Fallback to default
        return self.agents.get('default')

    @timeit
    def run(self, query: str) -> str:
        """Route and execute query on chosen agent"""
        agent = self.route_query(query)
        if not agent:
            raise ValueError("No agent available to handle the query")
        return agent.run(query)


class ImprovedRAGAgent:
    """Enhanced agent combining document processing, context, and routing"""
    def __init__(self):
        # Initialize core components
        self.processor = DocumentProcessor()
        self.context_mgr = ContextManager()
        # Setup agent instances with error handling
        try:
            default_agent = SimpleRAGAgent(fast_mode=True)
            logging.info("✅ Successfully initialized SimpleRAGAgent in fast mode")
        except Exception as e:
            logging.error(f"Failed to initialize SimpleRAGAgent: {e}")
            # Create a fallback mock agent
            default_agent = type('MockAgent', (), {
                'run': lambda self, query: f"Error: Could not connect to LLM service. Query was: {query}",
                'knowledge_base': "Service temporarily unavailable"
            })()
        self.manager = AgentManager(agents={'default': default_agent})

    def ingest_document(self, text: str) -> None:
        """Process and store document chunks (stub for embedding)"""
        chunks = self.processor.process_document(text)
        # TODO: integrate embedding/storage pipeline
        logging.info(f"Ingested document into {len(chunks)} chunks")

    def chat(self, query: str, history: List[str]) -> str:
        """Manage context and process a user query end-to-end"""
        # Update context window
        _ = self.context_mgr.manage_context(history + [query])

        # Route query and return response
        return self.manager.run(query)

    def run(self, user_input: str) -> str:
        """Legacy API compatibility: simple run interface"""
        return self.chat(user_input, [])


if __name__ == '__main__':
    # Check if we should run in web mode
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--web':
        # Web server mode
        from flask import Flask, request, jsonify
        
        app = Flask(__name__)
        agent = ImprovedRAGAgent()
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8091
        
        @app.route('/')
        def home():
            return '''
            <h1>🔧 Enhanced RAG Agent v2</h1>
            <p>Enhanced agent with multi-agent coordination, improved document processing, and context management.</p>
            <p>Send POST requests to /chat with JSON: {"message": "your question"}</p>
            <form method="post" action="/chat">
                <input type="text" name="message" placeholder="Ask me anything..." style="width: 300px; margin: 10px;">
                <input type="submit" value="Send">
            </form>
            '''
        
        @app.route('/chat', methods=['POST'])
        def chat():
            try:
                if request.is_json:
                    data = request.get_json()
                    message = data.get('message', '')
                else:
                    message = request.form.get('message', '')
                
                if not message:
                    return jsonify({'error': 'No message provided'})
                
                logging.info(f"Processing query: {message}")
                response = agent.run(message)
                logging.info(f"Generated response: {response[:100]}...")
                return jsonify({'response': response})
            except Exception as e:
                logging.error(f"Chat error: {str(e)}")
                return jsonify({'error': f'Internal server error: {str(e)}'}), 500
        
        logging.info(f"🚀 Starting Enhanced RAG Agent v2 web server on http://127.0.0.1:{port}")
        app.run(debug=False, port=port, host='127.0.0.1', threaded=True)
    else:
        # Console mode (default)
        logging.info("🔧 Running Improved RAG Agent v2 interactive console")
        agent = ImprovedRAGAgent()
        history: List[str] = []
        while True:
            try:
                query = input("> ")
                if query.lower() in ('exit', 'quit'):
                    break
                resp = agent.chat(query, history)
                print(resp)
                history.append(query)
            except Exception as err:
                logging.error(f"Error: {err}")
