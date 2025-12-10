from flask import Blueprint, request, jsonify
from services.data_service import DataService

quality_bp = Blueprint('quality', __name__)
service = DataService()

@quality_bp.route('/stats', methods=['GET'])
def get_quality_stats():
    # Endpoint: /api/quality/stats?line_id=L1
    line_id = request.args.get('line_id')
    machine_id = request.args.get('machine_id')
    
    data = service.get_quality_stats(line_id, machine_id)
    return jsonify(data)