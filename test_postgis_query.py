#!/usr/bin/env python3
"""Test script voor PostGIS query uitvoering.

Gebruik:
    python test_postgis_query.py

Test de PostGIS verbinding en voert een enkele query uit om te controleren
of de database-level timeout en de verbinding correct werken.
"""
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Project root toevoegen aan path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Logging instellen met console output
BRUSSELS = timezone(timedelta(hours=2))
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,
)
logger = logging.getLogger(__name__)

SETTINGS_PATH = "/opt/data-platform/config/settings_RSA.json"


def load_settings():
    logger.info("Laden settings uit %s", SETTINGS_PATH)
    with open(SETTINGS_PATH, "r") as f:
        settings = json.load(f)
    logger.info("Settings geladen.")
    return settings


def test_postgis_connection(settings):
    """Test of de PostGIS verbinding werkt en log de statement_timeout."""
    from lib.connectors.PostGISConnector import SinglePostGISConnector

    postgis_settings = settings.get("databases", {}).get("PostGIS", {})
    if not postgis_settings:
        logger.error("Geen PostGIS settings gevonden in settings.json")
        return False

    logger.info("PostGIS settings: host=%s, port=%s, database=%s, user=%s",
                postgis_settings.get("host"),
                postgis_settings.get("port"),
                postgis_settings.get("database"),
                postgis_settings.get("user"))

    try:
        SinglePostGISConnector.reset()
    except Exception:
        pass

    try:
        from lib.connectors.PostGISConnector import SinglePostGISConnector
        connector = SinglePostGISConnector.init(
            host=postgis_settings["host"],
            port=postgis_settings["port"],
            user=postgis_settings["user"],
            password=postgis_settings["password"],
            database=postgis_settings["database"],
            default_statement_timeout_ms=int(postgis_settings.get("statement_timeout", 60000)),
            default_lock_timeout_ms=int(postgis_settings.get("lock_timeout", 10000)),
        )
        logger.info("PostGIS connector geïnitialiseerd.")
    except Exception as e:
        logger.error("Fout bij initialiseren PostGIS connector: %s", e, exc_info=True)
        return False

    # Test verbinding met een simpele query
    try:
        conn = connector.pool.getconn()
        try:
            if not connector._validate_connection(conn):
                logger.error("Connection validatie gefaald")
                return False

            cur = conn.cursor()
            cur.execute("SELECT current_setting('statement_timeout')")
            timeout_val = cur.fetchone()[0]
            logger.info("Huidige statement_timeout voor deze verbinding: %s", timeout_val)

            cur.execute("SELECT 1")
            result = cur.fetchone()
            logger.info("Basis connectivity test (SELECT 1): %s", result)
            cur.close()
        finally:
            connector.pool.putconn(conn)
        logger.info("PostGIS verbinding test geslaagd.")
        return True
    except Exception as e:
        logger.error("Fout bij PostGIS verbindingstest: %s", e, exc_info=True)
        return False


def run_report0108_query(settings):
    """Voer de query van Report0108 direct uit."""
    from lib.connectors.PostGISConnector import SinglePostGISConnector

    postgis_settings = settings.get("databases", {}).get("PostGIS", {})
    if not postgis_settings:
        logger.error("Geen PostGIS settings gevonden.")
        return False

    try:
        SinglePostGISConnector.reset()
    except Exception:
        pass

    try:
        from lib.connectors.PostGISConnector import SinglePostGISConnector
        connector = SinglePostGISConnector.init(
            host=postgis_settings["host"],
            port=postgis_settings["port"],
            user=postgis_settings["user"],
            password=postgis_settings["password"],
            database=postgis_settings["database"],
            default_statement_timeout_ms=int(postgis_settings.get("statement_timeout", 60000)),
            default_lock_timeout_ms=int(postgis_settings.get("lock_timeout", 10000)),
        )
    except Exception as e:
        logger.error("Fout bij initialiseren PostGIS connector: %s", e, exc_info=True)
        return False

    # Query uit Report0108
    query = """
        with cte_geom as (
        SELECT
            assetuuid
            , wkt_string
            , SUBSTRING("wkt_string" FROM '^(POINT Z|LINESTRING Z|POLYGON Z)') AS wkt_string_prefix
            , st_geomfromtext(wkt_string) as geom
        FROM geometrie
        WHERE 
            wkt_string IS NOT null
        ), cte_geom_multiparts as (
            select
                assetuuid
                , st_geometrytype(geom) as geometry_type
                , geom
            from cte_geom
            where wkt_string ~ '^MULTI.*$' 
            )
        select 
            g.assetuuid
            , g.geometry_type
            , st_numgeometries(geom) as aantal_delen 
            , at.naam
            , at.URI
        from cte_geom_multiparts g
        left JOIN assets a ON g.assetuuid = a.uuid
        LEFT JOIN assettypes at ON a.assettype = at.uuid
        where
            a.actief = 'true'
            and 
            at.URI !~ '^(https://grp.).*' -- Regular expression does not start with 
        order by at.uri;
    """

    logger.info("Start Report0108 query uitvoering...")
    start_time = time.time()
    try:
        result = connector.perform_query(query, autocommit_for_read=True)
        elapsed = time.time() - start_time
        logger.info("Query succesvol uitgevoerd in %.2f seconden.", elapsed)
        logger.info("Resultaat: %d rijen", len(result) if result else 0)
        if result:
            logger.info("Eerste 5 rijen: %s", result[:5])
        return True
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error("Query gefaald na %.2f seconden: %s", elapsed, e, exc_info=True)
        return False


def main():
    logger.info("=" * 60)
    logger.info("PostGIS query test gestart om %s", datetime.now(tz=BRUSSELS).isoformat())
    logger.info("=" * 60)

    settings = load_settings()

    logger.info("-" * 60)
    logger.info("Stap 1: PostGIS verbinding testen")
    logger.info("-" * 60)
    conn_ok = test_postgis_connection(settings)

    if not conn_ok:
        logger.error("PostGIS verbinding test gefaald. Stoppen.")
        sys.exit(1)

    logger.info("-" * 60)
    logger.info("Stap 2: Report0108 query uitvoeren")
    logger.info("-" * 60)
    query_ok = run_report0108_query(settings)

    logger.info("=" * 60)
    if query_ok:
        logger.info("RESULTAAT: Query is succesvol uitgevoerd.")
    else:
        logger.error("RESULTAAT: Query is gefaald.")
    logger.info("=" * 60)

    sys.exit(0 if query_ok else 1)


if __name__ == "__main__":
    main()
