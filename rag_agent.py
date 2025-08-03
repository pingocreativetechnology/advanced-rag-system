from langchain_ollama import OllamaLLM
import os
import re
import errno
import PyPDF2

class SimpleRAGAgent:
    def __init__(self, fast_mode=False):
        """Initialize a simple RAG agent without heavy dependencies"""
        # Use lighter model for faster responses if requested
        model = "llama3.2:1b" if fast_mode else "mistral:7b"
        
        self.llm = OllamaLLM(
            model=model,
            temperature=0.3,
            top_p=0.9,
            repeat_penalty=1.1,
            num_ctx=8192 if fast_mode else 16384  # Smaller context for speed
        )
        self.fast_mode = fast_mode
        self.knowledge_base = self.load_knowledge_base()
        print(f"🚀 Initialized {'Fast' if fast_mode else 'Standard'} RAG Agent with {model}")
    
    def extract_pdf_text(self, pdf_path):
        """Extract text from a PDF file"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {e}")
            return ""
    
    def load_knowledge_base(self):
        """Load knowledge base from text file and doccydocs folder (including PDFs)"""
        knowledge_content = ""
        
        # Load the main knowledge base text file
        if os.path.exists('knowledge_base.txt'):
            with open('knowledge_base.txt', 'r') as f:
                knowledge_content += f.read() + "\n\n"
        
        # Load documents from doccydocs folder
        if os.path.exists('doccydocs'):
            print("Loading documents from doccydocs folder...")
            for filename in os.listdir('doccydocs'):
                file_path = os.path.join('doccydocs', filename)
                
                if filename.endswith('.txt'):
                    try:
                        with open(file_path, 'r') as f:
                            knowledge_content += f"=== {filename} ===\n"
                            knowledge_content += f.read() + "\n\n"
                        print(f"✓ Loaded text file: {filename}")
                    except Exception as e:
                        print(f"✗ Error reading {filename}: {e}")
                
                elif filename.endswith('.pdf'):
                    try:
                        pdf_text = self.extract_pdf_text(file_path)
                        if pdf_text.strip():
                            knowledge_content += f"=== {filename} ===\n"
                            knowledge_content += pdf_text + "\n\n"
                            print(f"✓ Loaded PDF file: {filename}")
                        else:
                            print(f"⚠ No text extracted from: {filename}")
                    except Exception as e:
                        print(f"✗ Error processing PDF {filename}: {e}")
        
        if knowledge_content:
            print(f"📚 Total knowledge base size: {len(knowledge_content)} characters")
        else:
            print("⚠ No knowledge base content loaded")
            
        return knowledge_content
    
    def search_knowledge(self, query: str) -> str:
        """Enhanced text search in knowledge base"""
        if not self.knowledge_base:
            return "No knowledge base available"
        
        # Convert to lowercase for case-insensitive search
        query_lower = query.lower()
        query_words = query_lower.split()
        
        # Find relevant sections with scoring
        relevant_sections = []
        lines = self.knowledge_base.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            score = 0
            
            # Score based on word matches
            for word in query_words:
                if word in line_lower:
                    score += 1
                    
            # Boost score for exact phrase matches
            if query_lower in line_lower:
                score += len(query_words)
            
            if score > 0:
                # Include more context - 3 lines before and after
                start = max(0, i-3)
                end = min(len(lines), i+4)
                context = '\n'.join(lines[start:end])
                relevant_sections.append((score, context, i))
        
        if relevant_sections:
            # Sort by score and return top matches
            relevant_sections.sort(key=lambda x: x[0], reverse=True)
            top_matches = [section[1] for section in relevant_sections[:4]]
            
            # Deduplicate similar sections
            unique_matches = []
            for match in top_matches:
                is_duplicate = False
                for existing in unique_matches:
                    if len(set(match.split()) & set(existing.split())) > len(match.split()) * 0.7:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    unique_matches.append(match)
            
            return '\n\n---\n\n'.join(unique_matches[:3])
        else:
            return "No relevant information found in knowledge base"
    
    def run(self, user_input: str) -> str:
        """Process user input with RAG context"""
        try:
            # Search knowledge base for relevant info
            context = self.search_knowledge(user_input)
            
            # Create enhanced prompt with better instructions
            prompt = f"""You are an intelligent AI assistant with access to a knowledge base. Please provide helpful, accurate, and detailed responses.

CONTEXT FROM KNOWLEDGE BASE:
{context}

USER QUESTION: {user_input}

INSTRUCTIONS:
- Use the provided context when relevant to answer the question
- If the context doesn't contain relevant information, use your general knowledge
- Be comprehensive but concise
- Provide specific details when available
- If you're unsure about something, say so rather than guessing

