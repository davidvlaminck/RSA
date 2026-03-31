from __future__ import annotations

import json
import os
from pathlib import Path

from datasources.neo4j import Neo4JDatasource
from datasources.postgis import PostGISDatasource


def try_init_postgis_from_settings() -> bool:
    """Best-effort PostGIS connector init from settings for local/test runs."""
    try:
        from lib.connectors.PostGISConnector import SinglePostGISConnector
    except Exception:
        return False

    try:
        SinglePostGISConnector.get_connector()
        return True
    except RuntimeError:
        pass

    settings_path = os.environ.get("RSA_SETTINGS") or str(
        Path.home() / "Documenten" / "AWV" / "resources" / "settings_RSA.json"
    )
    try:
        if Path(settings_path).exists():
            with open(settings_path, "r", encoding="utf-8") as fh:
                settings = json.load(fh)
            postgis_conf = settings.get("databases", {}).get("PostGIS") or settings.get("databases", {}).get("postgis")
            if postgis_conf:
                SinglePostGISConnector.init(
                    host=postgis_conf.get("host"),
                    port=str(postgis_conf.get("port")),
                    user=postgis_conf.get("user"),
                    password=postgis_conf.get("password"),
                    database=postgis_conf.get("database"),
                )
                return True
    except Exception:
        return False
    return False


def make_datasource(name: str):
    if name == "Neo4J":
        return Neo4JDatasource()
    if name == "PostGIS":
        try:
            return PostGISDatasource()
        except RuntimeError:
            if try_init_postgis_from_settings():
                return PostGISDatasource()
            raise
    if name == "ArangoDB":
        from datasources.arango import ArangoDatasource, SingleArangoConnector

        db = SingleArangoConnector.get_db()
        return ArangoDatasource.from_existing_connection(db)
    raise ValueError(f"Unsupported datasource: {name}")

