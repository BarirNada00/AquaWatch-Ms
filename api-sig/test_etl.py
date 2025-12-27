#!/usr/bin/env python3
# Script de test pour diagnostiquer les problèmes de synchronisation
import asyncio
import asyncpg
import os
import sys

TIMESCALEDB_DSN = os.getenv(
    "TIMESCALEDB_DSN",
    "postgresql://aquawatch:example@timescaledb:5432/aquawatch"
)
POSTGIS_DSN = os.getenv(
    "POSTGIS_DSN",
    "postgresql://aquawatch:example@postgis:5432/aquawatch_gis"
)

async def test_connections():
    """Test des connexions aux bases de données"""
    print("=" * 60)
    print("TEST DES CONNEXIONS")
    print("=" * 60)
    
    # Test TimescaleDB
    try:
        conn = await asyncpg.connect(TIMESCALEDB_DSN)
        print("✓ Connexion à TimescaleDB réussie")
        
        # Vérifier la table anomalies
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'anomalies'
            );
        """)
        
        if not table_exists:
            print("❌ Table 'anomalies' n'existe pas dans TimescaleDB!")
        else:
            print("✓ Table 'anomalies' existe")
            
            # Statistiques
            total = await conn.fetchval("SELECT COUNT(*) FROM anomalies;")
            with_coords = await conn.fetchval("""
                SELECT COUNT(*) FROM anomalies 
                WHERE latitude IS NOT NULL AND longitude IS NOT NULL;
            """)
            recent = await conn.fetchval("""
                SELECT COUNT(*) FROM anomalies 
                WHERE latitude IS NOT NULL 
                  AND longitude IS NOT NULL
                  AND timestamp > NOW() - INTERVAL '7 days';
            """)
            
            print(f"  - Total: {total}")
            print(f"  - Avec coordonnées: {with_coords}")
            print(f"  - Récentes (7j) avec coordonnées: {recent}")
            
            # Afficher quelques exemples
            if with_coords > 0:
                examples = await conn.fetch("""
                    SELECT id, type, latitude, longitude, timestamp
                    FROM anomalies
                    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
                    LIMIT 3
                """)
                print("\n  Exemples d'anomalies avec coordonnées:")
                for ex in examples:
                    print(f"    - {ex['id']}: {ex['type']} @ ({ex['latitude']}, {ex['longitude']}) - {ex['timestamp']}")
        
        await conn.close()
    except Exception as e:
        print(f"❌ Erreur TimescaleDB: {e}")
        return False
    
    # Test PostGIS
    try:
        conn = await asyncpg.connect(POSTGIS_DSN)
        print("\n✓ Connexion à PostGIS réussie")
        
        # Vérifier PostGIS
        postgis_enabled = await conn.fetchval("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'postgis');")
        if postgis_enabled:
            print("✓ Extension PostGIS activée")
        else:
            print("⚠ Extension PostGIS non activée")
        
        # Vérifier la table
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'anomalies_gis'
            );
        """)
        
        if not table_exists:
            print("⚠ Table 'anomalies_gis' n'existe pas dans PostGIS")
        else:
            print("✓ Table 'anomalies_gis' existe")
            total = await conn.fetchval("SELECT COUNT(*) FROM anomalies_gis;")
            print(f"  - Total: {total}")
        
        await conn.close()
    except Exception as e:
        print(f"❌ Erreur PostGIS: {e}")
        return False
    
    return True

async def test_sync():
    """Test d'une synchronisation manuelle"""
    print("\n" + "=" * 60)
    print("TEST DE SYNCHRONISATION")
    print("=" * 60)
    
    try:
        import etl_anomalies
        await etl_anomalies.sync_anomalies()
        print("\n✅ Test de synchronisation terminé")
    except Exception as e:
        print(f"\n❌ Erreur lors de la synchronisation: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Fonction principale"""
    print("\n🔍 DIAGNOSTIC DE L'ETL\n")
    
    # Test des connexions
    if await test_connections():
        # Test de synchronisation
        await test_sync()
    else:
        print("\n❌ Les connexions ont échoué, impossible de continuer")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("FIN DU DIAGNOSTIC")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
