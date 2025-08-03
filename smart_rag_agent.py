#!/usr/bin/env python3
"""
Smart RAG Agent with Vector Database
Uses ChromaDB for semantic search and document embeddings
"""
import os
import logging
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import PyPDF2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartRAGAgent:
    def __init__(self, fast_mode=False):
        """Initialize Smart RAG Agent with vector database"""
        self.fast_mode = fast_mode
        model = "llama3.2:1b" if fast_mode else "mistral:7b"
        
        # Initialize LLM
        self.llm = OllamaLLM(
            model=model,
            temperature=0.3,
            top_p=0.9,
            repeat_penalty=1.1,
            num_ctx=8192 if fast_mode else 16384
        )
        
        # Initialize embeddings
        self.embeddings = OllamaEmbeddings(
            model="nomic-embed-text",  # Excellent for RAG
            base_url="http://localhost:11434"
        )
        
        # Initialize ChromaDB
        self.persist_directory = "./chroma_db"
        self.vectorstore = None
        self.qa_chain = None
        
        logger.info(f"🚀 Initialized Smart RAG Agent with {model}")
        self.setup_vectorstore()
    
    def setup_vectorstore(self):
        """Setup ChromaDB vector store"""
        try:
            # Check if we have existing vectorstore
            if os.path.exists(self.persist_directory):
                logger.info("📚 Loading existing vector database...")
                self.vectorstore = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings
                )
            else:
                logger.info("🆕 Creating new vector database...")
                self.vectorstore = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings
                )
                self.load_and_index_documents()
            
            self.setup_qa_chain()
            
        except Exception as e:
            logger.error(f"❌ Error setting up vectorstore: {e}")
            logger.info("📝 Falling back to basic document loading...")
            self.fallback_setup()
    
    def load_and_index_documents(self):
        """Load and index documents from doccydocs folder"""
        if not os.path.exists('doccydocs'):
            logger.warning("📁 No doccydocs folder found")
            return
        
        documents = []
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        logger.info("📖 Loading documents...")
        for filename in os.listdir('doccydocs'):
            file_path = os.path.join('doccydocs', filename)
            
            try:
                if filename.endswith('.pdf'):
                    loader = PyPDFLoader(file_path)
                    docs = loader.load()
                    documents.extend(docs)
                    logger.info(f"✅ Loaded PDF: {filename}")
                
                elif filename.endswith('.txt'):
                    loader = TextLoader(file_path)
                    docs = loader.load()
                    documents.extend(docs)
                    logger.info(f"✅ Loaded TXT: {filename}")
                    
            except Exception as e:
                logger.error(f"❌ Error loading {filename}: {e}")
        
        if documents:
            logger.info(f"🔄 Splitting {len(documents)} documents into chunks...")
            splits = text_splitter.split_documents(documents)
            logger.info(f"📦 Created {len(splits)} document chunks")
            
            logger.info("🔄 Creating embeddings and storing in vector database...")
            self.vectorstore.add_documents(splits)
            self.vectorstore.persist()
            logger.info("✅ Documents indexed successfully!")
        else:
            logger.warning("⚠️ No documents found to index")
    
    def setup_qa_chain(self):
        """Setup the QA retrieval chain"""
        # Custom prompt template for better responses
        template = """You are a helpful AI assistant. Use the following context to answer the question accurately and comprehensively.

Context:
{context}

Question: {question}

Instructions:
- Answer based on the provided context
- If the context doesn't contain enough information, say so clearly
- Be concise but thorough
- Use specific details from the context when available

Answer:"""

        PROMPT = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        
        # Setup retrieval QA chain
        retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}  # Retrieve top 3 most relevant chunks
        )
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": PROMPT},
            return_source_documents=True
        )
        
        logger.info("🔗 QA chain setup complete")
    
    def fallback_setup(self):
        """Fallback to basic document loading if vector DB fails"""
        self.knowledge_base = self.load_basic_knowledge_base()
    
    def load_basic_knowledge_base(self):
        """Load knowledge base from text file and doccydocs folder (fallback)"""
        knowledge_content = ""
        
        if os.path.exists('knowledge_base.txt'):
            with open('knowledge_base.txt', 'r') as f:
                knowledge_content += f.read() + "\n\n"
        
        if os.path.exists('doccydocs'):
            for filename in os.listdir('doccydocs'):
                file_path = os.path.join('doccydocs', filename)
                if filename.endswith('.pdf'):
                    try:
                        with open(file_path, 'rb') as file:
                            pdf_reader = PyPDF2.PdfReader(file)
                            text = ""
                            for page in pdf_reader.pages:
                                text += page.extract_text() + "\n"
                            knowledge_content += f"\n--- {filename} ---\n{text}\n"
                    except Exception as e:
                        logger.error(f"Error extracting {filename}: {e}")
        
        return knowledge_content
    
    def run(self, query: str) -> str:
        """Process query using vector search or fallback"""
        try:
            if self.qa_chain:
                logger.info("🔍 Using vector search...")
                result = self.qa_chain.invoke({"query": query})
                
                # Extract answer and sources
                answer = result.get("result", "")
                sources = result.get("source_documents", [])
                
                # Add source information
                if sources:
                    source_info = "\n\n📚 Sources:"
                    for i, doc in enumerate(sources[:2], 1):  # Show top 2 sources
                        source = doc.metadata.get('source', 'Unknown')
                        source_info += f"\n{i}. {os.path.basename(source)}"
                    answer += source_info
                
                return answer
            else:
                logger.info("📝 Using basic search...")
                return self.basic_search(query)
                
        except Exception as e:
            logger.error(f"❌ Error in query processing: {e}")
            return f"I encountered an error processing your question: {str(e)}"
    
    def basic_search(self, query: str) -> str:
        """Basic keyword search fallback"""
        if not hasattr(self, 'knowledge_base') or not self.knowledge_base:
            return "I don't have access to any knowledge base to answer your question."
        
        # Simple keyword matching
        query_words = query.lower().split()
        relevant_lines = []
        
        for line in self.knowledge_base.split('\n'):
            if any(word in line.lower() for word in query_words):
                relevant_lines.append(line.strip())
        
        if relevant_lines:
            context = '\n'.join(relevant_lines[:5])  # Top 5 relevant lines
            prompt = f"Based on this context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
            return self.llm.invoke(prompt)
        else:
            return f"I couldn't find relevant information about '{query}' in my knowledge base."
    
    def add_document(self, file_path: str):
        """Add a new document to the vector database"""
        if not self.vectorstore:
            logger.error("❌ Vector database not available")
            return False
        
        try:
            if file_path.endswith('.pdf'):
                loader = PyPDFLoader(file_path)
            elif file_path.endswith('.txt'):
                loader = TextLoader(file_path)
            else:
                logger.error(f"❌ Unsupported file type: {file_path}")
                return False
            
            docs = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            splits = text_splitter.split_documents(docs)
            
            self.vectorstore.add_documents(splits)
            self.vectorstore.persist()
            
            logger.info(f"✅ Added {file_path} to vector database")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error adding document: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database"""
        try:
            if self.vectorstore:
                collection = self.vectorstore._collection
                count = collection.count()
                return {
                    "vector_db": "ChromaDB",
                    "total_chunks": count,
                    "embedding_model": "nomic-embed-text",
                    "status": "✅ Active"
                }
            else:
                return {
                    "vector_db": "None",
                    "total_chunks": 0,
                    "embedding_model": "None",
                    "status": "❌ Fallback mode"
                }
        except Exception as e:
            return {
                "vector_db": "ChromaDB",
                "total_chunks": "Unknown",
                "embedding_model": "nomic-embed-text", 
                "status": f"❌ Error: {e}"
            }

if __name__ == '__main__':
    # Check if nomic-embed-text model is available
    import subprocess
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if 'nomic-embed-text' not in result.stdout:
            logger.info("📥 Downloading nomic-embed-text model...")
            subprocess.run(['ollama', 'pull', 'nomic-embed-text'], check=True)
            logger.info("✅ Downloaded nomic-embed-text model")
    except Exception as e:
        logger.warning(f"⚠️ Could not check/download embedding model: {e}")
    
    # Interactive mode
    agent = SmartRAGAgent()
    logger.info("🤖 Smart RAG Agent ready! Type 'quit' to exit.")
    
    while True:
        try:
            query = input("\n> ")
            if query.lower() in ('quit', 'exit'):
                break
            
            response = agent.run(query)
            print(f"\n🤖 {response}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Error: {e}")
    
    logger.info("👋 Goodbye!")