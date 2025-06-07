from app.models.db import db
from datetime import datetime
import json

class Movie(db.Model):
    __tablename__ = 'movies'
    
    id = db.Column(db.Integer, primary_key=True)
    tmdb_id = db.Column(db.Integer, unique=True, nullable=True)
    imdb_id = db.Column(db.String(20), unique=True, nullable=True)
    title = db.Column(db.String(255), nullable=False)
    original_title = db.Column(db.String(255), nullable=True)
    overview = db.Column(db.Text, nullable=True)
    genres = db.Column(db.Text, nullable=True)  # Stored as JSON string
    release_date = db.Column(db.Date, nullable=True)
    runtime = db.Column(db.Integer, nullable=True)
    popularity = db.Column(db.Float, nullable=True)
    vote_average = db.Column(db.Float, nullable=True)
    vote_count = db.Column(db.Integer, nullable=True)
    wr = db.Column(db.Float, nullable=True)  # Weighted Rating
    poster_path = db.Column(db.String(255), nullable=True)
    production_companies = db.Column(db.Text, nullable=True)  # Stored as JSON string
    keywords = db.Column(db.String(255), nullable=True)  # Stored as JSON string
    cast = db.Column(db.Text, nullable=True)  
    crew = db.Column(db.Text, nullable=True) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ratings = db.relationship('UserRating', back_populates='movie', cascade='all, delete-orphan')
    watch_history = db.relationship('UserWatchHistory', back_populates='movie', cascade='all, delete-orphan')
    
    def get_genres_list(self):
        if self.genres is None or self.genres == '':
            # Update the field to be a valid JSON array
            self.genres = '[]'
            return []
        try:
            return json.loads(self.genres)
        except (json.JSONDecodeError, TypeError):
            # If there's an error parsing, reset to empty array
            self.genres = '[]'
            return []
    
    def get_keywords_list(self):
        if self.keywords is None or self.keywords == '':
            return []
        try:
            return json.loads(self.keywords)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def get_cast_list(self):
        if self.cast is None or self.cast == '':
            # Update the field to be a valid JSON array
            self.cast = '[]'
            return []
        try:
            # Try to parse as JSON
            return json.loads(self.cast)
        except (json.JSONDecodeError, TypeError):
            # If there's an error parsing, try to fix common issues
            try:
                # Replace single quotes with double quotes
                fixed_str = self.cast.replace("'", "\"")
                # Fix unescaped quotes in strings
                fixed_str = fixed_str.replace('\\"', '\\\\"')
                # Fix missing commas
                fixed_str = fixed_str.replace('"}{"', '"},{"')
                
                # Try to parse the fixed string
                return json.loads(fixed_str)
            except (json.JSONDecodeError, TypeError):
                # If still failing, try to extract data using regex
                import re
                import logging
                logger = logging.getLogger(__name__)
                
                try:
                    # Extract name fields using regex
                    name_pattern = r"['\"]name['\"]:\s*['\"]([^'\"]*)['\"]"
                    names = re.findall(name_pattern, self.cast)
                    if names:
                        logger.info(f"Extracted {len(names)} names from cast using regex")
                        return [{'name': name} for name in names]
                except Exception as regex_error:
                    logger.error(f"Error extracting names with regex: {str(regex_error)}")
                
                # If all else fails, reset to empty array
                self.cast = '[]'
                try:
                    db.session.commit()
                except:
                    db.session.rollback()
                return []
    
    def get_production_companies(self):
        if self.production_companies is None or self.production_companies == '':
            return []
        try:
            return json.loads(self.production_companies)
        except (json.JSONDecodeError, TypeError):
            return []
            
    def get_crew_list(self):
        if self.crew is None or self.crew == '':
            # Update the field to be a valid JSON array
            self.crew = '[]'
            return []
        try:
            # Try to parse as JSON
            return json.loads(self.crew)
        except (json.JSONDecodeError, TypeError):
            # If there's an error parsing, try to fix common issues
            try:
                # Replace single quotes with double quotes
                fixed_str = self.crew.replace("'", "\"")
                # Fix unescaped quotes in strings
                fixed_str = fixed_str.replace('\\"', '\\\\"')
                # Fix missing commas
                fixed_str = fixed_str.replace('"}{"', '"},{"')
                
                # Try to parse the fixed string
                return json.loads(fixed_str)
            except (json.JSONDecodeError, TypeError):
                # If still failing, try to extract data using regex
                import re
                import logging
                logger = logging.getLogger(__name__)
                
                try:
                    # Extract name fields using regex
                    name_pattern = r"['\"]name['\"]:\s*['\"]([^'\"]*)['\"]"
                    names = re.findall(name_pattern, self.crew)
                    if names:
                        logger.info(f"Extracted {len(names)} names from crew using regex")
                        return [{'name': name} for name in names]
                except Exception as regex_error:
                    logger.error(f"Error extracting names with regex: {str(regex_error)}")
                
                # If all else fails, reset to empty array
                self.crew = '[]'
                try:
                    db.session.commit()
                except:
                    db.session.rollback()
                return []
    
    def get_director(self):
        try:
            crew_list = self.get_crew_list()
            directors = []
            
            # Handle different crew data formats
            for person in crew_list:
                if isinstance(person, dict):
                    # Check for 'job' field with value 'Director'
                    if 'job' in person and person['job'] == 'Director' and 'name' in person:
                        directors.append(person['name'])
                    # Some APIs use 'department' instead of 'job'
                    elif 'department' in person and person['department'] == 'Directing' and 'name' in person:
                        directors.append(person['name'])
            
            return directors[0] if directors else None
        except Exception:
            # Return None if any error occurs
            return None
        
    def get_production_companies_list(self):
        if self.production_companies is None or self.production_companies == '':
            return []
        try:
            companies = json.loads(self.production_companies)
            return [company['name'] for company in companies if isinstance(company, dict) and 'name' in company]
        except (json.JSONDecodeError, TypeError):
            return []
            
    def to_dict(self):
        # Get the data from JSON fields
        try:
            # Import logging at the top level
            import logging
            logger = logging.getLogger(__name__)
            
            # Initialize empty lists for all fields
            cast_data = []
            crew_data = []
            genres_data = []
            keywords_data = []
            production_companies_data = []
            
            # Helper function to safely parse JSON
            def safe_parse_json(json_str, field_name):
                if not json_str:
                    return []
                
                try:
                    if isinstance(json_str, str):
                        # Try to fix common JSON formatting issues
                        if json_str.startswith("[{") and "'" in json_str:
                            # Replace single quotes with double quotes for JSON compatibility
                            fixed_str = json_str.replace("'", "\"")
                            return json.loads(fixed_str)
                        
                        # Try to parse as is
                        try:
                            return json.loads(json_str)
                        except json.JSONDecodeError as e:
                            # Try to fix common JSON issues
                            # Replace single quotes with double quotes
                            fixed_str = json_str.replace("'", "\"")
                            # Fix unescaped quotes in strings
                            fixed_str = fixed_str.replace('\\"', '\\\\"')
                            # Fix missing commas
                            fixed_str = fixed_str.replace('"}{"', '"},{"')
                            
                            # Fix truncated JSON strings
                            if field_name in ['cast', 'crew']:
                                # Check if the string is truncated
                                if not (fixed_str.endswith(']') or fixed_str.endswith('"}]')):
                                    # Try to find the last complete object
                                    last_complete_obj = fixed_str.rfind('"}')
                                    if last_complete_obj > 0:
                                        fixed_str = fixed_str[:last_complete_obj+2] + ']'
                                    else:
                                        # If we can't find a good truncation point, return empty array
                                        return []
                            
                            # Try to parse again
                            try:
                                return json.loads(fixed_str)
                            except json.JSONDecodeError:
                                # If still failing, try more aggressive fixes
                                if field_name in ['cast', 'crew']:
                                    # Try to extract just the first few valid objects
                                    import re
                                    pattern = r'\{"[^}]+"\s*:\s*"[^}]+"\}'
                                    matches = re.findall(pattern, fixed_str)
                                    if matches:
                                        # Construct a valid JSON array with the extracted objects
                                        valid_json = '[' + ','.join(matches) + ']'
                                        try:
                                            return json.loads(valid_json)
                                        except:
                                            pass
                                return []
                    elif isinstance(json_str, list):
                        return json_str
                    else:
                        return []
                except Exception as e:
                    logger.error(f"Error parsing {field_name}: {str(e)}")
                    # Log the problematic string for debugging
                    if isinstance(json_str, str):
                        logger.error(f"Problematic {field_name} string: {json_str[:100]}...")
                    
                    # Try to extract data using regex as a last resort
                    import re
                    if field_name in ['cast', 'crew', 'keywords', 'genres']:
                        try:
                            # Extract name fields using regex - improved pattern to handle more cases
                            name_patterns = [
                                r"'name':\s*'([^']*)'",  # Single quotes
                                r'"name":\s*"([^"]*)"',  # Double quotes
                                r"name['\"]?\s*:\s*['\"]([^'\"]*)['\"]"  # More flexible pattern
                            ]
                            
                            names = []
                            for pattern in name_patterns:
                                found_names = re.findall(pattern, json_str)
                                if found_names:
                                    names.extend(found_names)
                                    break  # Use the first successful pattern
                                    
                            if names:
                                logger.info(f"Extracted {len(names)} names from {field_name} using regex")
                                return [{'name': name} for name in names]
                        except Exception as regex_error:
                            logger.error(f"Error extracting names with regex: {str(regex_error)}")
                    
                    # Set to empty array if all parsing fails
                    setattr(self, field_name, '[]')
                    try:
                        db.session.commit()
                    except:
                        db.session.rollback()
                    return []
            
            # Parse all JSON fields
            cast_data = safe_parse_json(self.cast, 'cast')
            crew_data = safe_parse_json(self.crew, 'crew')
            genres_data = safe_parse_json(self.genres, 'genres')
            keywords_data = safe_parse_json(self.keywords, 'keywords')
            production_companies_data = safe_parse_json(self.production_companies, 'production_companies')
         
        
            # Extract names from cast with better error handling
            cast_names = []
            try:
                if isinstance(cast_data, list):
                    for person in cast_data:
                        if isinstance(person, dict) and 'name' in person:
                            cast_names.append(person['name'])
                        elif isinstance(person, str):
                            cast_names.append(person)
                elif isinstance(cast_data, dict) and 'name' in cast_data:
                    # Handle case where cast_data is a single object instead of a list
                    cast_names.append(cast_data['name'])
                elif isinstance(cast_data, str):
                    # Handle case where cast_data is a string
                    cast_names.append(cast_data)
            except Exception as e:
                logger.error(f"Error extracting cast names: {str(e)}")
                # If all else fails, set to empty list
                cast_names = []
            
            # Extract names from crew with better error handling
            crew_names = []
            try:
                if isinstance(crew_data, list):
                    for person in crew_data:
                        if isinstance(person, dict) and 'name' in person:
                            crew_names.append(person['name'])
                        elif isinstance(person, str):
                            crew_names.append(person)
                elif isinstance(crew_data, dict) and 'name' in crew_data:
                    # Handle case where crew_data is a single object instead of a list
                    crew_names.append(crew_data['name'])
                elif isinstance(crew_data, str):
                    # Handle case where crew_data is a string
                    crew_names.append(crew_data)
            except Exception as e:
                logger.error(f"Error extracting crew names: {str(e)}")
                # If all else fails, set to empty list
                crew_names = []
            
            # Extract names from genres
            genre_names = []
            for genre in genres_data:
                if isinstance(genre, dict) and 'name' in genre:
                    genre_names.append(genre['name'])
                elif isinstance(genre, str):
                    genre_names.append(genre)
            
            # Extract names from keywords
            keyword_names = []
            for keyword in keywords_data:
                if isinstance(keyword, dict) and 'name' in keyword:
                    keyword_names.append(keyword['name'])
                elif isinstance(keyword, str):
                    keyword_names.append(keyword)
            
            # Log the extracted keywords
            logger.debug(f"Extracted keywords: {keyword_names}")
            
            # Extract names from production companies
            company_names = []
            for company in production_companies_data:
                if isinstance(company, dict) and 'name' in company:
                    company_names.append(company['name'])
                elif isinstance(company, str):
                    company_names.append(company)
            
            # Get director from crew with better error handling
            director = []
            try:
                if isinstance(crew_data, list):
                    for person in crew_data:
                        if isinstance(person, dict):
                            # Check for director role
                            if ('job' in person and person['job'] == 'Director' and 'name' in person):
                                director.append(person['name'])
                            # Some APIs use 'department' instead of 'job'
                            elif ('department' in person and person['department'] == 'Directing' and 'name' in person):
                                director.append(person['name'])
                            # If no specific director info, just add all crew names
                            elif 'name' in person and not director:
                                director.append(person['name'])
                        elif isinstance(person, str) and not director:
                            director.append(person)
                elif isinstance(crew_data, dict) and 'name' in crew_data:
                    # Handle case where crew_data is a single object
                    director.append(crew_data['name'])
            except Exception as e:
                logger.error(f"Error extracting director: {str(e)}")
                # If all else fails, set to empty list
                director = []
            
            # Log the extracted data for debugging
            logger.debug(f"Extracted {len(cast_names)} cast members")
            logger.debug(f"Extracted {len(crew_names)} crew members")
            logger.debug(f"Extracted {len(genre_names)} genres")
            logger.debug(f"Extracted {len(keyword_names)} keywords")
            logger.debug(f"Extracted {len(company_names)} production companies")
            
            # Return the movie data as a dictionary
            return {
                'id': self.id,
                'tmdb_id': self.tmdb_id,
                'imdb_id': self.imdb_id,
                'title': self.title,
                'original_title': self.original_title,
                'overview': self.overview,
                'genres': genre_names,
                'release_date': self.release_date.isoformat() if self.release_date else None,
                'runtime': self.runtime,
                'popularity': self.popularity,
                'vote_average': self.vote_average,
                'vote_count': self.vote_count,
                'wr': self.wr,  # Weighted Rating
                'poster_path': self.poster_path,
                'production_companies': company_names,
                'keywords': keyword_names,
                'cast': cast_names,
                'crew': crew_names,
                'director': director,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None
            }
        except Exception as e:
            # Fallback in case of any error
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in to_dict: {str(e)}")
            return {
                'id': self.id,
                'tmdb_id': self.tmdb_id,
                'imdb_id': self.imdb_id,
                'title': self.title,
                'original_title': self.original_title,
                'overview': self.overview,
                'genres': [],
                'release_date': self.release_date.isoformat() if self.release_date else None,
                'runtime': self.runtime,
                'popularity': self.popularity,
                'vote_average': self.vote_average,
                'vote_count': self.vote_count,
                'wr': self.wr,
                'poster_path': self.poster_path,
                'production_companies': [],
                'keywords': [],
                'cast': [],
                'crew': [],
                'director': None,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None
            }