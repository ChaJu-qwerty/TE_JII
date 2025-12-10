import time
import numpy as np
import threading
from datetime import datetime
from db import get_db_connection
from config import TARGET_DIAMETER, TARGET_SPEED, TOLERANCE

class ExtruderSimulator:
    def __init__(self, machine_id, line_id):
        self.id = machine_id
        self.line_id = line_id
        self.tick = 0
        self.current_length = 0
        self.status = "RUN" # RUN, STOP, MICROSTOP
        
    def generate_step(self):
        self.tick += 1
        timestamp = time.time()
        
        # --- 1. Dinámica de Velocidad (Simular Micro-paros) ---
        # 5% de probabilidad de micro-paro (caída de velocidad)
        if np.random.rand() > 0.95: 
            self.status = "MICROSTOP"
            actual_speed = 0
            # Registramos el evento (simplificado)
            self.log_event("MICROSTOP", "Performance", "Atasco en Tolva", 15)
        elif np.random.rand() > 0.98:
             self.status = "STOP"
             actual_speed = 0
        else:
            self.status = "RUN"
            # Velocidad normal con un poco de ruido
            actual_speed = TARGET_SPEED + np.random.normal(0, 10) 
        
        # --- 2. Dinámica de Calidad (Diámetro) ---
        # Simular una onda senoidal para el diámetro (tendencia) + ruido
        base_diameter = TARGET_DIAMETER + (0.04 * np.sin(self.tick / 20))
        actual_diameter = base_diameter + np.random.normal(0, 0.01)
        
        # Determinar si es Scrap
        is_scrap = False
        scrap_reason = None
        
        if actual_diameter > (TARGET_DIAMETER + TOLERANCE) or actual_diameter < (TARGET_DIAMETER - TOLERANCE):
            is_scrap = True
            scrap_reason = "Diámetro fuera de tol."
        
        # --- 3. Cálculos OEE Instantáneos ---
        oee_avail = 100 if self.status != "STOP" else 0
        oee_perf = (actual_speed / TARGET_SPEED) * 100 if self.status == "RUN" else 0
        oee_qual = 0 if is_scrap else 100
        
        # OEE Global simple
        oee_global = (oee_avail * oee_perf * oee_qual) / 10000 
        
        self.current_length += (actual_speed / 60) # Metros por segundo

        # --- 4. Guardar en DB ---
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO production_log (
                timestamp, timestamp_iso, machine_id, line_id, 
                running, state, line_speed, produced_length, 
                wire_diameter, scrap_reason, 
                oee_availability, oee_performance, oee_quality, oee_global
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp, datetime.now().isoformat(), self.id, self.line_id,
            1 if self.status == "RUN" else 0, self.status, actual_speed, self.current_length,
            actual_diameter, scrap_reason,
            oee_avail, oee_perf, oee_qual, oee_global
        ))
        conn.commit()
        conn.close()

    def log_event(self, evt_type, cat, reason, duration):
        # Función auxiliar para registrar en event_log (usada raramente para no saturar)
        conn = get_db_connection()
        conn.execute("INSERT INTO event_log (timestamp, timestamp_iso, machine_id, line_id, event_type, category, reason, duration_sec) VALUES (?,?,?,?,?,?,?,?)",
                     (time.time(), datetime.now().isoformat(), self.id, self.line_id, evt_type, cat, reason, duration))
        conn.commit()
        conn.close()

def run_simulation():
    machines = [
        ExtruderSimulator("MX-01", "Línea 1"),
        ExtruderSimulator("MX-02", "Línea 1"),
        ExtruderSimulator("MX-03", "Línea 2")
    ]
    print("--- Simulador de Planta Iniciado ---")
    while True:
        for m in machines:
            m.generate_step()
        time.sleep(1) # 1 Tick por segundo