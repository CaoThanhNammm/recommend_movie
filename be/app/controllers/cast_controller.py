from flask import Blueprint, request, jsonify
from app.services.cast_service import CastService

cast_bp = Blueprint('cast', __name__)

@cast_bp.route('/', methods=['GET'])
def get_cast_members():
    """Get a paginated list of cast members."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search')
    
    cast_members, total, pages, current_page = CastService.get_all_cast(
        page=page,
        per_page=per_page,
        search=search
    )
    
    return jsonify({
        'cast': [cast.to_dict() for cast in cast_members],
        'total': total,
        'pages': pages,
        'current_page': current_page
    }), 200


    """Get a cast member by ID."""
    cast = CastService.get_cast_by_id(cast_id)
    
    if not cast:
        return jsonify({'message': 'Cast member not found'}), 404
    
    return jsonify(cast.to_dict()), 200

@cast_bp.route('/', methods=['POST'])
def create_cast_member():
    """Create a new cast member."""
    data = request.get_json()
    
    # Validate input
    if not data or 'name' not in data:
        return jsonify({'message': 'Name is required'}), 400
    
    # Create cast member
    cast, message = CastService.create_cast(
        name=data['name'],
        gender=data.get('gender'),
        profile_path=data.get('profile_path')
    )
    
    if not cast:
        return jsonify({'message': message}), 400
    
    return jsonify({
        'message': message,
        'cast': cast.to_dict()
    }), 201


    """Import cast members from a CSV file."""
    data = request.get_json()
    
    # Validate input
    if not data or 'csv_path' not in data:
        return jsonify({'message': 'CSV path is required'}), 400
    
    # Import cast members
    batch_size = data.get('batch_size', 1000)
    count, message = CastService.import_cast_from_csv(
        csv_path=data['csv_path'],
        batch_size=batch_size
    )
    
    return jsonify({
        'message': message,
        'count': count
    }), 200 if count > 0 else 400