# API-SIG AquaWatch

## Description

L'API-SIG (Système d'Information Géographique) fournit les couches de données environnementales aux utilisateurs externes via une interface cartographique.

## Technologies

- **FastAPI** : Framework REST API moderne et performant
- **PostGIS** : Base de données spatiale pour stocker les anomalies géolocalisées
- **GeoJSON** : Format de données pour les cartes interactives
- **GeoServer** : Serveur de cartes (configuré séparément)

## Fonctionnalités

### 1. Cartes interactives
- **Endpoint** : `GET /api/anomalies/geojson`
- Retourne les anomalies en format GeoJSON pour affichage sur cartes
- Filtres disponibles : jours, type d'anomalie, capteur, bounding box

### 2. Zones rouges/vertes par commune
- **Endpoint** : `GET /api/zones/communes`
- Calcule la densité d'anomalies par zone géographique
- Classification : rouge (critique), orange (à surveiller), vert (normal)

### 3. Historiques de qualité
- **Endpoint** : `GET /api/historical`
- Retourne l'historique de qualité de l'eau
- Statistiques par jour et par paramètre

### 4. Statistiques
- **Endpoint** : `GET /api/stats`
- Statistiques globales sur les anomalies

## Architecture

Le service API-SIG combine deux composants :

1. **ETL de synchronisation** (`etl_anomalies.py`)
   - Synchronise les anomalies de TimescaleDB vers PostGIS
   - Exécution toutes les 5 minutes
   - Crée automatiquement la géométrie spatiale (Point) à partir des coordonnées

2. **API REST/GeoJSON** (`main.py`)
   - Expose les endpoints REST
   - Convertit les données PostGIS en GeoJSON
   - Gère les connexions via un pool de connexions

## Endpoints disponibles

### Documentation interactive
- **Swagger UI** : `http://localhost:8000/docs`
- **ReDoc** : `http://localhost:8000/redoc`

### Endpoints principaux

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/` | GET | Point d'entrée avec liste des endpoints |
| `/api/health` | GET | Vérification de l'état de l'API |
| `/api/anomalies/geojson` | GET | Anomalies en format GeoJSON |
| `/api/zones/communes` | GET | Zones rouges/vertes par commune |
| `/api/historical` | GET | Historique de qualité d'eau |
| `/api/stats` | GET | Statistiques globales |

## Exemples d'utilisation

### Récupérer les anomalies des 7 derniers jours
```bash
curl http://localhost:8000/api/anomalies/geojson?days=7
```

### Filtrer par type d'anomalie
```bash
curl http://localhost:8000/api/anomalies/geojson?days=7&anomaly_type=spike
```

### Récupérer les zones par commune
```bash
curl http://localhost:8000/api/zones/communes?days=30
```

### Historique de qualité
```bash
curl http://localhost:8000/api/historical?days=30&parameter=temperature
```

## Déploiement

### Avec Docker Compose

Le service est configuré dans `docker-compose.yml` :

```yaml
api-sig:
  build:
    context: ./api-sig
  ports:
    - "8000:8000"
  environment:
    POSTGIS_DSN: "postgresql://aquawatch:example@postgis:5432/aquawatch_gis"
    TIMESCALEDB_DSN: "postgresql://aquawatch:example@timescaledb:5432/aquawatch"
```

### Démarrage

```bash
# Reconstruire et démarrer
docker-compose up -d --build api-sig

# Voir les logs
docker-compose logs -f api-sig

# Vérifier l'état
curl http://localhost:8000/api/health
```

## Structure des données

### Table `anomalies_gis` (PostGIS)

```sql
CREATE TABLE anomalies_gis (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    sensor_id TEXT,
    parameter TEXT,
    value NUMERIC,
    message TEXT,
    geom GEOMETRY(Point, 4326) NOT NULL
);
```

### Format GeoJSON

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [longitude, latitude]
      },
      "properties": {
        "id": "anomaly-id",
        "type": "spike",
        "timestamp": "2024-01-01T12:00:00",
        "sensor_id": "sensor-01",
        "parameter": "temperature",
        "value": 45.5,
        "message": "Température anormalement élevée"
      }
    }
  ]
}
```

## Intégration avec GeoServer

GeoServer peut être configuré pour utiliser PostGIS comme source de données :

1. Créer un nouveau Store PostGIS dans GeoServer
2. Configurer la connexion vers `postgis:5432/aquawatch_gis`
3. Publier la table `anomalies_gis` comme couche WMS/WFS
4. Utiliser les styles pour colorer les zones selon le statut

## Monitoring

- **Health check** : `/api/health`
- **Logs** : Accessibles via `docker-compose logs api-sig`
- **Métriques** : Endpoint `/api/stats` pour les statistiques

## Notes importantes

1. L'ETL synchronise uniquement les anomalies avec des coordonnées valides (latitude/longitude non null)
2. Les anomalies sont synchronisées pour les 7 derniers jours par défaut
3. Les zones rouges/vertes utilisent une grille spatiale (peut être adapté pour utiliser de vraies communes)
4. CORS est activé pour permettre l'accès depuis les interfaces web (à restreindre en production)
