from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class EmbeddingService:
    def __init__(self, model_name="intfloat/multilingual-e5-large-instruct"):
        """
        Initialize the embedding service with the specified model.
        
        Args:
            model_name (str): The name of the model to use for embeddings.
        """
        self.model = SentenceTransformer(model_name)
    
    # def get_embedding(self, text):
    #     """
    #     Generate an embedding for the given text.
        
    #     Args:
    #         text (str): The text to embed.
            
    #     Returns:
    #         numpy.ndarray: The embedding vector.
    #     """
    #     # For E5 models, prepend "query: " for query texts and "passage: " for passage texts
    #     # For movie recommendation, we'll use "passage: " as we're embedding content
    #     if not text.startswith("passage: ") and not text.startswith("query: "):
    #         text = "passage: " + text
            
    #     return self.model.encode(text, normalize_embeddings=True)
    
    # def get_query_embedding(self, text):
        """
        Generate a query embedding for the given text.
        
        Args:
            text (str): The query text to embed.
            
        Returns:
            numpy.ndarray: The embedding vector.
        """
        # For E5 models, prepend "query: " for query texts
        if not text.startswith("query: "):
            text = "query: " + text
            
        return self.model.encode(text, normalize_embeddings=True)
    
    def calculate_similarity(self, embedding1, embedding2):
        """
        Calculate the cosine similarity between two embeddings.
        
        Args:
            embedding1 (numpy.ndarray): The first embedding.
            embedding2 (numpy.ndarray): The second embedding.
            
        Returns:
            float: The cosine similarity score.
        """
        # Reshape embeddings for cosine_similarity function
        embedding1_reshaped = embedding1.reshape(1, -1)
        embedding2_reshaped = embedding2.reshape(1, -1)
        
        # Calculate cosine similarity
        similarity = cosine_similarity(embedding1_reshaped, embedding2_reshaped)[0][0]
        
        return similarity
    
    def batch_encode(self, texts, is_query=False):
        """
        Encode a batch of texts.
        
        Args:
            texts (list): List of texts to encode.
            is_query (bool): Whether the texts are queries or passages.
            
        Returns:
            numpy.ndarray: The batch of embedding vectors.
        """
        # Prepend appropriate prefix for E5 models
        prefix = "query: " if is_query else "passage: "
        prefixed_texts = [prefix + text if not text.startswith(prefix) else text for text in texts]
        
        return self.model.encode(prefixed_texts, normalize_embeddings=True)