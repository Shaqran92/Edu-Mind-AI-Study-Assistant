# core/chat.py
from typing import List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from utils import chunk_text
from config import settings

class NotesChatRetriever:
    """
    Handles text chunking and TF-IDF based retrieval. This class is a dedicated
    "Retriever" whose only job is to find the most relevant text chunks.
    """
    def __init__(self, content: str):
        self.chunks = chunk_text(content, settings.max_chunk_chars)
        
        if self.chunks:
            self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
            try:
                self.matrix = self.vectorizer.fit_transform(self.chunks)
            except ValueError:
                self.vectorizer = TfidfVectorizer(stop_words="english")
                self.matrix = self.vectorizer.fit_transform(self.chunks)
        else:
            self.vectorizer = None
            self.matrix = None

    def retrieve(self, question: str, top_k: int = 3) -> List[str]:
        """
        Finds and returns the top_k most relevant text chunks for a given question.
        """
        if not self.chunks or self.matrix is None:
            print("⚠️ Retriever has no content to search.")
            return []
        
        query_vector = self.vectorizer.transform([question])
        similarities = cosine_similarity(query_vector, self.matrix).flatten()
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        # --- THIS IS THE FIX ---
        # REMOVED the strict similarity filter. Now, we will ALWAYS return the
        # top 'k' results, even if their similarity score is low. This lets the
        # much smarter LLM decide if the context is useful, which is the correct
        # approach for RAG.
        relevant_chunks = [self.chunks[i] for i in top_indices]
        # --- END FIX ---

        print(f"🔍 Retrieved {len(relevant_chunks)} chunks for the AI. Top score: {similarities[top_indices[0]]:.2f}")
        return relevant_chunks