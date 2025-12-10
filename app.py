import threading
from flask import Flask
from flask_cors import CORS
from db import init_db
from simulator import run_simulation

# Importar Blueprints
from routes.general import general_bp
from routes.performance import performance_bp
from routes.machines import machines_bp
from routes.quality import quality_bp        # <--- NUEVO
from routes.availability import availability_bp # <--- NUEVO
from routes.reports import reports_bp
from routes.ingest import ingest_bp
app = Flask(__name__)
CORS(app) 

#Rutas
app.register_blueprint(general_bp, url_prefix='/api/general')
app.register_blueprint(performance_bp, url_prefix='/api/performance')
app.register_blueprint(quality_bp, url_prefix='/api/quality')          # <--- NUEVO
app.register_blueprint(availability_bp, url_prefix='/api/availability') # <--- NUEVO
app.register_blueprint(reports_bp, url_prefix='/api/reports')
app.register_blueprint(machines_bp, url_prefix='/api/machines')
app.register_blueprint(ingest_bp, url_prefix='/api/ingest')

if __name__ == '__main__':
    init_db()

    sim_thread = threading.Thread(target=run_simulation, daemon=True)
    sim_thread.start()

    print("Backend API corriendo en http://localhost:5000")
    app.run(debug=True, port=5000, use_reloader=False)