from db import get_db_connection

class DataService:
    
    def _build_filter_clause(self, line_id=None, machine_id=None):
        """Helper para construir el WHERE de SQL dinámicamente."""
        clauses = []
        params = []
        if line_id:
            clauses.append("line_id = ?")
            params.append(line_id)
        if machine_id:
            clauses.append("machine_id = ?")
            params.append(machine_id)
        
        where_sql = "WHERE " + " AND ".join(clauses) if clauses else ""
        return where_sql, tuple(params)

    def get_general_kpis(self, line_id=None, machine_id=None):
        """Calcula los promedios de OEE basados en filtros."""
        conn = get_db_connection()
        where_sql, params = self._build_filter_clause(line_id, machine_id)
        
        # Tomamos los últimos 300 registros para el "tiempo real"
        query = f'''
            SELECT 
                AVG(oee_availability) as avail,
                AVG(oee_performance) as perf,
                AVG(oee_quality) as qual,
                AVG(oee_global) as oee,
                SUM(line_speed/60) as total_meters 
            FROM (SELECT * FROM production_log {where_sql} ORDER BY id DESC LIMIT 300)
        '''
        row = conn.execute(query, params).fetchone()
        conn.close()
        
        return {
            "availability": round(row['avail'] or 0, 1),
            "performance": round(row['perf'] or 0, 1),
            "quality": round(row['qual'] or 0, 1),
            "global": round(row['oee'] or 0, 1),
            "production_volume": int(row['total_meters'] or 0) 
        }

    def get_performance_stats(self, line_id=None, machine_id=None):
        conn = get_db_connection()
        where_sql, params = self._build_filter_clause(line_id, machine_id)
        
        # 1. Gráfica de Estabilidad (Speed vs Time)
        query_trend = f"SELECT timestamp_iso as time, line_speed as actual FROM production_log {where_sql} ORDER BY id DESC LIMIT 30"
        trend_rows = conn.execute(query_trend, params).fetchall()
        
        # 2. Pareto de Micro-paros
        query_pareto = f'''
            SELECT reason, COUNT(*) as count 
            FROM event_log 
            WHERE category='Performance' {where_sql.replace('WHERE', 'AND')} 
            GROUP BY reason ORDER BY count DESC LIMIT 5
        '''
        pareto_rows = conn.execute(query_pareto, params).fetchall() 
        
        conn.close()
        
        return {
            "hourly_stability": [{"time": r['time'][11:16], "actual": r['actual'], "target": 500} for r in trend_rows][::-1],
            "top_microstops": [{"cause": r['reason'], "count": r['count']} for r in pareto_rows]
        }

    def get_quality_stats(self, line_id=None, machine_id=None):
        conn = get_db_connection()
        where_sql, params = self._build_filter_clause(line_id, machine_id)
        
        # Construcción dinámica de WHERE para evitar errores de sintaxis
        if where_sql:
            diameter_where = f"{where_sql} AND running = 1"
            scrap_where = where_sql.replace("WHERE", "WHERE scrap_reason IS NOT NULL AND")
        else:
            diameter_where = "WHERE running = 1"
            scrap_where = "WHERE scrap_reason IS NOT NULL"

        # 1. Carta de Control
        query_diameter = f'''
            SELECT id, timestamp_iso, wire_diameter 
            FROM production_log 
            {diameter_where} 
            ORDER BY id DESC LIMIT 50
        '''
        diameter_rows = conn.execute(query_diameter, params).fetchall()
        
        # 2. Pareto de Defectos
        query_pareto = f'''
            SELECT scrap_reason, COUNT(*) as count 
            FROM production_log 
            {scrap_where}
            GROUP BY scrap_reason 
            ORDER BY count DESC LIMIT 5
        '''
        pareto_rows = conn.execute(query_pareto, params).fetchall()

        # 3. Bitácora de Scrap
        query_log = f'''
            SELECT timestamp_iso, line_id, scrap_reason, produced_length 
            FROM production_log 
            {scrap_where}
            ORDER BY id DESC LIMIT 10
        '''
        log_rows = conn.execute(query_log, params).fetchall()
        
        conn.close()
        
        return {
            "control_chart_diameter": [
                {"sample": str(r['id']), "value": r['wire_diameter'], "time": r['timestamp_iso'][11:19]} 
                for r in diameter_rows
            ][::-1],
            "defects_pareto": [
                {"name": r['scrap_reason'], "count": r['count']} for r in pareto_rows
            ],
            "scrap_log": [
                {
                    "lote": f"L-{int(r['produced_length'])}", 
                    "motivo": r['scrap_reason'],
                    "qty": 1 
                } for r in log_rows
            ]
        }

    def get_availability_stats(self, line_id=None, machine_id=None):
        conn = get_db_connection()
        where_sql, params = self._build_filter_clause(line_id, machine_id)
        
        # 1. Timeline de Estados (La tabla que ya tenías)
        query_states = f'''
            SELECT timestamp_iso, event_type, duration_sec, reason
            FROM event_log
            WHERE category IN ('Availability', 'Performance') 
            {where_sql.replace('WHERE', 'AND')}
            ORDER BY id DESC LIMIT 20
        '''
        state_rows = conn.execute(query_states, params).fetchall()

        # 2. Estado de la Flota (Para el componente FleetStatus)
        # Obtenemos la última lectura de cada máquina
        fleet_query = "SELECT id, name, status FROM machines"
        fleet_rows = conn.execute(fleet_query).fetchall()
        
        fleet_status = []
        for machine in fleet_rows:
            # Buscamos si está corriendo en el log de producción
            last_log = conn.execute("SELECT running, oee_global FROM production_log WHERE machine_id = ? ORDER BY id DESC LIMIT 1", (machine['id'],)).fetchone()
            
            is_running = last_log['running'] == 1 if last_log else False
            oee = last_log['oee_global'] if last_log else 0
            
            fleet_status.append({
                "id": machine['id'],
                "name": machine['name'],
                "status": "RUNNING" if is_running else "STOPPED",
                "oee": round(oee, 1)
            })

        conn.close()
        
        # 3. KPIs Simulados (En un futuro se calcularían con fórmulas de MTBF/MTTR reales)
        # Por ahora enviamos datos que tengan sentido para el dashboard
        kpis = {
            "mtbf": "45h",
            "mttr": "15m",
            "uptime": "92.5%",
            "trend_up": True
        }
        
        # 4. Datos de Tendencia (Simulados para el gráfico de línea)
        trend_data = [
            {"day": "Lunes", "value": 91}, {"day": "Martes", "value": 93},
            {"day": "Miércoles", "value": 89}, {"day": "Jueves", "value": 94},
            {"day": "Viernes", "value": 92}
        ]

        return {
            "kpis": kpis,
            "trend": trend_data,
            "fleet_status": fleet_status,
            "downtime_log": [
                {
                    "time": r['timestamp_iso'][11:16], 
                    "status": r['event_type'], 
                    "reason": r['reason'],
                    "duration": f"{int(r['duration_sec'])}s" if r['duration_sec'] else "0s"
                } for r in state_rows
            ]
        }
    
    def get_full_reports(self, line_id=None, machine_id=None, limit=100):
        conn = get_db_connection()
        where_sql, params = self._build_filter_clause(line_id, machine_id)
        
        query = f'''
            SELECT id, timestamp_iso, machine_id, line_id, 
                   event_type, category, reason, duration_sec 
            FROM event_log
            {where_sql}
            ORDER BY id DESC 
            LIMIT ?
        '''
        
        query_params = list(params)
        query_params.append(limit)
        
        rows = conn.execute(query, tuple(query_params)).fetchall()
        conn.close()
        
        return [
            {
                "id": r['id'],
                "date": r['timestamp_iso'][:10],
                "time": r['timestamp_iso'][11:19],
                "machine": f"{r['machine_id']} ({r['line_id']})",
                "type": r['event_type'],
                "category": r['category'],
                "message": r['reason'],
                "duration": f"{int(r['duration_sec'])}s" if r['duration_sec'] else "-"
            }
            for r in rows
        ]