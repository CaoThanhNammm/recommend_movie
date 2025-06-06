from app.models.db import db
from app.models.crew import Crew

class CrewService:
    @staticmethod
    def get_all_crew(page=1, per_page=20, search=None, department=None):
        """
        Get a paginated list of crew members with optional filtering.
        
        Args:
            page (int): The page number
            per_page (int): The number of items per page
            search (str, optional): Filter by name search
            department (str, optional): Filter by department
            
        Returns:
            tuple: (crew_members, total, pages, current_page)
        """
        # Base query
        query = Crew.query
        
        # Apply filters
        if search:
            query = query.filter(Crew.name.like(f'%{search}%'))
        
        if department:
            query = query.filter(Crew.department == department)
        
        # Paginate results
        crew_pagination = query.order_by(Crew.name).paginate(page=page, per_page=per_page)
        
        return (
            crew_pagination.items,
            crew_pagination.total,
            crew_pagination.pages,
            crew_pagination.page
        )
    

        """
        Get a crew member by their ID.
        
        Args:
            crew_id (int): The ID of the crew member
            
        Returns:
            Crew: The crew object or None if not found
        """
        return Crew.query.get(crew_id)
    

        """
        Get all unique departments.
        
        Returns:
            list: A list of unique department names
        """
        departments = db.session.query(Crew.department).distinct().filter(Crew.department.isnot(None)).all()
        return [dept[0] for dept in departments]
    
    @staticmethod
    def create_crew(name, department=None, job=None, gender=None, profile_path=None):
        """
        Create a new crew member.
        
        Args:
            name (str): The name of the crew member
            department (str, optional): The department of the crew member
            job (str, optional): The job title of the crew member
            gender (int, optional): The gender of the crew member
            profile_path (str, optional): The profile image path
            
        Returns:
            tuple: (crew, message)
                If successful, returns (Crew object, "Crew member created successfully")
                If error, returns (None, error_message)
        """
        try:
            # Create new crew member
            new_crew = Crew(
                name=name,
                department=department,
                job=job,
                gender=gender,
                profile_path=profile_path
            )
            db.session.add(new_crew)
            db.session.commit()
            
            return new_crew, "Crew member created successfully"
            
        except Exception as e:
            db.session.rollback()
            return None, f"Error creating crew member: {str(e)}"
    

        """
        Import crew members from a CSV file.
        
        Args:
            csv_path (str): Path to the CSV file
            batch_size (int): Number of records to commit at once
            
        Returns:
            tuple: (count, message)
                If successful, returns (number of crew members imported, "Crew members imported successfully")
                If error, returns (0, error_message)
        """
        import pandas as pd
        
        try:
            # Read CSV file
            df = pd.read_csv(csv_path)
            
            required_columns = ['id', 'name']
            if not all(col in df.columns for col in required_columns):
                return 0, f"CSV file must contain columns: {', '.join(required_columns)}"
            
            # Import crew members in batches
            count = 0
            total_rows = len(df)
            
            for i in range(0, total_rows, batch_size):
                batch_df = df.iloc[i:i+batch_size]
                
                for _, row in batch_df.iterrows():
                    # Check if crew member already exists
                    existing_crew = Crew.query.get(row['id'])
                    
                    if not existing_crew:
                        # Create new crew member
                        new_crew = Crew(
                            id=row['id'],
                            name=row['name'],
                            department=row.get('department'),
                            job=row.get('job'),
                            gender=row.get('gender'),
                            profile_path=row.get('profile_path')
                        )
                        db.session.add(new_crew)
                        count += 1
                
                # Commit batch
                db.session.commit()
                print(f"Imported {count}/{total_rows} crew members...")
            
            return count, "Crew members imported successfully"
            
        except Exception as e:
            db.session.rollback()
            return 0, f"Error importing crew members: {str(e)}"