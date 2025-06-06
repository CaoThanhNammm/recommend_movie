from app.models.db import db
from app.models.cast import Cast

class CastService:
    @staticmethod
    def get_all_cast(page=1, per_page=20, search=None):
        """
        Get a paginated list of cast members with optional search.
        
        Args:
            page (int): The page number
            per_page (int): The number of items per page
            search (str, optional): Filter by name search
            
        Returns:
            tuple: (cast_members, total, pages, current_page)
        """
        # Base query
        query = Cast.query
        
        # Apply search filter
        if search:
            query = query.filter(Cast.name.like(f'%{search}%'))
        
        # Paginate results
        cast_pagination = query.order_by(Cast.name).paginate(page=page, per_page=per_page)
        
        return (
            cast_pagination.items,
            cast_pagination.total,
            cast_pagination.pages,
            cast_pagination.page
        )
    
  
        """
        Get a cast member by their ID.
        
        Args:
            cast_id (int): The ID of the cast member
            
        Returns:
            Cast: The cast object or None if not found
        """
        return Cast.query.get(cast_id)
    
    @staticmethod
    def create_cast(name, gender=None, profile_path=None):
        """
        Create a new cast member.
        
        Args:
            name (str): The name of the cast member
            gender (int, optional): The gender of the cast member
            profile_path (str, optional): The profile image path
            
        Returns:
            tuple: (cast, message)
                If successful, returns (Cast object, "Cast member created successfully")
                If error, returns (None, error_message)
        """
        try:
            # Create new cast member
            new_cast = Cast(
                name=name,
                gender=gender,
                profile_path=profile_path
            )
            db.session.add(new_cast)
            db.session.commit()
            
            return new_cast, "Cast member created successfully"
            
        except Exception as e:
            db.session.rollback()
            return None, f"Error creating cast member: {str(e)}"
    

        """
        Import cast members from a CSV file.
        
        Args:
            csv_path (str): Path to the CSV file
            batch_size (int): Number of records to commit at once
            
        Returns:
            tuple: (count, message)
                If successful, returns (number of cast members imported, "Cast members imported successfully")
                If error, returns (0, error_message)
        """
        import pandas as pd
        
        try:
            # Read CSV file
            df = pd.read_csv(csv_path)
            
            required_columns = ['id', 'name']
            if not all(col in df.columns for col in required_columns):
                return 0, f"CSV file must contain columns: {', '.join(required_columns)}"
            
            # Import cast members in batches
            count = 0
            total_rows = len(df)
            
            for i in range(0, total_rows, batch_size):
                batch_df = df.iloc[i:i+batch_size]
                
                for _, row in batch_df.iterrows():
                    # Check if cast member already exists
                    existing_cast = Cast.query.get(row['id'])
                    
                    if not existing_cast:
                        # Create new cast member
                        new_cast = Cast(
                            id=row['id'],
                            name=row['name'],
                            gender=row.get('gender'),
                            profile_path=row.get('profile_path')
                        )
                        db.session.add(new_cast)
                        count += 1
                
                # Commit batch
                db.session.commit()
                print(f"Imported {count}/{total_rows} cast members...")
            
            return count, "Cast members imported successfully"
            
        except Exception as e:
            db.session.rollback()
            return 0, f"Error importing cast members: {str(e)}"