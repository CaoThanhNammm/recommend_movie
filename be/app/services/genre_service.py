from app.models.db import db
from app.models.genre import Genre

class GenreService:
    @staticmethod
    def get_all_genres():
        """
        Get all genres.
        
        Returns:
            list: A list of all genres
        """
        return Genre.query.order_by(Genre.name).all()
    
        """
        Get a genre by its ID.
        
        Args:
            genre_id (int): The ID of the genre
            
        Returns:
            Genre: The genre object or None if not found
        """
        return Genre.query.get(genre_id)
    

        """
        Get a genre by its name.
        
        Args:
            name (str): The name of the genre
            
        Returns:
            Genre: The genre object or None if not found
        """
        return Genre.query.filter_by(name=name).first()
    
    @staticmethod
    def create_genre(name):
        """
        Create a new genre.
        
        Args:
            name (str): The name of the genre
            
        Returns:
            tuple: (genre, message)
                If successful, returns (Genre object, "Genre created successfully")
                If error, returns (None, error_message)
        """
        # Check if genre already exists
        existing_genre = GenreService.get_genre_by_name(name)
        if existing_genre:
            return None, f"Genre '{name}' already exists"
        
        try:
            # Create new genre
            new_genre = Genre(name=name)
            db.session.add(new_genre)
            db.session.commit()
            
            return new_genre, "Genre created successfully"
            
        except Exception as e:
            db.session.rollback()
            return None, f"Error creating genre: {str(e)}"
    

        """
        Import genres from a CSV file.
        
        Args:
            csv_path (str): Path to the CSV file
            
        Returns:
            tuple: (count, message)
                If successful, returns (number of genres imported, "Genres imported successfully")
                If error, returns (0, error_message)
        """
        import pandas as pd
        
        try:
            # Read CSV file
            df = pd.read_csv(csv_path)
            
            if 'name' not in df.columns:
                return 0, "CSV file does not contain a 'name' column"
            
            # Import genres
            count = 0
            for _, row in df.iterrows():
                name = row['name']
                if not GenreService.get_genre_by_name(name):
                    genre, _ = GenreService.create_genre(name)
                    if genre:
                        count += 1
            
            return count, "Genres imported successfully"
            
        except Exception as e:
            db.session.rollback()
            return 0, f"Error importing genres: {str(e)}"