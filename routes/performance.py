from flask import Blueprint, request, jsonify
from services.data_service import DataService

performance_bp = Blueprint('performance', __name__)
service = DataService()

@performance_bp.route('/stats', methods=['GET'])
def get_performance_stats():
    line_id = request.args.get('line_id')
    machine_id = request.args.get('machine_id')
    
    data = service.get_performance_stats(line_id, machine_id)
    return jsonify(data)