import sqlite3
from config import DB_NAME

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Tabla Principal: Registros por segundo
    c.execute('''
        CREATE TABLE IF NOT EXISTS production_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            timestamp_iso TEXT,
            machine_id TEXT,
            line_id TEXT,
            
            -- Estado
            running INTEGER,        -- 1=ON, 0=OFF
            state TEXT,             -- 'RUN', 'STOP', 'IDLE'
            
            -- Métricas Físicas (Bulk Cable)
            line_speed REAL,        -- m/min
            extruder_rpm REAL,
            produced_length REAL,   -- Metros acumulados
            
            -- Calidad
            wire_diameter REAL,     -- mm
            scrap_reason TEXT,      -- NULL si es bueno, String si es malo
            
            -- OEE Instantáneo (0-100)
            oee_availability REAL,
            oee_performance REAL,
            oee_quality REAL,
            oee_global REAL
        )
    ''')
    
    # Tabla Eventos: Para bitácoras y paretos
    c.execute('''
        CREATE TABLE IF NOT EXISTS event_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            timestamp_iso TEXT,
            machine_id TEXT,
            line_id TEXT,
            event_type TEXT,      -- 'STOP', 'ALARM', 'MICROSTOP'
            category TEXT,        -- 'Quality', 'Performance', 'Availability'
            reason TEXT,          -- 'Atasco', 'Falta Material', etc.
            duration_sec REAL     -- Duración del evento
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS machines (
            id TEXT PRIMARY KEY,    -- Ej: 'MX-01' (Código único)
            name TEXT NOT NULL,     -- Ej: 'Extrusora Principal'
            line_id TEXT,           -- Ej: 'Línea 1'
            model TEXT,             -- Ej: 'Siemens S7-1200'
            status TEXT DEFAULT 'ACTIVE', -- 'ACTIVE', 'MAINTENANCE', 'DECOMMISSIONED'
            target_speed REAL DEFAULT 500.0,
            created_at TEXT
        )
    ''')
    
    # (Opcional) Seed inicial para no empezar vacío
    # Verificamos si está vacía para insertar defaults
    c.execute("SELECT count(*) FROM machines")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO machines (id, name, line_id, status) VALUES (?,?,?,?)", [
            ("MX-01", "Extrusora A", "Línea 1", "ACTIVE"),
            ("MX-02", "Extrusora B", "Línea 1", "ACTIVE"),
            ("MX-03", "Extrusora C", "Línea 2", "MAINTENANCE")
        ])
    conn.commit()
    conn.close()
    print(f"Base de datos {DB_NAME} inicializada.")