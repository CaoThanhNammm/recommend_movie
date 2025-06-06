import pandas as pd
import numpy as np
import json
import os
import faiss
import pickle
import torch
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Union, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Check if GPU is available
GPU_AVAILABLE = torch.cuda.is_available()
if GPU_AVAILABLE:
    logger.info(f"GPU available: {torch.cuda.get_device_name(0)}")
else:
    logger.info("No GPU available, using CPU")

class MovieEmbedder:
    """
    A class to embed movie data from a CSV file into a FAISS vector database.
    Uses the intfloat/multilingual-e5-large-instruct model for embedding.
    """
    
    def __init__(self, 
                 csv_path: str = "dataset/movies_processed.csv", 
                 model_name: str = "intfloat/multilingual-e5-large-instruct",
                 output_dir: str = "embeddings",
                 use_gpu: bool = True,
                 batch_size: int = 32):
        """
        Initialize the MovieEmbedder.
        
        Args:
            csv_path: Path to the CSV file containing movie data
            model_name: Name of the SentenceTransformer model to use
            output_dir: Directory to save the embeddings and index
            use_gpu: Whether to use GPU for FAISS (if available)
            batch_size: Batch size for encoding (larger values use more memory but are faster)
        """
        self.csv_path = csv_path
        self.model_name = model_name
        self.output_dir = output_dir
        self.use_gpu = use_gpu and GPU_AVAILABLE
        self.batch_size = batch_size
        self.model = None
        self.df = None
        self.embeddings = None
        self.index = None
        self.metadata = None
        self.res = None  # For GPU resources
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Create faiss directory if it doesn't exist
        faiss_dir = os.path.join(output_dir, "faiss")
        if not os.path.exists(faiss_dir):
            os.makedirs(faiss_dir)
            
        logger.info(f"Initialized MovieEmbedder with model: {model_name}")
        if self.use_gpu:
            logger.info("GPU acceleration enabled for FAISS")
    
    def load_data(self) -> pd.DataFrame:
        """
        Load the movie data from the CSV file.
        
        Returns:
            DataFrame containing the movie data
        """
        logger.info(f"Loading data from {self.csv_path}")
        self.df = pd.read_csv(self.csv_path)
        logger.info(f"Loaded {len(self.df)} movies")
        return self.df
    
    def load_model(self) -> SentenceTransformer:
        """
        Load the SentenceTransformer model.
        
        Returns:
            The loaded SentenceTransformer model
        """
        logger.info(f"Loading model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        return self.model
    
    def _parse_json_field(self, field: str) -> List[str]:
        """
        Parse a JSON field from the DataFrame and extract the 'name' values.
        
        Args:
            field: The JSON field to parse
            
        Returns:
            List of name values extracted from the JSON field
        """
        if pd.isna(field):
            return []
        
        try:
            data = json.loads(field.replace("'", "\""))
            return [item.get('name', '') for item in data if 'name' in item]
        except (json.JSONDecodeError, AttributeError):
            return []
    
    def _prepare_text_for_embedding(self, row: pd.Series) -> str:
        """
        Prepare the text for embedding by combining relevant fields.
        
        Args:
            row: A row from the DataFrame
            
        Returns:
            A string containing the combined text for embedding
        """
        # Extract and process fields
        title = row['title'] if not pd.isna(row['title']) else ""
        overview = row['overview'] if not pd.isna(row['overview']) else ""
        
        # Parse JSON fields
        genres = self._parse_json_field(row['genres'])
        production_companies = self._parse_json_field(row['production_companies'])
        keywords = self._parse_json_field(row['keywords'])
        cast = self._parse_json_field(row['cast'])
        crew = self._parse_json_field(row['crew'])
        
        # Format release date
        release_date = row['release_date'] if not pd.isna(row['release_date']) else ""
        
        # Format ratings
        vote_average = f"Rating: {row['vote_average']}" if not pd.isna(row['vote_average']) else ""
        vote_count = f"Votes: {row['vote_count']}" if not pd.isna(row['vote_count']) else ""
        
        # Combine all fields into a single text
        text_parts = [
            f"Title: {title}",
            f"Overview: {overview}",
            f"Genres: {', '.join(genres)}",
            f"Release Date: {release_date}",
            vote_average,
            vote_count,
            f"Production Companies: {', '.join(production_companies)}",
            f"Keywords: {', '.join(keywords)}",
            f"Cast: {', '.join(cast)}",
            f"Crew: {', '.join(crew)}"
        ]
        
        # Filter out empty parts and join with newlines
        text = "\n".join([part for part in text_parts if part and part.strip()])
        return text
    
    def _create_metadata(self, row: pd.Series) -> Dict[str, Any]:
        """
        Create metadata for a movie.
        
        Args:
            row: A row from the DataFrame
            
        Returns:
            Dictionary containing metadata for the movie
        """
        # Parse JSON fields
        genres = self._parse_json_field(row['genres'])
        production_companies = self._parse_json_field(row['production_companies'])
        keywords = self._parse_json_field(row['keywords'])
        cast = self._parse_json_field(row['cast'])
        crew = self._parse_json_field(row['crew'])
        
        return {
            'id': row['id'],
            'tmdb_id': row['tmdb_id'],
            'imdb_id': row['imdb_id'],
            'title': row['title'],
            'original_title': row['original_title'],
            'overview': row['overview'],
            'genres': genres,
            'release_date': row['release_date'],
            'vote_average': row['vote_average'],
            'vote_count': row['vote_count'],
            'production_companies': production_companies,
            'keywords': keywords,
            'cast': cast,
            'crew': crew,
            'poster_path': row['poster_path'],
            'backdrop_path': row['backdrop_path']
        }
    
    def create_embeddings(self) -> np.ndarray:
        """
        Create embeddings for all movies in the DataFrame.
        Uses batching for better memory management.
        
        Returns:
            NumPy array of embeddings
        """
        if self.df is None:
            self.load_data()
        
        if self.model is None:
            self.load_model()
        
        logger.info("Preparing texts for embedding...")
        texts = []
        self.metadata = []
        
        for _, row in self.df.iterrows():
            text = self._prepare_text_for_embedding(row)
            texts.append(text)
            self.metadata.append(self._create_metadata(row))
        
        logger.info(f"Creating embeddings for {len(texts)} movies...")
        
        # Use batching for better memory management
        batch_size = self.batch_size
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            batch_num = i // batch_size + 1
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch_texts)} texts)")
            batch_embeddings = self.model.encode(
                batch_texts, 
                show_progress_bar=True,
                convert_to_numpy=True,
                device='cuda' if self.use_gpu else 'cpu'
            )
            all_embeddings.append(batch_embeddings)
            
            # Free up memory
            if self.use_gpu:
                torch.cuda.empty_cache()
        
        # Combine all batches
        self.embeddings = np.vstack(all_embeddings)
        
        logger.info(f"Created embeddings with shape: {self.embeddings.shape}")
        return self.embeddings
    
    def build_faiss_index(self) -> faiss.Index:
        """
        Build a FAISS index from the embeddings.
        Uses GPU if available and enabled.
        
        Returns:
            FAISS index
        """
        if self.embeddings is None:
            self.create_embeddings()
        
        # Get the dimension of the embeddings
        dimension = self.embeddings.shape[1]
        
        logger.info(f"Building FAISS index with dimension {dimension}...")
        
        # Create a flat L2 index
        index = faiss.IndexFlatL2(dimension)
        
        # Use GPU if available and enabled
        if self.use_gpu:
            try:
                # Get GPU resources
                self.res = faiss.StandardGpuResources()
                
                # Configure GPU options
                gpu_options = faiss.GpuIndexFlatConfig()
                gpu_options.device = 0  # Use first GPU
                gpu_options.useFloat16 = False  # Use full precision (more accurate)
                
                # Create GPU index
                gpu_index = faiss.GpuIndexFlatL2(self.res, dimension, gpu_options)
                
                # Add vectors to the index
                gpu_index.add(self.embeddings.astype('float32'))
                
                # Store the index
                self.index = gpu_index
                logger.info("Using GPU-accelerated FAISS index")
            except Exception as e:
                logger.warning(f"Failed to create GPU index: {e}")
                logger.info("Falling back to CPU index")
                index.add(self.embeddings.astype('float32'))
                self.index = index
        else:
            # Add vectors to the CPU index
            index.add(self.embeddings.astype('float32'))
            self.index = index
        
        logger.info(f"Built FAISS index with {self.index.ntotal} vectors")
        return self.index
    
    def save_embeddings_and_index(self, 
                                  embeddings_file: str = "faiss/movie_embeddings.npy",
                                  index_file: str = "faiss/movie_index.faiss",
                                  metadata_file: str = "faiss/movie_metadata.pkl") -> None:
        """
        Save the embeddings, FAISS index, and metadata to disk.
        
        Args:
            embeddings_file: Filename for the embeddings
            index_file: Filename for the FAISS index
            metadata_file: Filename for the metadata
        """
        if self.embeddings is None or self.index is None or self.metadata is None:
            logger.error("Embeddings, index, or metadata not created yet")
            return
        
        # Save embeddings
        embeddings_path = os.path.join(self.output_dir, embeddings_file)
        np.save(embeddings_path, self.embeddings)
        logger.info(f"Saved embeddings to {embeddings_path}")
        
        # Save FAISS index
        index_path = os.path.join(self.output_dir, index_file)
        faiss.write_index(self.index, index_path)
        logger.info(f"Saved FAISS index to {index_path}")
        
        # Save metadata
        metadata_path = os.path.join(self.output_dir, metadata_file)
        with open(metadata_path, 'wb') as f:
            pickle.dump(self.metadata, f)
        logger.info(f"Saved metadata to {metadata_path}")
    
    def load_embeddings_and_index(self, 
                                 embeddings_file: str = "faiss/movie_embeddings.npy", 
                                 index_file: str = "faiss/movie_index.faiss",
                                 metadata_file: str = "faiss/movie_metadata.pkl") -> tuple:
        """
        Load the embeddings, FAISS index, and metadata from disk.
        Converts the index to GPU if GPU is available and enabled.
        
        Args:
            embeddings_file: Filename for the embeddings
            index_file: Filename for the FAISS index
            metadata_file: Filename for the metadata
            
        Returns:
            Tuple of (embeddings, index, metadata)
        """
        # Load embeddings
        embeddings_path = os.path.join(self.output_dir, embeddings_file)
        self.embeddings = np.load(embeddings_path)
        logger.info(f"Loaded embeddings from {embeddings_path} with shape {self.embeddings.shape}")
        
        # Load FAISS index
        index_path = os.path.join(self.output_dir, index_file)
        cpu_index = faiss.read_index(index_path)
        
        # Convert to GPU index if GPU is available and enabled
        if self.use_gpu:
            try:
                # Get GPU resources
                self.res = faiss.StandardGpuResources()
                
                # Configure GPU options
                gpu_options = faiss.GpuIndexFlatConfig()
                gpu_options.device = 0  # Use first GPU
                gpu_options.useFloat16 = False  # Use full precision
                
                # Convert CPU index to GPU index
                self.index = faiss.index_cpu_to_gpu(self.res, 0, cpu_index)
                logger.info(f"Converted index to GPU with {self.index.ntotal} vectors")
            except Exception as e:
                logger.warning(f"Failed to convert index to GPU: {e}")
                logger.info("Using CPU index instead")
                self.index = cpu_index
        else:
            self.index = cpu_index
            
        logger.info(f"Loaded FAISS index from {index_path} with {self.index.ntotal} vectors")
        
        # Load metadata
        metadata_path = os.path.join(self.output_dir, metadata_file)
        with open(metadata_path, 'rb') as f:
            self.metadata = pickle.load(f)
        logger.info(f"Loaded metadata from {metadata_path} with {len(self.metadata)} entries")
        
        return self.embeddings, self.index, self.metadata
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for movies similar to the query.
        Uses GPU for encoding if available and enabled.
        
        Args:
            query: Query text
            k: Number of results to return
            
        Returns:
            List of dictionaries containing metadata for the top k results
        """
        if self.model is None:
            self.load_model()
        
        if self.index is None or self.metadata is None:
            logger.error("Index or metadata not loaded. Please build or load the index first.")
            return []
        
        # Encode the query using GPU if available
        query_embedding = self.model.encode(
            [query], 
            convert_to_numpy=True,
            device='cuda' if self.use_gpu else 'cpu'
        )[0].reshape(1, -1).astype('float32')
        
        # Search the index
        distances, indices = self.index.search(query_embedding, k)
        
        # Get the metadata for the results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.metadata):
                result = self.metadata[idx].copy()
                result['distance'] = float(distances[0][i])
                # Calculate similarity score (1 = perfect match, 0 = completely different)
                result['similarity'] = 1.0 - min(float(distances[0][i]), 1.0)
                results.append(result)
        
        # Free up GPU memory if using GPU
        if self.use_gpu:
            torch.cuda.empty_cache()
        
        return results

def main():
    """
    Main function to demonstrate the usage of the MovieEmbedder class.
    """
    import time
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Movie Embedder Demo')
    parser.add_argument('--no-gpu', action='store_true', help='Disable GPU acceleration')
    parser.add_argument('--batch-size', type=int, default=32, help='Batch size for encoding')
    parser.add_argument('--query', type=str, default="action movies with high ratings", 
                        help='Search query')
    parser.add_argument('--top-k', type=int, default=5, help='Number of results to return')
    parser.add_argument('--load-only', action='store_true', 
                        help='Load existing index instead of creating a new one')
    args = parser.parse_args()
    
    # Create an instance of MovieEmbedder
    embedder = MovieEmbedder(
        use_gpu=not args.no_gpu,
        batch_size=args.batch_size
    )
    
    if args.load_only:
        # Load existing embeddings and index
        logger.info("Loading existing embeddings and index...")
        start_time = time.time()
        embedder.load_embeddings_and_index()
        load_time = time.time() - start_time
        logger.info(f"Loaded in {load_time:.2f} seconds")
    else:
        # Load data and create embeddings
        logger.info("Loading data...")
        embedder.load_data()
        
        # Create embeddings
        logger.info("Creating embeddings...")
        start_time = time.time()
        embedder.create_embeddings()
        embed_time = time.time() - start_time
        logger.info(f"Created embeddings in {embed_time:.2f} seconds")
        
        # Build and save the FAISS index
        logger.info("Building FAISS index...")
        start_time = time.time()
        embedder.build_faiss_index()
        index_time = time.time() - start_time
        logger.info(f"Built index in {index_time:.2f} seconds")
        
        logger.info("Saving embeddings and index...")
        embedder.save_embeddings_and_index()
    
    # Example search
    logger.info(f"Searching for: {args.query}")
    start_time = time.time()
    results = embedder.search(args.query, k=args.top_k)
    search_time = time.time() - start_time
    logger.info(f"Search completed in {search_time:.4f} seconds")
    
    # Print the results
    print(f"\nFound {len(results)} results:")
    for i, result in enumerate(results):
        print(f"{i+1}. {result['title']} (Score: {result['similarity']:.4f})")
        print(f"   Genres: {', '.join(result['genres'])}")
        print(f"   Rating: {result['vote_average']} ({result['vote_count']} votes)")
        print(f"   Release Date: {result['release_date']}")
        print()

if __name__ == "__main__":
    main()