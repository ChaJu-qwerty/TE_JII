from db import get_db_connection
from datetime import datetime
import time
from config import TARGET_DIAMETER, TOLERANCE # Asegúrate de tener estas constantes en config.py

class IngestionService:
    
    def process_plc_data(self, payload):
        """
        Recibe datos crudos del PLC, calcula OEE y guarda en BD.
        Payload esperado:
        {
            "machine_id": "MX-01",
            "line_id": "Línea 1",
            "status": "RUN" | "STOP" | "ALARM",
            "speed": 450.5,       # m/min
            "diameter": 2.51,     # mm
            "total_length": 1500  # metros acumulados (opcional)
        }
        """
        conn = get_db_connection()
        
        # 1. Obtener configuración de la máquina (para calcular Performance)
        machine = conn.execute("SELECT target_speed FROM machines WHERE id = ?", (payload['machine_id'],)).fetchone()
        target_speed = machine['target_speed'] if machine else 500.0 # Default si no existe
        
        # 2. Cálculos de Calidad
        actual_diameter = float(payload.get('diameter', 0))
        is_scrap = False
        scrap_reason = None
        
        # Lógica simple de tolerancia
        if actual_diameter > (TARGET_DIAMETER + TOLERANCE) or actual_diameter < (TARGET_DIAMETER - TOLERANCE):
            is_scrap = True
            scrap_reason = "Diámetro fuera de tol."
            
        # 3. Cálculos de OEE
        # Disponibilidad (100 si corre, 0 si para)
        oee_avail = 100.0 if payload['status'] == 'RUN' else 0.0
        
        # Rendimiento (Velocidad Actual / Velocidad Meta)
        current_speed = float(payload.get('speed', 0))
        oee_perf = (current_speed / target_speed) * 100.0 if payload['status'] == 'RUN' else 0.0
        if oee_perf > 100: oee_perf = 100.0 # Cap al 100%
        
        # Calidad (100 si bueno, 0 si malo - Simplificado para flujo continuo)
        oee_qual = 0.0 if is_scrap else 100.0
        
        # OEE Global
        oee_global = (oee_avail * oee_perf * oee_qual) / 10000.0
        
        # 4. Insertar en Base de Datos
        timestamp = time.time()
        timestamp_iso = datetime.now().isoformat()
        
        conn.execute('''
            INSERT INTO production_log (
                timestamp, timestamp_iso, machine_id, line_id, 
                running, state, line_speed, produced_length, 
                wire_diameter, scrap_reason, 
                oee_availability, oee_performance, oee_quality, oee_global
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp, 
            timestamp_iso, 
            payload['machine_id'], 
            payload['line_id'],
            1 if payload['status'] == 'RUN' else 0, # running (bool/int)
            payload['status'],                      # state (text)
            current_speed,
            payload.get('total_length', 0),         # Si el PLC no manda acumulado, mandar 0 o calcular delta
            actual_diameter,
            scrap_reason,
            oee_avail, oee_perf, oee_qual, oee_global
        ))
        
        conn.commit()
        conn.close()
        
        return {
            "status": "success", 
            "calculated_oee": round(oee_global, 1),
            "timestamp": timestamp_iso
        }