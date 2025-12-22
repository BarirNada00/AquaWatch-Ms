# Guide de Diagnostic - Problème de Synchronisation

## 🔍 Problème : Les anomalies ne sont pas copiées de TimescaleDB vers PostGIS

## Étapes de diagnostic

### 1. Vérifier que le service fonctionne

```bash
# Vérifier que le conteneur est démarré
docker-compose ps api-sig

# Voir les logs en temps réel
docker-compose logs -f api-sig
```

### 2. Exécuter le script de diagnostic

```bash
# Exécuter le script de test dans le conteneur
docker-compose exec api-sig python3 test_etl.py
```

Ce script va :
- ✅ Tester les connexions aux deux bases
- ✅ Vérifier que les tables existent
- ✅ Afficher les statistiques
- ✅ Tester une synchronisation manuelle

### 3. Vérifier manuellement dans TimescaleDB

```bash
# Se connecter à TimescaleDB
docker-compose exec timescaledb psql -U aquawatch -d aquawatch

# Vérifier les anomalies avec coordonnées
SELECT COUNT(*) FROM anomalies WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

# Voir quelques exemples
SELECT id, type, latitude, longitude, timestamp 
FROM anomalies 
WHERE latitude IS NOT NULL AND longitude IS NOT NULL 
LIMIT 5;
```

### 4. Vérifier manuellement dans PostGIS

```bash
# Se connecter à PostGIS
docker-compose exec postgis psql -U aquawatch -d aquawatch_gis

# Vérifier que la table existe
\dt anomalies_gis

# Compter les anomalies
SELECT COUNT(*) FROM anomalies_gis;

# Vérifier PostGIS
SELECT PostGIS_version();
```

## 🔧 Solutions aux problèmes courants

### Problème 1 : Aucune anomalie avec coordonnées dans TimescaleDB

**Symptôme** : Les logs montrent "Aucune anomalie à synchroniser"

**Solution** : Vérifier que les anomalies sont créées avec des coordonnées :

```sql
-- Dans TimescaleDB, vérifier
SELECT COUNT(*) FROM anomalies WHERE latitude IS NULL OR longitude IS NULL;
```

Si toutes les anomalies ont des coordonnées NULL, le problème vient de la création des anomalies dans `anomaly_detector`.

### Problème 2 : La table n'existe pas dans PostGIS

**Symptôme** : Erreur "Table 'anomalies_gis' n'existe pas"

**Solution** : La table sera créée automatiquement maintenant. Sinon, créer manuellement :

```sql
-- Dans PostGIS
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

CREATE INDEX idx_anomalies_gis_geom ON anomalies_gis USING GIST (geom);
CREATE INDEX idx_anomalies_gis_timestamp ON anomalies_gis (timestamp DESC);
```

### Problème 3 : Extension PostGIS non activée

**Symptôme** : Erreur lors de l'utilisation de fonctions PostGIS

**Solution** : L'extension sera activée automatiquement. Sinon :

```sql
-- Dans PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;
```

### Problème 4 : Erreurs de connexion

**Symptôme** : "Connection refused" ou "timeout"

**Solutions** :
1. Vérifier que les services sont démarrés : `docker-compose ps`
2. Vérifier les variables d'environnement dans `docker-compose.yml`
3. Vérifier la connectivité réseau : `docker-compose exec api-sig ping postgis`

### Problème 5 : L'ETL ne s'exécute pas

**Symptôme** : Aucun log de synchronisation

**Solutions** :
1. Vérifier les logs : `docker-compose logs api-sig`
2. Redémarrer le service : `docker-compose restart api-sig`
3. Vérifier que `start.py` lance bien l'ETL

## 📊 Vérification du fonctionnement

### Checklist

- [ ] Le conteneur `api-sig` est démarré
- [ ] Les logs montrent "DÉBUT DE LA SYNCHRONISATION"
- [ ] Les connexions aux deux bases réussissent
- [ ] La table `anomalies_gis` existe dans PostGIS
- [ ] Il y a des anomalies avec coordonnées dans TimescaleDB
- [ ] Les statistiques sont affichées dans les logs
- [ ] Le message "Synchronisation terminée" apparaît

### Commandes de vérification rapide

```bash
# Vérifier les logs récents
docker-compose logs --tail=50 api-sig | grep -E "(SYNCHRONISATION|anomalies|erreur|ERROR)"

# Compter dans TimescaleDB
docker-compose exec timescaledb psql -U aquawatch -d aquawatch -c "SELECT COUNT(*) FROM anomalies WHERE latitude IS NOT NULL AND longitude IS NOT NULL;"

# Compter dans PostGIS
docker-compose exec postgis psql -U aquawatch -d aquawatch_gis -c "SELECT COUNT(*) FROM anomalies_gis;"

# Tester l'API
curl http://localhost:8000/api/anomalies/geojson?days=7 | jq '.features | length'
```

## 🚀 Améliorations apportées

1. **Logs détaillés** : Affichage des statistiques avant/après synchronisation
2. **Création automatique** : La table et l'extension PostGIS sont créées si nécessaire
3. **Validation des coordonnées** : Vérification que les coordonnées sont dans des plages valides
4. **Synchronisation immédiate** : L'ETL s'exécute au démarrage, pas après 5 minutes
5. **Transaction** : Utilisation d'une transaction pour améliorer les performances
6. **Meilleure gestion d'erreurs** : Affichage détaillé des erreurs

## 📝 Notes importantes

- L'ETL synchronise uniquement les anomalies des **7 derniers jours** par défaut
- Les anomalies doivent avoir des **coordonnées non-null** pour être synchronisées
- Les coordonnées doivent être dans les plages valides : latitude [-90, 90], longitude [-180, 180]
- La synchronisation s'exécute **immédiatement au démarrage**, puis toutes les 5 minutes

## 🆘 Si le problème persiste

1. Exécuter le script de diagnostic : `docker-compose exec api-sig python3 test_etl.py`
2. Partager les logs complets : `docker-compose logs api-sig > logs.txt`
3. Vérifier les données dans TimescaleDB et PostGIS manuellement
4. Vérifier que les anomalies sont bien créées avec des coordonnées dans `anomaly_detector`
