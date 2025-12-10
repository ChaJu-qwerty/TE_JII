from flask import Blueprint, request, jsonify
from services.data_service import DataService

general_bp = Blueprint('general', __name__)
service = DataService()

@general_bp.route('/kpis', methods=['GET'])
def get_kpis():
    # Leemos los Query Params: ?line_id=L1&machine_id=MX01
    line_id = request.args.get('line_id')
    machine_id = request.args.get('machine_id')
    
    data = service.get_general_kpis(line_id, machine_id)
    return jsonify(data)