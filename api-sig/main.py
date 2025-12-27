# AquaWatch/api-sig/main.py
# API REST/GeoJSON pour servir les données environnementales
import asyncio
import asyncpg
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from py_eureka_client.eureka_client import EurekaClient

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variables d'environnement
POSTGIS_DSN = os.getenv(
    "POSTGIS_DSN",
    "postgresql://aquawatch:example@postgis:5432/aquawatch_gis"
)

# Pool de connexions PostGIS
db_pool: Optional[asyncpg.Pool] = None

# Application FastAPI
app = FastAPI(
    title="AquaWatch API-SIG",
    description="API REST/GeoJSON pour les données environnementales",
    version="1.0.0"
)

# Initialize Eureka client
eureka_client = EurekaClient(
    app_name='api-sig',
    eureka_server="http://eureka-server:8761/eureka/",
    instance_host='api-sig',
    instance_port=8001
)
eureka_client.register()

# CORS pour permettre l'accès depuis les interfaces web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Modèles Pydantic
class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: dict
    properties: dict


class GeoJSONResponse(BaseModel):
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]


# Initialisation de la connexion à la base de données
@app.on_event("startup")
async def startup():
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(
            POSTGIS_DSN,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        logger.info("✓ Connexion au pool PostGIS établie")
    except Exception as e:
        logger.error(f"Erreur de connexion à PostGIS: {e}")
        raise


@app.on_event("shutdown")
async def shutdown():
    global db_pool
    if db_pool:
        await db_pool.close()
        logger.info("Connexion PostGIS fermée")


# ============================================
# ENDPOINTS PRINCIPAUX
# ============================================

@app.get("/")
async def root():
    """Point d'entrée de l'API"""
    return {
        "service": "AquaWatch API-SIG",
        "version": "1.0.0",
        "endpoints": {
            "anomalies_geojson": "/api/anomalies/geojson",
            "zones_communes": "/api/zones/communes",
            "historical": "/api/historical",
            "health": "/api/health"
        }
    }


@app.get("/api/health")
async def health_check():
    """Vérification de l'état de l'API et de la connexion PostGIS"""
    try:
        if not db_pool:
            return {"status": "error", "message": "Pool de connexion non initialisé"}
        
        async with db_pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            if result == 1:
                return {
                    "status": "healthy",
                    "database": "connected",
                    "timestamp": datetime.utcnow().isoformat()
                }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@app.get("/api/anomalies/geojson", response_model=GeoJSONResponse)
async def get_anomalies_geojson(
    days: int = Query(7, ge=1, le=365, description="Nombre de jours d'historique"),
    anomaly_type: Optional[str] = Query(None, description="Filtrer par type d'anomalie"),
    sensor_id: Optional[str] = Query(None, description="Filtrer par ID de capteur"),
    bbox: Optional[str] = Query(None, description="Bounding box: min_lon,min_lat,max_lon,max_lat")
):
    """
    Retourne les anomalies en format GeoJSON pour les cartes interactives.
    
    - **days**: Nombre de jours d'historique (1-365)
    - **anomaly_type**: Type d'anomalie (spike, drift, dropout, etc.)
    - **sensor_id**: ID du capteur
    - **bbox**: Bounding box pour filtrer spatialement
    """
    if not db_pool:
        raise HTTPException(status_code=503, detail="Service non disponible")
    
    try:
        # Construction de la requête SQL avec paramètres positionnels
        param_count = 1
        params = []
        conditions = []
        
        # Condition de base pour la date
        conditions.append(f"timestamp > NOW() - INTERVAL '${param_count} days'")
        params.append(days)
        param_count += 1
        
        if anomaly_type:
            conditions.append(f"type = ${param_count}")
            params.append(anomaly_type)
            param_count += 1
        
        if sensor_id:
            conditions.append(f"sensor_id = ${param_count}")
            params.append(sensor_id)
            param_count += 1
        
        if bbox:
            try:
                coords = [float(x.strip()) for x in bbox.split(',')]
                if len(coords) == 4:
                    conditions.append(
                        f"ST_Within(geom, ST_MakeEnvelope(${param_count}, ${param_count + 1}, ${param_count + 2}, ${param_count + 3}, 4326))"
                    )
                    params.extend(coords)
                    param_count += 4
            except ValueError:
                pass  # Ignorer les bbox invalides
        
        query = f"""
            SELECT 
                id,
                type,
                timestamp,
                sensor_id,
                parameter,
                value,
                message,
                ST_AsGeoJSON(geom)::json as geometry
            FROM anomalies_gis
            WHERE {' AND '.join(conditions)}
            ORDER BY timestamp DESC
            LIMIT 10000
        """
        
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        features = []
        for row in rows:
            feature = {
                "type": "Feature",
                "geometry": row['geometry'],
                "properties": {
                    "id": row['id'],
                    "type": row['type'],
                    "timestamp": row['timestamp'].isoformat() if row['timestamp'] else None,
                    "sensor_id": row['sensor_id'],
                    "parameter": row['parameter'],
                    "value": float(row['value']) if row['value'] is not None else None,
                    "message": row['message']
                }
            }
            features.append(feature)
        
        return {
            "type": "FeatureCollection",
            "features": features
        }
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des anomalies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


@app.get("/api/zones/communes")
async def get_zones_communes(
    days: int = Query(7, ge=1, le=365, description="Nombre de jours d'historique")
):
    """
    Retourne les zones rouges/vertes par commune basées sur la densité d'anomalies.
    
    - **days**: Nombre de jours d'historique pour calculer les zones
    """
    if not db_pool:
        raise HTTPException(status_code=503, detail="Service non disponible")
    
    try:
        # Requête pour calculer la densité d'anomalies par zone
        # On utilise une grille spatiale pour simuler les communes
        query = """
            WITH grid AS (
                SELECT 
                    ST_MakeEnvelope(
                        FLOOR(ST_X(geom) * 10) / 10.0,
                        FLOOR(ST_Y(geom) * 10) / 10.0,
                        (FLOOR(ST_X(geom) * 10) + 1) / 10.0,
                        (FLOOR(ST_Y(geom) * 10) + 1) / 10.0,
                        4326
                    ) as cell,
                    COUNT(*) as anomaly_count
                FROM anomalies_gis
                WHERE timestamp > NOW() - INTERVAL '$1 days'
                GROUP BY cell
            )
            SELECT 
                ST_AsGeoJSON(cell)::json as geometry,
                anomaly_count,
                CASE 
                    WHEN anomaly_count >= 10 THEN 'rouge'
                    WHEN anomaly_count >= 5 THEN 'orange'
                    ELSE 'vert'
                END as zone_status
            FROM grid
            ORDER BY anomaly_count DESC
        """
        
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(query, days)
        
        features = []
        for row in rows:
            feature = {
                "type": "Feature",
                "geometry": row['geometry'],
                "properties": {
                    "anomaly_count": row['anomaly_count'],
                    "zone_status": row['zone_status'],
                    "status_label": {
                        "rouge": "Zone critique",
                        "orange": "Zone à surveiller",
                        "vert": "Zone normale"
                    }.get(row['zone_status'], "Inconnu")
                }
            }
            features.append(feature)
        
        return {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {
                "total_zones": len(features),
                "zones_rouges": sum(1 for f in features if f['properties']['zone_status'] == 'rouge'),
                "zones_oranges": sum(1 for f in features if f['properties']['zone_status'] == 'orange'),
                "zones_vertes": sum(1 for f in features if f['properties']['zone_status'] == 'vert')
            }
        }
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des zones: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


@app.get("/api/historical")
async def get_historical_quality(
    days: int = Query(30, ge=1, le=365, description="Nombre de jours d'historique"),
    sensor_id: Optional[str] = Query(None, description="Filtrer par ID de capteur"),
    parameter: Optional[str] = Query(None, description="Filtrer par paramètre (temperature, pressure, etc.)")
):
    """
    Retourne l'historique de qualité de l'eau.
    
    - **days**: Nombre de jours d'historique
    - **sensor_id**: ID du capteur
    - **parameter**: Paramètre à analyser
    """
    if not db_pool:
        raise HTTPException(status_code=503, detail="Service non disponible")
    
    try:
        param_count = 1
        params = []
        conditions = []
        
        # Condition de base pour la date
        conditions.append(f"timestamp > NOW() - INTERVAL '${param_count} days'")
        params.append(days)
        param_count += 1
        
        if sensor_id:
            conditions.append(f"sensor_id = ${param_count}")
            params.append(sensor_id)
            param_count += 1
        
        if parameter:
            conditions.append(f"parameter = ${param_count}")
            params.append(parameter)
            param_count += 1
        
        query = f"""
            SELECT 
                DATE(timestamp) as date,
                parameter,
                COUNT(*) as anomaly_count,
                AVG(value) as avg_value,
                MIN(value) as min_value,
                MAX(value) as max_value
            FROM anomalies_gis
            WHERE {' AND '.join(conditions)}
            GROUP BY DATE(timestamp), parameter
            ORDER BY date DESC, parameter
        """
        
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        historical_data = []
        for row in rows:
            historical_data.append({
                "date": row['date'].isoformat() if row['date'] else None,
                "parameter": row['parameter'],
                "anomaly_count": row['anomaly_count'],
                "statistics": {
                    "avg_value": float(row['avg_value']) if row['avg_value'] is not None else None,
                    "min_value": float(row['min_value']) if row['min_value'] is not None else None,
                    "max_value": float(row['max_value']) if row['max_value'] is not None else None
                }
            })
        
        return {
            "period_days": days,
            "total_records": len(historical_data),
            "data": historical_data
        }
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'historique: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


@app.get("/api/stats")
async def get_statistics():
    """Retourne des statistiques globales sur les anomalies"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Service non disponible")
    
    try:
        async with db_pool.acquire() as conn:
            total = await conn.fetchval("SELECT COUNT(*) FROM anomalies_gis")
            last_7_days = await conn.fetchval(
                "SELECT COUNT(*) FROM anomalies_gis WHERE timestamp > NOW() - INTERVAL '7 days'"
            )
            by_type = await conn.fetch(
                "SELECT type, COUNT(*) as count FROM anomalies_gis GROUP BY type"
            )
            by_parameter = await conn.fetch(
                "SELECT parameter, COUNT(*) as count FROM anomalies_gis WHERE parameter IS NOT NULL GROUP BY parameter"
            )
        
        return {
            "total_anomalies": total,
            "last_7_days": last_7_days,
            "by_type": {row['type']: row['count'] for row in by_type},
            "by_parameter": {row['parameter']: row['count'] for row in by_parameter if row['parameter']}
        }
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des statistiques: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
