from flask import Blueprint, request, jsonify
from app.services.crew_service import CrewService

crew_bp = Blueprint('crew', __name__)

@crew_bp.route('/', methods=['GET'])
def get_crew_members():
    """Get a paginated list of crew members."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search')
    department = request.args.get('department')
    
    crew_members, total, pages, current_page = CrewService.get_all_crew(
        page=page,
        per_page=per_page,
        search=search,
        department=department
    )
    
    return jsonify({
        'crew': [crew.to_dict() for crew in crew_members],
        'total': total,
        'pages': pages,
        'current_page': current_page
    }), 200


    """Get a crew member by ID."""
    crew = CrewService.get_crew_by_id(crew_id)
    
    if not crew:
        return jsonify({'message': 'Crew member not found'}), 404
    
    return jsonify(crew.to_dict()), 200


@crew_bp.route('/', methods=['POST'])
def create_crew_member():
    """Create a new crew member."""
    data = request.get_json()
    
    # Validate input
    if not data or 'name' not in data:
        return jsonify({'message': 'Name is required'}), 400
    
    # Create crew member
    crew, message = CrewService.create_crew(
        name=data['name'],
        department=data.get('department'),
        job=data.get('job'),
        gender=data.get('gender'),
        profile_path=data.get('profile_path')
    )
    
    if not crew:
        return jsonify({'message': message}), 400
    
    return jsonify({
        'message': message,
        'crew': crew.to_dict()
    }), 201




