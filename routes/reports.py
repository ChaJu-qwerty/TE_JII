from flask import Blueprint, request, jsonify
from services.data_service import DataService
from db import get_db_connection
import time
from datetime import datetime

reports_bp = Blueprint('reports', __name__)
service = DataService()

@reports_bp.route('/history', methods=['GET'])
def get_reports_history():
    # Endpoint: /api/reports/history?machine_id=MX01&limit=50
    line_id = request.args.get('line_id')
    machine_id = request.args.get('machine_id')
    limit = request.args.get('limit', 100, type=int)
    
    data = service.get_full_reports(line_id, machine_id, limit)
    return jsonify(data)

# --- Endpoint Extra: SIMULADOR DE INCIDENTES (Botón de Pánico) ---
# Esto te servirá para probar tu dashboard en tiempo real.
# Puedes llamar a este endpoint desde Postman o un botón "Simular Falla" en el Frontend.
@reports_bp.route('/create', methods=['POST'])
def create_manual_report():
    data = request.json
    # Esperamos: { "machine_id": "MX-01", "line_id": "Línea 1", "reason": "Falla Motor", "type": "STOP" }
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO event_log 
        (timestamp, timestamp_iso, machine_id, line_id, event_type, category, reason, duration_sec)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        time.time(), 
        datetime.now().isoformat(), 
        data.get('machine_id'), 
        data.get('line_id'), 
        data.get('type', 'INFO'), 
        'Manual', 
        data.get('reason', 'Reporte Manual'), 
        0
    ))
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success", "message": "Incidente registrado manualmente"}), 201