RESPONSE:"""
            
            print(f"DEBUG: Sending prompt to model: {prompt[:200]}...")
            response = self.llm.invoke(prompt)
            print(f"DEBUG: Model response: {response[:200]}...")
            
            return self.clean_for_voice(response)
            
        except Exception as e:
            print(f"ERROR in RAG agent: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return f"I encountered a technical error: {str(e)}. Please try again or contact support."
    
    def run_advanced(self, user_input: str, temperature: float = 0.3, max_context: int = 16384, prompt_strategy: str = 'simple') -> str:
        """Process user input with advanced RAG context and configurable parameters"""
        try:
            # Create a new LLM instance with custom parameters
            advanced_llm = OllamaLLM(
                model="mistral:7b",
                temperature=temperature,
                top_p=0.9,
                repeat_penalty=1.1,
                num_ctx=max_context
            )
            
            # Search knowledge base for relevant info
            context = self.search_knowledge(user_input)
            
            # Select prompt based on strategy
            prompt = self.get_advanced_prompt(user_input, context, prompt_strategy)
            
            print(f"DEBUG: Advanced mode - Strategy: {prompt_strategy}, Temp: {temperature}, Context: {max_context}")
            print(f"DEBUG: Sending advanced prompt to model: {prompt[:200]}...")
            
            response = advanced_llm.invoke(prompt)
            print(f"DEBUG: Advanced model response: {response[:200]}...")
            
            return self.clean_for_voice(response)
            
        except Exception as e:
            print(f"ERROR in advanced RAG agent: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            # Handle local LLM connection errors specifically
            if isinstance(e, ConnectionRefusedError) or getattr(e, 'errno', None) == errno.ECONNREFUSED:
                return (
                    "I’m unable to connect to the local LLM server. "
                    "Please ensure it’s running and accessible, then try again or contact support."
                )
            return f"I encountered a technical error in advanced mode: {str(e)}. Please try again or contact support."
    
    def get_advanced_prompt(self, user_input: str, context: str, strategy: str) -> str:
        """Generate prompts based on different strategies from rag_improvement_prompt.md concepts"""
        
        if strategy == 'enhanced':
            return f"""You are an advanced AI assistant with enhanced contextual understanding. You have access to a comprehensive knowledge base and should provide detailed, nuanced responses.

KNOWLEDGE BASE CONTEXT:
{context}

USER QUERY: {user_input}

ENHANCED INSTRUCTIONS:
- Analyze the query for implicit requirements and context
- Use multi-layered reasoning to connect information across different sources
- Provide comprehensive answers with supporting evidence
- Consider alternative interpretations and edge cases
- Structure your response with clear reasoning chains
- When relevant, explain the methodology behind your conclusions
- Identify any limitations or assumptions in your response

Please provide a thorough, well-reasoned response:"""

        elif strategy == 'analytical':
            return f"""You are a specialized analytical AI assistant focused on systematic analysis and structured reasoning. Break down complex problems methodically.

KNOWLEDGE BASE CONTEXT:
{context}

ANALYTICAL QUERY: {user_input}

ANALYTICAL FRAMEWORK:
1. PROBLEM DECOMPOSITION:
   - Identify key components and relationships
   - Determine relevant variables and constraints
   - Map dependencies and causal relationships

2. EVIDENCE ANALYSIS:
   - Evaluate source credibility and relevance
   - Identify patterns, trends, and anomalies
   - Cross-reference multiple data points

3. SYSTEMATIC REASONING:
   - Apply logical frameworks and methodologies
   - Consider multiple perspectives and scenarios
   - Validate conclusions against available evidence

4. SYNTHESIS AND RECOMMENDATIONS:
   - Integrate findings into coherent insights
   - Propose actionable recommendations
   - Identify areas requiring further investigation

Provide your analytical response following this structured approach:"""

        elif strategy == 'creative':
            return f"""You are a creative and innovative AI assistant that thinks beyond conventional boundaries. Use imaginative approaches while maintaining accuracy.

KNOWLEDGE BASE CONTEXT:
{context}

CREATIVE CHALLENGE: {user_input}

CREATIVE INSTRUCTIONS:
- Explore unconventional angles and perspectives
- Generate novel connections between seemingly unrelated concepts
- Use analogies, metaphors, and creative explanations
- Propose innovative solutions or approaches
- Think outside traditional frameworks while remaining grounded in facts
- Encourage exploration of possibilities and "what-if" scenarios
- Balance creativity with practical applicability

Let your creativity flow while providing valuable insights:"""

        else:  # simple strategy (default)
            return f"""You are an intelligent AI assistant with access to a knowledge base. Please provide helpful, accurate, and detailed responses.

CONTEXT FROM KNOWLEDGE BASE:
{context}

USER QUESTION: {user_input}

INSTRUCTIONS:
- Use the provided context when relevant to answer the question
- If the context doesn't contain relevant information, use your general knowledge
- Be comprehensive but concise
- Provide specific details when available
- If you're unsure about something, say so rather than guessing

RESPONSE:"""

    def clean_for_voice(self, text: str) -> str:
        """Clean text for voice synthesis"""
        text = text.replace('**', '').replace('*', '')
        text = text.replace('```', '').replace('`', '')
        text = text.replace('\n', '. ')
        
        if len(text) > 500:
            text = text[:500] + "..."
        
        return text.strip()

if __name__ == '__main__':
    print("🤖 Simple RAG Agent - Interactive Chat")
    print("=" * 50)
    print("Type your messages below. Type 'quit' to exit.")
    print("=" * 50)
    
    agent = SimpleRAGAgent()
    print(f"Knowledge base loaded: {'Yes' if agent.knowledge_base else 'No'}")
    
    while True:
        try:
            user_input = input("\n💬 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye', 'goodbye']:
                print("\n🤖 Agent: Goodbye! It was nice chatting with you!")
                break
                
            if not user_input:
                continue
                
            print("🤔 Agent is thinking...")
            response = agent.run(user_input)
            print(f"🤖 Agent: {response}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Chat interrupted. Goodbye!")
            break
        except EOFError:
            print("\n\n👋 Chat ended. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
