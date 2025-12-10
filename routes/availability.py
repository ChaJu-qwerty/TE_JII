from flask import Blueprint, request, jsonify
from services.data_service import DataService

availability_bp = Blueprint('availability', __name__)
service = DataService()

@availability_bp.route('/stats', methods=['GET'])
def get_availability_stats():
    # Endpoint: /api/availability/stats?machine_id=MX01
    line_id = request.args.get('line_id')
    machine_id = request.args.get('machine_id')
    
    data = service.get_availability_stats(line_id, machine_id)
    return jsonify(data)