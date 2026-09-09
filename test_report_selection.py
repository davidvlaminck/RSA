#!/usr/bin/env python3
"""Test script voor een enkele PostGIS report via run_selection."""
import json
import logging
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

from lib.reports.selection_runner import run_selection

BRUSSELS = timezone(timedelta(hours=2))
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,
)
logger = logging.getLogger(__name__)

DEFAULT_SETTINGS_PATH = "/opt/data-platform/config/settings_RSA.json"


def main():
    report = "Report0108"
    settings_path = DEFAULT_SETTINGS_PATH

    logger.info("=" * 60)
    logger.info("Test PostGIS report via run_selection")
    logger.info("Report: %s", report)
    logger.info("Settings: %s", settings_path)
    logger.info("Tijd: %s", datetime.now(tz=BRUSSELS).isoformat())
    logger.info("=" * 60)

    # Toon database-level timeout
    try:
        with open(settings_path, "r") as f:
            settings = json.load(f)
        postgis = settings.get("databases", {}).get("PostGIS", {})
        db_timeout = postgis.get("statement_timeout", "niet gevonden")
        logger.info("settings databases.PostGIS.statement_timeout = %s", db_timeout)
    except Exception as e:
        logger.warning("Kon settings niet lezen: %s", e)

    logger.info("-" * 60)
    logger.info("Start run_selection voor %s", report)
    logger.info("-" * 60)
    start = time.time()
    rc = run_selection(
        settings_path=settings_path,
        report_names=[report],
        force_parallel=False,
        stream_output=True,
    )
    elapsed = time.time() - start
    logger.info("-" * 60)
    logger.info("run_selection klaar in %.2f s met return code %s", elapsed, rc)
    logger.info("=" * 60)
    sys.exit(rc)


if __name__ == "__main__":
    main()
