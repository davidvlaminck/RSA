#!/usr/bin/env python3
"""
Execute Report0101 AQL and normalize JSON output to a CSV table.

This script embeds a null-safe AQL variant of the provided query (prevents errors when bestek list is empty)
and exports results to CSV. Arrays and objects are JSON-stringified.

Usage:
  python scripts/export_0101_normalize.py --settings /path/to/settings.json --out /tmp/report0101.csv
  OR
  python scripts/export_0101_normalize.py --host 127.0.0.1 --port 8529 --user user --password pw --database db --out /tmp/report0101.csv

Options:
  --example   write a small example CSV without connecting to DB (useful for layout/debug)

"""
from __future__ import annotations
import argparse
import csv
import json
import os
import sys
from pathlib import Path

DEFAULT_SETTINGS_PATH = Path(os.environ.get('RSA_SETTINGS') or Path.home() / 'Documenten' / 'AWV' / 'resources' / 'settings_RSA.json')

SAFE_AQL = r'''
/* Report0101 Vplankoppelingen - safe variant */
LET vr1_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "lgc:installatie#ITSApp-RIS" LIMIT 1 RETURN at._key)
LET vr2_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "lgc:installatie#VRLegacy" LIMIT 1 RETURN at._key)

LET candidates = (
  FOR a IN assets
    FILTER a.AIMDBStatus_isActief == true
      AND (a.assettype_key == vr1_key OR a.assettype_key == vr2_key)
    RETURN {
      _key: a._key,
      actief: a.AIMDBStatus_isActief,
      naam: a.AIMNaamObject_naam,
      naampad: a.NaampadObject_naampad,
      naampad_parent: a.naampad_parent,
      toestand: a.toestand,
      loc: a.loc,
      bs: a.bs,
      geometry: a.geometry
    }
)

FOR c IN candidates
  FOR vplan IN vplankoppelingen
    FILTER vplan.asset_key == c._key

    LET adres_json = (c.loc && c.loc.Locatie_puntlocatie && c.loc.Locatie_puntlocatie.DtcPuntlocatie_adres) ? c.loc.Locatie_puntlocatie.DtcPuntlocatie_adres : null
    LET provincie = adres_json && adres_json.DtcAdres_provincie ? adres_json.DtcAdres_provincie : null
    LET gemeente = adres_json && adres_json.DtcAdres_gemeente ? adres_json.DtcAdres_gemeente : null
    LET adres_parts = [
      adres_json && adres_json.DtcAdres_straat ? adres_json.DtcAdres_straat : null,
      adres_json && adres_json.DtcAdres_nummer ? adres_json.DtcAdres_nummer : null,
      adres_json && adres_json.DtcAdres_bus ? adres_json.DtcAdres_bus : null,
      adres_json && adres_json.DtcAdres_postcode ? adres_json.DtcAdres_postcode : null,
      adres_json && adres_json.DtcAdres_gemeente ? adres_json.DtcAdres_gemeente : null
    ]
    LET adres_arr = (FOR p IN adres_parts FILTER p != null RETURN p)
    LET adres = LENGTH(adres_arr) > 0 ? CONCAT_SEPARATOR(" ", adres_arr) : null

    LET asset_bestekken = (
      FOR bk IN (c.bs && c.bs.Bestek_bestekkoppeling ? c.bs.Bestek_bestekkoppeling : [])
        FILTER bk != null AND bk._to != null
        LET b = DOCUMENT(bk._to)
        FILTER b != null
        RETURN {
          dossiernummer: b.eDeltaDossiernummer ? b.eDeltaDossiernummer : null,
          besteknummer: b.eDeltaBesteknummer ? b.eDeltaBesteknummer : null,
          aannemer: b.aannemerNaam ? b.aannemerNaam : null,
          van: bk.DtcBestekkoppeling_actiefVan ? bk.DtcBestekkoppeling_actiefVan : null,
          tot: bk.DtcBestekkoppeling_actiefTot ? bk.DtcBestekkoppeling_actiefTot : null
        }
    )
    LET meest_recent_bestek = (LENGTH(asset_bestekken) > 0 ? asset_bestekken[0] : null)

    LET jarenInDienst =
      IS_NULL(vplan.uitDienstDatum)
        ? DATE_DIFF(LEFT(vplan.inDienstDatum, 10), DATE_NOW(), "years")
        : DATE_DIFF(LEFT(vplan.inDienstDatum, 10), LEFT(vplan.uitDienstDatum, 10), "years")
    LET vplan_nummer_kort = vplan.vplan_nummer ? LEFT(vplan.vplan_nummer, 7) : null
    LET tien_jaar_oud = jarenInDienst >= 10

    /* safe access to geometry coordinates (longitude, latitude) */
    LET coords = (c.geometry && c.geometry.coordinates) ? c.geometry.coordinates : null
    LET longitude = (coords ? coords[0] : null)
    LET latitude = (coords ? coords[1] : null)

    /* dataconflicten translation from SQL CASE */
    LET vplan_has_id = (HAS(vplan, '_key') && vplan._key != null) || (HAS(vplan, 'uuid') && vplan.uuid != null) || (HAS(vplan, 'vplan_uuid') && vplan.vplan_uuid != null)
    LET dataconflicten = (
      ((NOT vplan_has_id) && c.actief == true && c.toestand == 'in-gebruik')
      || ((vplan.uitDienstDatum == null) && vplan_has_id && c.actief == true && (c.toestand != 'in-gebruik' && c.toestand != 'overgedragen'))
      || ((provincie == null || coords == null) && c.actief == true)
    )

    SORT c.actief DESC, c.naampad ASC, vplan.inDienstDatum DESC

    RETURN {
      uuid: c._key,
      installatie: (c.naampad ? regex_matches(c.naampad, '^[^/]{1,10}', false)[0] : null),
      naampad: c.naampad,
      actief: c.actief,
      toestand: c.toestand,
      longitude: longitude,
      latitude: latitude,
      adres_gemeente: gemeente,
      adres_provincie: provincie,
      indienstdatum: vplan.inDienstDatum,
      uitdienstdatum: vplan.uitDienstDatum,
      vplan_nr: vplan.vplan_nummer,
      vplan_nr_kort: vplan_nummer_kort,
      commentaar: (vplan.commentaar ? vplan.commentaar : 'onbeschikbaar'),
      edeltadossiernummer: (meest_recent_bestek != null ? meest_recent_bestek.dossiernummer : null),
      aannemernaam: (meest_recent_bestek != null ? meest_recent_bestek.aannemer : null),
      tien_jaar_oud: tien_jaar_oud,
      dataconflicten: dataconflicten
    }
'''


