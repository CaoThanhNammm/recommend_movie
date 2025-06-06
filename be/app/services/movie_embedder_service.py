import os
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
import faiss
import pickle
from typing import List, Dict, Any, Optional
import logging
from dotenv import load_dotenv
import threading

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Check if GPU is available for PyTorch
GPU_AVAILABLE = torch.cuda.is_available()

# Check if FAISS has GPU support
FAISS_GPU_AVAILABLE = False
try:
    # Try to access GPU-specific FAISS functionality
    faiss.StandardGpuResources
    FAISS_GPU_AVAILABLE = True
    logger.info("FAISS GPU support is available")
except AttributeError:
    logger.info("FAISS GPU support is not available, using CPU version")

class MovieEmbedderService:
    """
    Service for embedding movie data and performing semantic search using FAISS.
    Based on the MovieEmbedder class from movie_embedder_kaggle.py.
    """
    
    # Lock for thread-safe model loading
    _model_lock = threading.Lock()
    
    def __init__(self, 
                 model_name: str = None,
                 faiss_dir: str = None,
                 use_gpu: bool = None,
                 lazy_load: bool = None):
        """
        Initialize the MovieEmbedderService.
        
        Args:
            model_name: Name of the SentenceTransformer model to use
            faiss_dir: Directory where FAISS index and metadata are stored
            use_gpu: Whether to use GPU for encoding (if available)
            lazy_load: Whether to load the model lazily (only when needed)
        """
        # Get configuration from environment variables or use defaults
        self.model_name = model_name or os.getenv('EMBEDDER_MODEL_NAME', "intfloat/multilingual-e5-large-instruct")
        self.faiss_dir = faiss_dir or os.getenv('FAISS_DIR', "d:/recommend_movie_system/embeddings/faiss")
        
        # Parse use_gpu from environment if not provided
        env_use_gpu = os.getenv('USE_GPU', 'auto').lower()
        if use_gpu is None:
            if env_use_gpu == 'auto':
                use_gpu = GPU_AVAILABLE
            else:
                use_gpu = env_use_gpu in ('true', '1', 'yes')
        
        # Parse lazy_load from environment if not provided
        env_lazy_load = os.getenv('LAZY_LOAD_MODEL', 'true').lower()
        if lazy_load is None:
            lazy_load = env_lazy_load in ('true', '1', 'yes')
        
        self.lazy_load = lazy_load
        
        # Only use GPU for FAISS if both PyTorch GPU and FAISS GPU are available
        self.use_gpu_for_faiss = use_gpu and GPU_AVAILABLE and FAISS_GPU_AVAILABLE
        # Use GPU for PyTorch if available
        self.use_gpu_for_torch = use_gpu and GPU_AVAILABLE
        
        self.model = None
        self.index = None
        self.metadata = None
        
        # Create faiss directory if it doesn't exist
        os.makedirs(self.faiss_dir, exist_ok=True)
        
        # Load index immediately (we need this for search)
        self.load_index_and_metadata()
        
        # Load model only if not using lazy loading
        if not self.lazy_load:
            self.load_model()
            logger.info(f"Model loaded immediately: {self.model_name}")
        else:
            logger.info(f"Model will be loaded lazily when needed: {self.model_name}")
        
        logger.info(f"MovieEmbedderService initialized")
        logger.info(f"Using GPU for PyTorch: {self.use_gpu_for_torch}")
        logger.info(f"Using GPU for FAISS: {self.use_gpu_for_faiss}")
    
    def load_model(self) -> Any:
        """
        Load the SentenceTransformer model.
        
        Returns:
            The loaded model
        """
        # If model is already loaded, return it
        if self.model is not None:
            return self.model
            
        # Use lock to ensure thread safety
        with self._model_lock:
            # Check again in case another thread loaded the model while we were waiting
            if self.model is not None:
                return self.model
                
            try:
                logger.info(f"Loading model: {self.model_name}")
                self.model = SentenceTransformer(self.model_name)
                
                # Use half precision if using GPU to save memory
                if self.use_gpu_for_torch:
                    self.model = self.model.half()
                    logger.info("Using half precision for model to save GPU memory")
                    
                return self.model
            except Exception as e:
                logger.error(f"Error loading model: {str(e)}")
                logger.warning("Using fallback random embedding method")
                # Create a dummy model that returns random embeddings
                # This is just for testing when the real model is not available
                class DummyModel:
                    def encode(self, texts, convert_to_numpy=True, device=None, show_progress_bar=False):
                        if isinstance(texts, list):
                            return np.random.random((len(texts), 1024)).astype('float32')
                        return np.random.random(1024).astype('float32')
                
                self.model = DummyModel()
                return self.model
    
    def load_index_and_metadata(self) -> None:
        """
        Load the FAISS index and metadata from disk.
        """
        index_path = os.path.join(self.faiss_dir, "movie_index.faiss")
        metadata_path = os.path.join(self.faiss_dir, "movie_metadata.pkl")
        
        if os.path.exists(index_path) and os.path.exists(metadata_path):
            try:
                start_time = __import__('time').time()
                logger.info(f"Loading FAISS index from {index_path}")
                self.index = faiss.read_index(index_path)
                
                # Use GPU if available, enabled, and FAISS has GPU support
                if self.use_gpu_for_faiss:
                    try:
                        res = faiss.StandardGpuResources()
                        self.index = faiss.index_cpu_to_gpu(res, 0, self.index)
                        logger.info("Successfully moved FAISS index to GPU")
                    except Exception as e:
                        logger.warning(f"Failed to move FAISS index to GPU: {str(e)}")
                        logger.info("Using CPU for FAISS index")
                
                logger.info(f"Loading metadata from {metadata_path}")
                with open(metadata_path, 'rb') as f:
                    self.metadata = pickle.load(f)
                
                load_time = __import__('time').time() - start_time
                logger.info(f"Loaded index with {self.index.ntotal} vectors and {len(self.metadata)} metadata entries in {load_time:.2f} seconds")
            except Exception as e:
                logger.error(f"Error loading index or metadata: {str(e)}", exc_info=True)
                self.index = None
                self.metadata = None
        else:
            logger.warning(f"FAISS index or metadata not found at {self.faiss_dir}")
            logger.warning(f"Expected files: {index_path} and {metadata_path}")
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for movies similar to the query.
        
        Args:
            query: Query text
            k: Number of results to return
            
        Returns:
            List of dictionaries containing metadata for the top k results
        """
        try:
            # Ensure model is loaded (will use lazy loading if enabled)
            if self.model is None:
                logger.info("Model not loaded yet, loading now...")
                self.load_model()
            
            if self.index is None or self.metadata is None:
                logger.error("Index or metadata not loaded.")
                return []
            
            # Encode the query using GPU if available for PyTorch
            device = 'cuda' if self.use_gpu_for_torch else 'cpu'
            logger.debug(f"Encoding query using device: {device}")
            
            start_time = __import__('time').time()
            query_embedding = self.model.encode(
                [query], 
                convert_to_numpy=True,
                device=device,
                show_progress_bar=False
            )[0].reshape(1, -1).astype('float32')
            encoding_time = __import__('time').time() - start_time
            logger.debug(f"Query encoding took {encoding_time:.2f} seconds")
            
            # Normalize for cosine similarity
            faiss.normalize_L2(query_embedding)
            
            # Search the index
            start_time = __import__('time').time()
            distances, indices = self.index.search(query_embedding, k)
            search_time = __import__('time').time() - start_time
            logger.debug(f"FAISS search took {search_time:.2f} seconds")
            
            # Get the metadata for the results
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.metadata) and idx >= 0:
                    result = self.metadata[idx].copy()
                    result['distance'] = float(distances[0][i])
                    # Calculate similarity score (1 = perfect match, 0 = completely different)
                    result['similarity'] = 1.0 - min(float(distances[0][i]), 1.0)
                    results.append(result)
            
            # Free up GPU memory if using GPU for PyTorch
            if self.use_gpu_for_torch:
                torch.cuda.empty_cache()
            
            logger.debug(f"Search returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error during search: {str(e)}", exc_info=True)
            logger.warning("Returning empty results due to search error")
            return []

# Singleton instance
_instance = None
_instance_lock = threading.Lock()

def get_instance():
    """
    Get or create the singleton instance of MovieEmbedderService.
    
    Returns:
        MovieEmbedderService instance
    """
    global _instance
    
    # Fast path: if instance already exists, return it
    if _instance is not None:
        return _instance
    
    # Slow path: create instance with lock to ensure thread safety
    with _instance_lock:
        # Check again in case another thread created the instance while we were waiting
        if _instance is None:
            logger.info("Creating MovieEmbedderService instance")
            _instance = MovieEmbedderService()
            
    return _instance