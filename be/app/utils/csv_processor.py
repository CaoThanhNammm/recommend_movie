import pandas as pd
import json
import os
from datetime import datetime
import numpy as np

class MovieCSVProcessor:
    """
    Class để xử lý và join các file CSV để tạo file CSV mới có cấu trúc như bảng Movie.
    """
    
    def __init__(self, dataset_dir):
        """
        Khởi tạo MovieCSVProcessor với đường dẫn đến thư mục chứa các file CSV.
        
        Args:
            dataset_dir (str): Đường dẫn đến thư mục chứa các file CSV.
        """
        self.dataset_dir = dataset_dir
        self.movies_metadata_path = os.path.join(dataset_dir, 'movies_metadata.csv')
        self.links_path = os.path.join(dataset_dir, 'links.csv')
        self.keywords_path = os.path.join(dataset_dir, 'keywords.csv')
        self.credits_path = os.path.join(dataset_dir, 'credits.csv')
    
    def load_data(self, nrows=None):
        """
        Load dữ liệu từ các file CSV.
        
        Args:
            nrows (int, optional): Số dòng cần đọc từ mỗi file. Nếu None, đọc toàn bộ file.
            
        Returns:
            tuple: Tuple chứa các DataFrame đã load.
        """
        print(f"Loading data from {self.dataset_dir}...")
        
        # Load movies metadata
        movies_df = pd.read_csv(self.movies_metadata_path, nrows=nrows, low_memory=False)
        
        # Load links
        links_df = pd.read_csv(self.links_path, nrows=nrows)
        
        # Load keywords
        keywords_df = pd.read_csv(self.keywords_path, nrows=nrows)
        
        # Load credits
        credits_df = pd.read_csv(self.credits_path, nrows=nrows)
        
        print("Data loaded successfully.")
        return movies_df, links_df, keywords_df, credits_df
    
    def process_data(self, movies_df, links_df, keywords_df, credits_df):
        """
        Xử lý và join các DataFrame để tạo DataFrame mới có cấu trúc như bảng Movie.
        
        Args:
            movies_df (DataFrame): DataFrame chứa metadata của phim.
            links_df (DataFrame): DataFrame chứa links.
            keywords_df (DataFrame): DataFrame chứa keywords.
            credits_df (DataFrame): DataFrame chứa credits.
            
        Returns:
            DataFrame: DataFrame đã xử lý.
        """
        print("Processing data...")
        
        # Chuyển đổi id sang kiểu số nguyên để join
        try:
            movies_df['id'] = pd.to_numeric(movies_df['id'], errors='coerce')
            keywords_df['id'] = pd.to_numeric(keywords_df['id'], errors='coerce')
            credits_df['id'] = pd.to_numeric(credits_df['id'], errors='coerce')
        except Exception as e:
            print(f"Error converting IDs to numeric: {str(e)}")
        
        # Join movies với keywords
        print("Joining movies with keywords...")
        movies_keywords = pd.merge(movies_df, keywords_df, on='id', how='left')
        
        # Join với credits
        print("Joining with credits...")
        movies_full = pd.merge(movies_keywords, credits_df, on='id', how='left')
        
        # Xử lý links (nếu cần)
        if 'tmdbId' in links_df.columns:
            print("Processing links...")
            # Chuyển đổi tmdbId sang kiểu số nguyên
            links_df['tmdbId'] = pd.to_numeric(links_df['tmdbId'], errors='coerce')
            
            # Join với links dựa trên tmdbId và id
            movies_full = pd.merge(
                movies_full, 
                links_df, 
                left_on='id', 
                right_on='tmdbId', 
                how='left'
            )
        
        # Tạo DataFrame mới với cấu trúc như bảng Movie
        print("Creating final DataFrame...")
        movie_data = []
        
        for _, row in movies_full.iterrows():
            try:
                # Xử lý ngày phát hành
                release_date = None
                if pd.notna(row.get('release_date')):
                    try:
                        release_date = pd.to_datetime(row['release_date']).strftime('%Y-%m-%d')
                    except:
                        pass
                
                # Tạo dictionary cho mỗi phim
                movie_dict = {
                    'id': row.get('id'),
                    'tmdb_id': row.get('id'),  # Sử dụng id từ movies_metadata làm tmdb_id
                    'imdb_id': row.get('imdb_id'),
                    'title': row.get('title', ''),
                    'original_title': row.get('original_title', ''),
                    'overview': row.get('overview', ''),
                    'genres': row.get('genres', '[]'),
                    'release_date': release_date,
                    'runtime': float(row.get('runtime')) if pd.notna(row.get('runtime')) else None,
                    'popularity': float(row.get('popularity')) if pd.notna(row.get('popularity')) else None,
                    'vote_average': float(row.get('vote_average')) if pd.notna(row.get('vote_average')) else None,
                    'vote_count': int(row.get('vote_count')) if pd.notna(row.get('vote_count')) else None,
                    'poster_path': row.get('poster_path', ''),
                    'production_companies': row.get('production_companies', '[]'),
                    'keywords': row.get('keywords', '[]'),
                    'cast': row.get('cast', '[]'),
                    'crew': row.get('crew', '[]'),
                    'created_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                movie_data.append(movie_dict)
            except Exception as e:
                print(f"Error processing movie {row.get('title', 'unknown')}: {str(e)}")
                continue
        
        # Tạo DataFrame từ list các dictionary
        result_df = pd.DataFrame(movie_data)
        print(f"Final DataFrame created with {len(result_df)} rows.")
        
        return result_df
    
    def create_movie_csv(self, output_path, nrows=None):
        """
        Tạo file CSV mới có cấu trúc như bảng Movie.
        
        Args:
            output_path (str): Đường dẫn đến file CSV output.
            nrows (int, optional): Số dòng cần đọc từ mỗi file input. Nếu None, đọc toàn bộ file.
            
        Returns:
            bool: True nếu thành công, False nếu thất bại.
        """
        try:
            # Load dữ liệu
            movies_df, links_df, keywords_df, credits_df = self.load_data(nrows)
            
            # Xử lý dữ liệu
            result_df = self.process_data(movies_df, links_df, keywords_df, credits_df)
            
            # Lưu kết quả vào file CSV
            print(f"Saving results to {output_path}...")
            result_df.to_csv(output_path, index=False)
            print(f"CSV file created successfully at {output_path}")
            
            return True
        except Exception as e:
            print(f"Error creating movie CSV: {str(e)}")
            return False
    
    def generate_embedding_text(self, row):
        """
        Tạo text để tạo embedding cho phim.
        
        Args:
            row (Series): Dòng dữ liệu của phim.
            
        Returns:
            str: Text để tạo embedding.
        """
        embedding_text = f"Movie: {row.get('title', '')}. "
        
        if pd.notna(row.get('overview')):
            embedding_text += f"Overview: {row.get('overview')}. "
        
        if pd.notna(row.get('genres')):
            try:
                genres_list = json.loads(row.get('genres', '[]'))
                genre_names = [g['name'] for g in genres_list if isinstance(g, dict) and 'name' in g]
                if genre_names:
                    embedding_text += f"Genres: {', '.join(genre_names)}. "
            except:
                pass
        
        return embedding_text


if __name__ == "__main__":
    # Đường dẫn đến thư mục chứa các file CSV
    dataset_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'dataset')
    
    # Đường dẫn đến file CSV output
    output_path = os.path.join(dataset_dir, 'movies_processed.csv')
    
    # Tạo instance của MovieCSVProcessor
    processor = MovieCSVProcessor(dataset_dir)
    
    # Tạo file CSV mới (chỉ xử lý 100 dòng đầu tiên để test)
    processor.create_movie_csv(output_path)
    
    print("Done!")