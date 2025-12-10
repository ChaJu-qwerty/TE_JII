from flask import Blueprint, request, jsonify
from services.ingestion_service import IngestionService

ingest_bp = Blueprint('ingest', __name__)
service = IngestionService()

@ingest_bp.route('/telemetry', methods=['POST'])
def ingest_telemetry():
    try:
        data = request.json
        
        # Validaciones básicas
        required_fields = ['machine_id', 'line_id', 'status', 'speed', 'diameter']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400
        
        result = service.process_plc_data(data)
        return jsonify(result), 201
        
    except Exception as e:
        print(f"Error en ingesta: {str(e)}")
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500