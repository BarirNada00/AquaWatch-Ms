# Étapes pour mettre en place l'API-SIG AquaWatch

## ✅ Analyse du code actuel

### Problèmes identifiés et corrigés :

1. **Problème principal** : Utilisation incorrecte de `asyncio.run()` dans une boucle
   - ✅ **Corrigé** : Utilisation d'une fonction `main_loop()` async avec gestion correcte de l'event loop

2. **API REST manquante** : Aucune API pour exposer les données
   - ✅ **Créé** : API FastAPI complète avec endpoints REST/GeoJSON

3. **Configuration Docker** : Service non configuré pour exposer l'API
   - ✅ **Corrigé** : Port 8000 exposé, healthcheck ajouté

## 📋 Étapes de déploiement

### Étape 1 : Vérifier les fichiers créés

Les fichiers suivants ont été créés/modifiés :

```
api-sig/
├── main.py              # API FastAPI avec endpoints REST/GeoJSON
├── etl_anomalies.py     # ETL corrigé (synchronisation TimescaleDB -> PostGIS)
├── start.py             # Script de démarrage (ETL + API)
├── requirements.txt      # Dépendances mises à jour
├── Dockerfile           # Dockerfile mis à jour
└── README.md            # Documentation
```

### Étape 2 : Reconstruire le conteneur

```bash
# Arrêter l'ancien service si nécessaire
docker-compose stop etl-anomalies

# Reconstruire le nouveau service api-sig
docker-compose build api-sig

# Démarrer le service
docker-compose up -d api-sig
```

### Étape 3 : Vérifier que le service fonctionne

```bash
# Vérifier les logs
docker-compose logs -f api-sig

# Tester l'endpoint de santé
curl http://localhost:8000/api/health

# Tester l'endpoint principal
curl http://localhost:8000/
```

### Étape 4 : Vérifier la synchronisation des données

```bash
# Vérifier que l'ETL fonctionne (dans les logs)
docker-compose logs api-sig | grep "Synchronisation"

# Tester l'endpoint GeoJSON
curl http://localhost:8000/api/anomalies/geojson?days=7

# Tester les zones
curl http://localhost:8000/api/zones/communes?days=30
```

### Étape 5 : Accéder à la documentation interactive

Ouvrir dans un navigateur :
- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

## 🎯 Endpoints disponibles

### 1. Cartes interactives (GeoJSON)
```
GET /api/anomalies/geojson
```
Paramètres :
- `days` : Nombre de jours (1-365, défaut: 7)
- `anomaly_type` : Type d'anomalie (optionnel)
- `sensor_id` : ID du capteur (optionnel)
- `bbox` : Bounding box (optionnel)

Exemple :
```bash
curl "http://localhost:8000/api/anomalies/geojson?days=7&anomaly_type=spike"
```

### 2. Zones rouges/vertes par commune
```
GET /api/zones/communes
```
Paramètres :
- `days` : Nombre de jours (1-365, défaut: 7)

Exemple :
```bash
curl "http://localhost:8000/api/zones/communes?days=30"
```

### 3. Historique de qualité
```
GET /api/historical
```
Paramètres :
- `days` : Nombre de jours (1-365, défaut: 30)
- `sensor_id` : ID du capteur (optionnel)
- `parameter` : Paramètre (optionnel)

Exemple :
```bash
curl "http://localhost:8000/api/historical?days=30&parameter=temperature"
```

### 4. Statistiques
```
GET /api/stats
```

Exemple :
```bash
curl http://localhost:8000/api/stats
```

## 🔧 Configuration GeoServer (optionnel)

Pour intégrer avec GeoServer :

1. Accéder à GeoServer : http://localhost:8080/geoserver
2. Créer un nouveau Store PostGIS :
   - Workspace : `aquawatch`
   - Data Source Name : `anomalies_gis`
   - Host : `postgis`
   - Port : `5432`
   - Database : `aquawatch_gis`
   - User : `aquawatch`
   - Password : `example`

3. Publier la couche `anomalies_gis` :
   - Nom : `anomalies`
   - SRS : `EPSG:4326`
   - Bounding Box : Calculer depuis les données

4. Créer des styles pour les zones :
   - Style "rouge" : zones critiques
   - Style "orange" : zones à surveiller
   - Style "vert" : zones normales

## 📊 Vérification du fonctionnement

### Checklist

- [ ] Le service `api-sig` démarre sans erreur
- [ ] L'endpoint `/api/health` retourne `{"status": "healthy"}`
- [ ] L'ETL synchronise les données (vérifier les logs)
- [ ] L'endpoint `/api/anomalies/geojson` retourne du GeoJSON valide
- [ ] L'endpoint `/api/zones/communes` retourne des zones
- [ ] La documentation Swagger est accessible

### Commandes de test

```bash
# Test complet
curl -s http://localhost:8000/api/health | jq
curl -s http://localhost:8000/api/anomalies/geojson?days=7 | jq '.features | length'
curl -s http://localhost:8000/api/zones/communes?days=30 | jq '.metadata'
curl -s http://localhost:8000/api/stats | jq
```

## 🐛 Dépannage

### Le service ne démarre pas
```bash
# Vérifier les logs
docker-compose logs api-sig

# Vérifier que PostGIS est accessible
docker-compose exec api-sig python3 -c "import asyncpg; import asyncio; asyncio.run(asyncpg.connect('postgresql://aquawatch:example@postgis:5432/aquawatch_gis'))"
```

### Aucune donnée dans les réponses
```bash
# Vérifier que la table existe dans PostGIS
docker-compose exec postgis psql -U aquawatch -d aquawatch_gis -c "SELECT COUNT(*) FROM anomalies_gis;"

# Vérifier que l'ETL synchronise
docker-compose logs api-sig | grep "anomalies ajoutées"
```

### Erreurs de connexion
```bash
# Vérifier que les services dépendants sont démarrés
docker-compose ps

# Vérifier la connectivité réseau
docker-compose exec api-sig ping -c 2 postgis
docker-compose exec api-sig ping -c 2 timescaledb
```

## 📝 Notes importantes

1. **Premier démarrage** : L'ETL peut prendre quelques minutes pour synchroniser les premières données
2. **Performance** : Les requêtes sont limitées à 10 000 résultats par défaut
3. **CORS** : Actuellement configuré pour accepter toutes les origines (à restreindre en production)
4. **Sécurité** : Les credentials sont en dur dans docker-compose.yml (à utiliser des secrets en production)

## 🎉 Résultat attendu

Une fois toutes les étapes complétées, vous devriez avoir :

✅ Une API REST fonctionnelle sur le port 8000  
✅ Des endpoints GeoJSON pour les cartes interactives  
✅ Des zones rouges/vertes calculées dynamiquement  
✅ Un historique de qualité accessible  
✅ Une documentation interactive (Swagger)  
✅ Une synchronisation automatique TimescaleDB → PostGIS  

L'API-SIG est maintenant conforme au cahier des charges ! 🚀
