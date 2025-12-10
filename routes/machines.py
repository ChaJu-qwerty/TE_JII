from flask import Blueprint, request, jsonify
from db import get_db_connection
from datetime import datetime

machines_bp = Blueprint('machines', __name__)

# --- READ (Listar todas o una) ---
@machines_bp.route('/', methods=['GET'])
def get_machines():
    conn = get_db_connection()
    # Podemos filtrar por línea: /api/machines?line_id=Línea 1
    line_id = request.args.get('line_id')
    
    query = "SELECT * FROM machines"
    params = []
    
    if line_id:
        query += " WHERE line_id = ?"
        params.append(line_id)
        
    machines = conn.execute(query, params).fetchall()
    conn.close()
    
    return jsonify([dict(m) for m in machines])

@machines_bp.route('/<id>', methods=['GET'])
def get_machine_detail(id):
    conn = get_db_connection()
    machine = conn.execute("SELECT * FROM machines WHERE id = ?", (id,)).fetchone()
    conn.close()
    if machine:
        return jsonify(dict(machine))
    return jsonify({"error": "Machine not found"}), 404

# --- CREATE (Alta de máquina) ---
@machines_bp.route('/', methods=['POST'])
def create_machine():
    data = request.json
    # Validación básica
    if not data.get('id') or not data.get('name'):
        return jsonify({"error": "ID and Name are required"}), 400
        
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO machines (id, name, line_id, model, status, target_speed, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['id'], 
            data['name'], 
            data.get('line_id', 'General'), 
            data.get('model', 'Generic'),
            data.get('status', 'ACTIVE'),
            data.get('target_speed', 500.0),
            datetime.now().isoformat()
        ))
        conn.commit()
        return jsonify({"message": "Machine created successfully", "id": data['id']}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

# --- UPDATE (Editar máquina) ---
@machines_bp.route('/<id>', methods=['PUT'])
def update_machine(id):
    data = request.json
    conn = get_db_connection()
    
    # Construimos query dinámico
    fields = []
    values = []
    for key in ['name', 'line_id', 'model', 'status', 'target_speed']:
        if key in data:
            fields.append(f"{key} = ?")
            values.append(data[key])
            
    if not fields:
        return jsonify({"error": "No fields to update"}), 400
        
    values.append(id)
    sql = f"UPDATE machines SET {', '.join(fields)} WHERE id = ?"
    
    conn.execute(sql, values)
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Machine updated"})

# --- DELETE (Baja lógica o física) ---
@machines_bp.route('/<id>', methods=['DELETE'])
def delete_machine(id):
    conn = get_db_connection()
    # Opción A: Borrado físico (Cuidado: Rompe integridad referencial con logs)
    # conn.execute("DELETE FROM machines WHERE id = ?", (id,))
    
    # Opción B (Recomendada): Soft Delete
    conn.execute("UPDATE machines SET status = 'DECOMMISSIONED' WHERE id = ?", (id,))
    
    conn.commit()
    conn.close()
    return jsonify({"message": "Machine decommissioned"})