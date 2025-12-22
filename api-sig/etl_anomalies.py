# AquaWatch/api-sig/etl_anomalies.py
import asyncio
import asyncpg
import logging
import os

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variables d'environnement (à définir dans docker-compose.yml ou .env)
TIMESCALEDB_DSN = os.getenv(
    "TIMESCALEDB_DSN",
    "postgresql://aquawatch:example@timescaledb:5432/aquawatch"
)
POSTGIS_DSN = os.getenv(
    "POSTGIS_DSN",
    "postgresql://aquawatch:example@postgis:5432/aquawatch_gis"
)

async def sync_anomalies():
    """Synchronise les anomalies de TimescaleDB vers PostGIS (table spatiale)."""
    src = None
    dst = None
    
    try:
        # Connexion aux deux bases
        logger.info("=" * 60)
        logger.info("DÉBUT DE LA SYNCHRONISATION")
        logger.info("=" * 60)
        
        logger.info(f"Connexion à TimescaleDB: {TIMESCALEDB_DSN.split('@')[1] if '@' in TIMESCALEDB_DSN else 'N/A'}")
        src = await asyncpg.connect(TIMESCALEDB_DSN)
        logger.info("✓ Connexion à TimescaleDB réussie")
        
        logger.info(f"Connexion à PostGIS: {POSTGIS_DSN.split('@')[1] if '@' in POSTGIS_DSN else 'N/A'}")
        dst = await asyncpg.connect(POSTGIS_DSN)
        logger.info("✓ Connexion à PostGIS réussie")
        
        # Vérifier que PostGIS est activé
        postgis_enabled = await dst.fetchval("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'postgis');")
        if not postgis_enabled:
            logger.warning("⚠ Extension PostGIS non activée, tentative d'activation...")
            try:
                await dst.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
                logger.info("✓ Extension PostGIS activée")
            except Exception as e:
                logger.error(f"Erreur lors de l'activation de PostGIS: {e}")
        
        # Vérifier que la table existe, sinon la créer
        table_exists = await dst.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'anomalies_gis'
            );
        """)
        
        if not table_exists:
            logger.warning("⚠ Table 'anomalies_gis' n'existe pas, création...")
            try:
                await dst.execute("""
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
                    CREATE INDEX IF NOT EXISTS idx_anomalies_gis_geom ON anomalies_gis USING GIST (geom);
                    CREATE INDEX IF NOT EXISTS idx_anomalies_gis_timestamp ON anomalies_gis (timestamp DESC);
                """)
                logger.info("✓ Table anomalies_gis créée avec succès")
            except Exception as e:
                logger.error(f"ERREUR lors de la création de la table: {e}", exc_info=True)
                return
        else:
            logger.info("✓ Table anomalies_gis trouvée dans PostGIS")
            
            # Vérifier et ajouter la contrainte PRIMARY KEY si elle n'existe pas
            has_pk = await dst.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_constraint 
                    WHERE conrelid = 'anomalies_gis'::regclass 
                    AND contype = 'p'
                );
            """)
            
            if not has_pk:
                logger.warning("⚠ Pas de PRIMARY KEY sur 'id', ajout de la contrainte...")
                try:
                    # Vérifier s'il y a des doublons avant d'ajouter la PK
                    duplicates = await dst.fetchval("""
                        SELECT COUNT(*) FROM (
                            SELECT id FROM anomalies_gis GROUP BY id HAVING COUNT(*) > 1
                        ) t;
                    """)
                    
                    if duplicates and duplicates > 0:
                        logger.warning(f"⚠ {duplicates} doublons trouvés, nettoyage...")
                        await dst.execute("""
                            DELETE FROM anomalies_gis a
                            USING anomalies_gis b
                            WHERE a.id = b.id AND a.ctid < b.ctid;
                        """)
                        logger.info("✓ Doublons supprimés")
                    
                    await dst.execute("ALTER TABLE anomalies_gis ADD PRIMARY KEY (id);")
                    logger.info("✓ PRIMARY KEY ajoutée sur 'id'")
                except Exception as e:
                    logger.error(f"ERREUR lors de l'ajout de la PRIMARY KEY: {e}", exc_info=True)
                    logger.warning("⚠ Continuons sans PRIMARY KEY (ON CONFLICT ne fonctionnera pas)")
            else:
                logger.info("✓ PRIMARY KEY sur 'id' vérifiée")
        
        # Statistiques dans TimescaleDB
        total_in_tsdb = await src.fetchval("SELECT COUNT(*) FROM anomalies;")
        with_coords = await src.fetchval("""
            SELECT COUNT(*) FROM anomalies 
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL;
        """)
        recent_with_coords = await src.fetchval("""
            SELECT COUNT(*) FROM anomalies 
            WHERE latitude IS NOT NULL 
              AND longitude IS NOT NULL
              AND timestamp > NOW() - INTERVAL '7 days';
        """)
        
        logger.info(f"📊 Statistiques TimescaleDB:")
        logger.info(f"   - Total anomalies: {total_in_tsdb}")
        logger.info(f"   - Avec coordonnées: {with_coords}")
        logger.info(f"   - Récentes (7 jours) avec coordonnées: {recent_with_coords}")
        
        # Statistiques dans PostGIS
        total_in_postgis = await dst.fetchval("SELECT COUNT(*) FROM anomalies_gis;")
        logger.info(f"📊 Statistiques PostGIS:")
        logger.info(f"   - Total anomalies: {total_in_postgis}")
        
        # Lire les anomalies non encore synchronisées (avec LIMIT pour éviter de charger trop de données)
        # On synchronise par batches pour gérer de grandes quantités
        BATCH_SIZE = 10000  # Traiter 10000 anomalies à la fois
        MAX_ANOMALIES = 100000  # Maximum total à synchroniser par exécution
        
        logger.info("🔍 Lecture des anomalies depuis TimescaleDB...")
        logger.info(f"   Configuration: batch_size={BATCH_SIZE}, max_total={MAX_ANOMALIES}")
        
        # Compter les anomalies récentes (sans vérifier si elles existent déjà - ON CONFLICT gère ça)
        total_recent = await src.fetchval("""
            SELECT COUNT(*) 
            FROM anomalies
            WHERE latitude IS NOT NULL 
              AND longitude IS NOT NULL
              AND timestamp > NOW() - INTERVAL '7 days'
        """)
        
        logger.info(f"   Anomalies récentes (7 jours) avec coordonnées: {total_recent}")
        
        if total_recent == 0:
            logger.info("✅ Aucune anomalie récente à synchroniser.")
            return
        
        # Limiter le nombre total pour cette exécution
        limit = min(total_recent, MAX_ANOMALIES)
        logger.info(f"   Synchronisation de {limit} anomalies maximum cette fois-ci...")
        logger.info(f"   (ON CONFLICT DO NOTHING évitera les doublons)")
        
        # Lire par batches - éviter ORDER BY qui est très lent sur 9M+ lignes
        # Utiliser une approche simple : lire sans tri, on synchronisera tout progressivement
        all_rows = []
        batch_num = 0
        last_id = None  # Utiliser l'ID pour pagination (plus rapide que timestamp)
        
        logger.info(f"   ⚠ Note: Lecture sans ORDER BY pour performance (9M+ lignes)")
        logger.info(f"   Les anomalies seront synchronisées dans l'ordre de la base")
        
        while len(all_rows) < limit:
            batch_num += 1
            batch_limit = min(BATCH_SIZE, limit - len(all_rows))
            
            logger.info(f"   Lecture du batch {batch_num} (déjà {len(all_rows)}/{limit} lues)...")
            
            try:
                # Utiliser WHERE id > last_id pour pagination efficace (pas besoin de ORDER BY)
                if last_id:
                    batch_rows = await src.fetch("""
                        SELECT id, type, timestamp, sensor_id, parameter, value, message, latitude, longitude
                        FROM anomalies
                        WHERE latitude IS NOT NULL 
                          AND longitude IS NOT NULL
                          AND timestamp > NOW() - INTERVAL '7 days'
                          AND id > $1
                        LIMIT $2
                    """, last_id, batch_limit)
                else:
                    # Premier batch : prendre les premières disponibles
                    batch_rows = await src.fetch("""
                        SELECT id, type, timestamp, sensor_id, parameter, value, message, latitude, longitude
                        FROM anomalies
                        WHERE latitude IS NOT NULL 
                          AND longitude IS NOT NULL
                          AND timestamp > NOW() - INTERVAL '7 days'
                        LIMIT $1
                    """, batch_limit)
                
                if not batch_rows:
                    logger.info(f"   ✓ Plus d'anomalies à lire")
                    break
                
                all_rows.extend(batch_rows)
                # Mettre à jour le dernier ID pour la pagination
                last_id = batch_rows[-1]['id']
                logger.info(f"   ✓ {len(batch_rows)} anomalies lues dans ce batch (total: {len(all_rows)}/{limit})")
                
                # Si on a moins que le batch size, on a fini
                if len(batch_rows) < BATCH_SIZE:
                    logger.info(f"   ✓ Toutes les anomalies disponibles ont été lues")
                    break
                
                # Si on a atteint la limite, arrêter
                if len(all_rows) >= limit:
                    break
                    
            except Exception as e:
                logger.error(f"   ❌ Erreur lors de la lecture du batch {batch_num}: {e}")
                if len(all_rows) > 0:
                    logger.info(f"   Continuons avec {len(all_rows)} anomalies déjà lues...")
                    break
                else:
                    raise

        if not all_rows:
            logger.warning("⚠ Aucune anomalie à synchroniser.")
            return

        logger.info(f"✅ {len(all_rows)} anomalies chargées et prêtes à être synchronisées.")

        # Insérer dans PostGIS avec géométrie (traiter par batches pour meilleure performance)
        inserted = 0
        skipped_duplicates = 0  # Déjà existantes
        skipped_invalid = 0     # Coordonnées invalides
        errors = 0
        
        # Traiter par batches pour éviter de saturer la mémoire
        total_batches = (len(all_rows) + BATCH_SIZE - 1) // BATCH_SIZE
        
        for batch_num in range(total_batches):
            batch_start = batch_num * BATCH_SIZE
            batch_end = min(batch_start + BATCH_SIZE, len(all_rows))
            batch = all_rows[batch_start:batch_end]
            
            logger.info(f"   Traitement du batch {batch_num + 1}/{total_batches} ({len(batch)} anomalies)...")
            
            # Filtrer et valider les données avant insertion
            valid_rows = []
            for r in batch:
                # Vérifier que les coordonnées sont valides
                if r['latitude'] is None or r['longitude'] is None:
                    skipped_invalid += 1
                    continue
                
                # Vérifier que les coordonnées sont dans des plages valides
                if not (-90 <= r['latitude'] <= 90) or not (-180 <= r['longitude'] <= 180):
                    skipped_invalid += 1
                    continue
                
                valid_rows.append(r)
            
            if not valid_rows:
                logger.info(f"     Aucune anomalie valide dans ce batch")
                continue
            
            # Insérer une par une avec gestion d'erreur individuelle
            # (évite que les erreurs n'abortent toute la transaction)
            for r in valid_rows:
                try:
                    result = await dst.execute("""
                        INSERT INTO anomalies_gis (id, type, timestamp, sensor_id, parameter, value, message, geom)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, ST_SetSRID(ST_MakePoint($8, $9), 4326))
                        ON CONFLICT (id) DO NOTHING
                    """, r['id'], r['type'], r['timestamp'], r['sensor_id'], r['parameter'],
                       r['value'], r['message'], r['longitude'], r['latitude'])
                    
                    # Vérifier si une ligne a été insérée
                    if result == "INSERT 0 1":
                        inserted += 1
                        if inserted % 1000 == 0:  # Log tous les 1000 insertions
                            logger.info(f"     {inserted} anomalies insérées...")
                    else:
                        skipped_duplicates += 1  # Déjà existant (ON CONFLICT DO NOTHING)
                        
                except Exception as e:
                    errors += 1
                    if errors <= 10:  # Afficher les 10 premières erreurs
                        logger.error(f"❌ Erreur insertion pour id={r['id']}: {e}")
            
            # Log après chaque batch
            logger.info(f"     Batch {batch_num + 1}/{total_batches} terminé: {inserted} insérées, {skipped_duplicates} doublons, {skipped_invalid} invalides, {errors} erreurs")

        logger.info("=" * 60)
        logger.info(f"✅ SYNCHRONISATION TERMINÉE")
        logger.info(f"   - {inserted} anomalies ajoutées")
        logger.info(f"   - {skipped_duplicates} déjà existantes (doublons ignorés)")
        logger.info(f"   - {skipped_invalid} avec coordonnées invalides (filtrées)")
        logger.info(f"   - {errors} erreurs")
        logger.info("=" * 60)
        
        # Vérification finale dans PostGIS
        final_count = await dst.fetchval("SELECT COUNT(*) FROM anomalies_gis;")
        logger.info(f"📊 Total final dans PostGIS: {final_count} anomalies")

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ ERREUR CRITIQUE lors de la synchronisation: {e}", exc_info=True)
        logger.error("=" * 60)
        raise
    finally:
        if src:
            await src.close()
            logger.debug("Connexion TimescaleDB fermée")
        if dst:
            await dst.close()
            logger.debug("Connexion PostGIS fermée")


async def main_loop():
    """Boucle principale avec gestion correcte de l'event loop."""
    # Exécuter immédiatement au démarrage
    logger.info("🚀 Démarrage de l'ETL de synchronisation...")
    try:
        await sync_anomalies()
    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation initiale : {e}", exc_info=True)
    
    # Puis exécuter toutes les 5 minutes
    while True:
        logger.info("⏰ Attente de 5 minutes avant la prochaine synchronisation...")
        await asyncio.sleep(300)  # 300 secondes = 5 minutes
        
        try:
            await sync_anomalies()
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation : {e}", exc_info=True)


if __name__ == "__main__":
    # Utiliser asyncio.run() une seule fois pour la boucle principale
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        logger.info("Arrêt demandé par l'utilisateur.")
    except Exception as e:
        logger.error(f"Erreur fatale : {e}", exc_info=True)