def format_value(v):
    if v is None:
        return ''
    if isinstance(v, (str, int, float)):
        return str(v)
    if isinstance(v, bool):
        return 'TRUE' if v else 'FALSE'
    # lists or dicts -> JSON string
    try:
        return json.dumps(v, ensure_ascii=False)
    except Exception:
        return str(v)


def write_csv_from_rows(rows_iter, out_path: Path):
    # rows_iter yields dicts
    # determine header from first row
    first = None
    try:
        first = next(rows_iter)
    except StopIteration:
        # no rows
        out_path.write_text('')
        print('No rows; wrote empty file at', out_path)
        return

    if not isinstance(first, dict):
        # serialize single-value rows
        with out_path.open('w', newline='', encoding='utf-8') as fh:
            writer = csv.writer(fh)
            writer.writerow(['value'])
            writer.writerow([format_value(first)])
            for r in rows_iter:
                writer.writerow([format_value(r)])
        print('Wrote CSV to', out_path)
        return

    header = list(first.keys())
    # peek at a small number of additional rows to gather additional keys
    prefix = []
    for _ in range(100):
        try:
            r = next(rows_iter)
        except StopIteration:
            r = None
        if r is None:
            break
        prefix.append(r)
        if isinstance(r, dict):
            for k in r.keys():
                if k not in header:
                    header.append(k)

    def chained():
        for r in prefix:
            yield r
        for r in rows_iter:
            yield r

    rows_all = chained()

    with out_path.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.writer(fh)
        writer.writerow([str(h) for h in header])
        # write first
        writer.writerow([format_value(first.get(k)) for k in header])
        for r in rows_all:
            if not isinstance(r, dict):
                writer.writerow([format_value(r)])
            else:
                writer.writerow([format_value(r.get(k)) for k in header])
    print('Wrote CSV to', out_path)


def main():
    p = argparse.ArgumentParser(description='Export Report0101 to CSV (normalizing JSON to table)')
    p.add_argument('--settings', help='settings JSON path', default=None)
    p.add_argument('--host', help='Arango host')
    p.add_argument('--port', help='Arango port')
    p.add_argument('--user', help='Arango user')
    p.add_argument('--password', help='Arango password')
    p.add_argument('--database', help='Arango database')
    p.add_argument('--out', help='output CSV path', default='/tmp/report0101.csv')
    p.add_argument('--example', action='store_true', help='write example CSV without DB')
    args = p.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if args.example:
        sample = [
            {'uuid': '1', 'installatie': 'A', 'naampad': 'a/b', 'actief': True, 'aant_bestekken': [{'dossiernummer': 'D1'}], 'longitude': 4.3, 'latitude': 51.1},
            {'uuid': '2', 'installatie': 'B', 'naampad': 'c/d', 'actief': False},
        ]
        write_csv_from_rows(iter(sample), out_path)
        return 0

    # resolve conf
    conf = None
    if args.host and args.port and args.user and args.database:
        conf = {'host': args.host, 'port': args.port, 'user': args.user, 'password': args.password or '', 'database': args.database}
    else:
        settings_path = Path(args.settings) if args.settings else DEFAULT_SETTINGS_PATH
        if not settings_path.exists():
            print('Settings file not found:', settings_path, file=sys.stderr)
            return 2
        with settings_path.open('r', encoding='utf-8') as fh:
            s = json.load(fh)
        dbs = s.get('databases', {})
        conf = dbs.get('ArangoDB') or dbs.get('arangodb')
        if not conf:
            print('No ArangoDB config under databases in settings', file=sys.stderr)
            return 3

    # init connector
    try:
        from datasources.arango import SingleArangoConnector
    except Exception as e:
        print('Cannot import Arango connector:', e, file=sys.stderr)
        return 4

    try:
        SingleArangoConnector.init(host=conf.get('host'), port=str(conf.get('port')), user=conf.get('user'), password=conf.get('password'), database=conf.get('database'))
        db = SingleArangoConnector.get_db()
    except Exception as e:
        print('Failed to init Arango connection:', repr(e), file=sys.stderr)
        return 5

    # execute AQL
    try:
        cursor = db.aql.execute(SAFE_AQL)
    except Exception as e:
        print('AQL execution failed:', repr(e), file=sys.stderr)
        return 6

    # stream rows
    # convert cursor to iterator of dicts
    def row_iter():
        for r in cursor:
            yield r

    write_csv_from_rows(row_iter(), out_path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

