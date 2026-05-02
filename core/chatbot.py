# core/chatbot.py
from typing import List, Dict, Tuple
from datetime import datetime
import re
from core.llm import get_provider
from core.chat import NotesChatRetriever # Make sure this is the correct import

class EduMindChatbot:
    """
    An advanced chatbot that can operate in two modes:
    1. 'notes': Answers questions based on a specific document (RAG).
    2. 'general': Acts as a general-purpose AI assistant.
    """
    def __init__(self, note_content: str = None, note_title: str = None):
        self.provider = get_provider()
        self.history: List[Dict[str, str]] = []
        self.set_mode('general') # Default to general mode

        if note_content and note_title:
            self.load_notes(note_content, note_title)

    def set_mode(self, mode: str):
        """Switches the chatbot's operational mode ('notes' or 'general')."""
        self.mode = mode
        if mode == 'notes':
            self.system_prompt = self._build_notes_system_prompt()
        else:
            self.system_prompt = self._build_general_system_prompt()
        self.clear_history() # Clear history when switching modes

    def load_notes(self, note_content: str, note_title: str):
        """Loads a document for 'notes' mode."""
        self.note_title = note_title
        self.retriever = NotesChatRetriever(note_content)
        self.set_mode('notes') # Switch to notes mode when a document is loaded

    def _build_general_system_prompt(self) -> str:
        """System prompt for the general-purpose AI assistant."""
        return """You are 'EduMind AI', a powerful and knowledgeable general-purpose AI assistant.
Your goal is to help users with a wide range of academic and general knowledge questions.
- Be curious, helpful, and highly intelligent.
- Provide accurate, well-structured, and detailed answers.
- Use markdown for formatting (headings, bold, lists, etc.).
- If a question is ambiguous, ask for clarification.
- Break down complex topics into easy-to-understand parts.
"""

    def _build_notes_system_prompt(self) -> str:
        """System prompt for answering questions based on user notes."""
        return f"""You are 'EduMind AI', an expert AI Tutor focused on helping a student understand their notes on '{self.note_title}'.
- Your answers MUST be based primarily on the provided <RELEVANT_NOTES_CONTEXT>.
- If the context doesn't contain the answer, you MUST state that clearly.
- Be conversational, encouraging, and clear. Use markdown for formatting.
"""

    def chat(self, user_message: str) -> str:
        """Processes a user message and returns the AI's response based on the current mode."""
        context_chunks = []
        if self.mode == 'notes' and hasattr(self, 'retriever'):
            # In notes mode, retrieve relevant context first
            context_chunks = self.retriever.retrieve(user_message, top_k=3)
        
        prompt = self._build_prompt(user_message, context_chunks)
        
        # Get response from the LLM
        response = self.provider.answer(prompt, []) # Pass empty list for context as it's in the prompt
        
        self.history.append({"role": "user", "content": user_message})
        self.history.append({"role": "assistant", "content": response})
        if len(self.history) > 10: self.history = self.history[-10:]
            
        return response

    def _build_prompt(self, user_message: str, context_chunks: List[str]) -> str:
        """Builds the final prompt for the LLM."""
        history_str = "\n".join([f"{msg['role'].title()}: {msg['content']}" for msg in self.history])
        
        # Construct the prompt differently based on the mode
        if self.mode == 'notes':
            context_str = "\n---\n".join(context_chunks) if context_chunks else "No specific context was found in the notes for this question."
            prompt = f"""{self.system_prompt}
<CONVERSATION_HISTORY>
{history_str}
</CONVERSATION_HISTORY>
<RELEVANT_NOTES_CONTEXT>
{context_str}
</RELEVANT_NOTES_CONTEXT>
**Student's Question:** "{user_message}"
**Your Task:** Based on the history and notes context, provide a helpful answer."""
        else: # General mode
            prompt = f"""{self.system_prompt}
<CONVERSATION_HISTORY>
{history_str}
</CONVERSATION_HISTORY>
**User's Question:** "{user_message}"
**Your Task:** Provide a comprehensive and accurate answer."""

        return prompt
    
    def clear_history(self):
        self.history = []