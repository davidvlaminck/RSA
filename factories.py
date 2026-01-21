from __future__ import annotations

from datasources.neo4j import Neo4JDatasource
from datasources.postgis import PostGISDatasource
from outputs.excel import ExcelOutput
from outputs.google_sheets import GoogleSheetsOutput


def make_datasource(name: str):
    if name == 'Neo4J':
        return Neo4JDatasource()
    if name == 'PostGIS':
        return PostGISDatasource()
    if name == 'ArangoDB':
        from datasources.arango import ArangoDatasource
        return ArangoDatasource()
    raise ValueError(f"Unsupported datasource: {name}")


def make_output(name: str, *, settings: dict | None = None):
    settings = settings or {}
    if name == 'GoogleSheets':
        return GoogleSheetsOutput()
    if name == 'Excel':
        out_dir = settings.get('excel', {}).get('output_dir', './out')
        return ExcelOutput(output_dir=out_dir)
    raise ValueError(f"Unsupported output: {name}")
