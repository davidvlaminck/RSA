from __future__ import annotations

import os
import json
from pathlib import Path

from datasources.neo4j import Neo4JDatasource
from datasources.postgis import PostGISDatasource
from outputs.excel import ExcelOutput
from outputs.google_sheets import GoogleSheetsOutput


def try_init_postgis_from_settings():
    # Try to initialize SinglePostGISConnector from RSA_SETTINGS or default location
    try:
        from lib.connectors.PostGISConnector import SinglePostGISConnector
    except Exception:
        return False

    try:
        # if already initialized, nothing to do
        SinglePostGISConnector.get_connector()
        return True
    except RuntimeError:
        pass

    settings_path = os.environ.get('RSA_SETTINGS') or str(Path.home() / 'Documenten' / 'AWV' / 'resources' / 'settings_RSA.json')
    try:
        if Path(settings_path).exists():
            with open(settings_path, 'r', encoding='utf-8') as fh:
                settings = json.load(fh)
            postgis_conf = settings.get('databases', {}).get('PostGIS') or settings.get('databases', {}).get('postgis')
            if postgis_conf:
                SinglePostGISConnector.init(host=postgis_conf.get('host'), port=str(postgis_conf.get('port')),
                                            user=postgis_conf.get('user'), password=postgis_conf.get('password'),
                                            database=postgis_conf.get('database'))
                return True
    except Exception:
        return False
    return False


def make_datasource(name: str):
    if name == 'Neo4J':
        return Neo4JDatasource()
    if name == 'PostGIS':
        # Ensure the connector is initialized (try from settings if needed) before returning datasource
        try:
            return PostGISDatasource()
        except RuntimeError:
            if try_init_postgis_from_settings():
                return PostGISDatasource()
            raise
    if name == 'ArangoDB':
        from datasources.arango import SingleArangoConnector, ArangoDatasource
        db = SingleArangoConnector.get_db()
        return ArangoDatasource.from_existing_connection(db)
    raise ValueError(f"Unsupported datasource: {name}")


def make_output(name: str, *, settings: dict | None = None):
    settings = settings or {}
    if name == 'GoogleSheets':
        return GoogleSheetsOutput()
    if name == 'Excel':
        # prefer a singleton wrapper if initialized (parity with SingleSheetsWrapper)
        try:
            from outputs.excel_wrapper import SingleExcelWriter
            return SingleExcelWriter.get_wrapper()
        except Exception:
            out_dir = settings.get('excel', {}).get('output_dir', './out')
            return ExcelOutput(output_dir=out_dir)
    raise ValueError(f"Unsupported output: {name}")
