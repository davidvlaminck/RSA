#!/usr/bin/env python3
"""Isolatietest: bepaal of de PostGIS pipeline of Report0108 het probleem is."""
import json
import logging
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

from lib.reports.selection_runner import run_selection
from lib.reports.pipeline_runner import run_pipelines_by_datasource

BRUSSELS = timezone(timedelta(hours=2))
log_path = Path("/opt/data-platform/RSA/RSA_OneDrive/postgis_isolation_test.log")
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(log_path), encoding="utf-8"),
    ],
    force=True,
)
logger = logging.getLogger(__name__)
logger.info("Logbestand: %s", log_path)

SETTINGS_PATH = "/opt/data-platform/config/settings_RSA.json"


def log_section(title):
    logger.info("=" * 60)
    logger.info(title)
    logger.info("=" * 60)


def scenario_single():
    log_section("Scenario 1: alleen Report0108 via run_selection")
    start = time.time()
    rc = run_selection(
        settings_path=SETTINGS_PATH,
        report_names=["Report0108"],
        force_parallel=False,
        stream_output=True,
    )
    logger.info("Scenario 1 klaar in %.2f s, rc=%s", time.time() - start, rc)
    return rc


def scenario_small_batch():
    log_section("Scenario 2: kleine batch met Report0108 via parallel pipeline")
    reports = [
        "Report0108",
        "Report0180",
        "Report0189",
        "Report0179",
        "Report0043",
    ]
    logger.info("Reports: %s", reports)
    start = time.time()
    rc, failed = run_pipelines_by_datasource(
        reports,
        json.load(open(SETTINGS_PATH)),
        SETTINGS_PATH,
        stream_output=True,
        batch_size=10,
    )
    logger.info("Scenario 2 klaar in %.2f s, rc=%s, failed=%s", time.time() - start, rc, failed)
    return rc, failed


def scenario_full_postgis():
    log_section("Scenario 3: volledige PostGIS pipeline (103 reports)")
    settings = json.load(open(SETTINGS_PATH))
    postgis_reports = [
        "Report0189", "Report0179", "Report0187", "Report0035", "Report0180",
        "Report0188", "Report0212", "Report0207", "Report0193", "Report0208",
        "Report0204", "Report0203", "Report0143", "Report0121", "Report0191",
        "Report0195", "Report0200", "Report0114", "Report0177", "Report0205",
        "Report0206", "Report0209", "Report0220", "Report0184", "Report0030",
        "Report0219", "Report0198", "Report0201", "Report0194", "Report0105",
        "Report0170", "Report0190", "Report0197", "Report0210", "Report0043",
        "Report0113", "Report0169", "Report0176", "Report0182",
        "Report0108", "Report0141", "Report0084", "Report0162", "Report0174",
        "Report0183", "Report0129", "Report0185", "Report0139", "Report0120",
        "Report0172", "Report0138", "Report0131", "Report0109", "Report0161",
        "Report0186", "Report0130", "Report0167", "Report0199", "Report0137",
        "Report0196", "Report0140", "Report0163", "Report0160", "Report0057",
        "Report0164", "Report0166", "Report0165", "Report0168", "Report0031",
        "Report0192", "Report0159", "Report0107", "Report0044", "Report0181",
        "Report0142", "Report0156", "Report0175", "Report0157", "Report0110",
        "Report0211", "Report0147", "Report0122", "Report0106", "Report0202",
        "Report0062",
        "Report0136", "Report0149", "Report0146",
        "Report0128", "Report0102", "Report0152", "Report0150", "Report0154",
        "Report0047", "Report0048", "Report0151", "Report0123", "Report0153",
        "Report0000", "Report0118",
    ] # removed 0101  Report0039 Report0171
    logger.info("Aantal PostGIS reports: %d", len(postgis_reports))
    start = time.time()
    rc, failed = run_pipelines_by_datasource(
        postgis_reports,
        settings,
        SETTINGS_PATH,
        stream_output=True,
        batch_size=10,
    )
    logger.info("Scenario 3 klaar in %.2f s, rc=%s, failed=%d", time.time() - start, rc, len(failed))
    return rc, failed


def main():
    log_section("PostGIS pipeline isolatietest")
    logger.info("Tijd: %s", datetime.now(tz=BRUSSELS).isoformat())
    logger.info("Settings: %s", SETTINGS_PATH)

    results = {}

    logger.info("-" * 60)
    rc1 = scenario_single()
    results["single"] = rc1

    logger.info("-" * 60)
    rc2, failed2 = scenario_small_batch()
    results["small_batch_rc"] = rc2
    results["small_batch_failed"] = failed2

    logger.info("-" * 60)
    rc3, failed3 = scenario_full_postgis()
    results["full_rc"] = rc3
    results["full_failed_count"] = len(failed3)

    log_section("RESULTATEN")
    logger.info("Scenario 1 (alleen Report0108): rc=%s", results["single"])
    logger.info("Scenario 2 (kleine batch): rc=%s, failed=%s, failed_names=%s", results["small_batch_rc"], results["small_batch_failed"], failed2)
    logger.info("Scenario 3 (volledig PostGIS): rc=%s, failed_count=%s, failed=%s", results["full_rc"], results["full_failed_count"], failed3)

    if results["single"] == 0 and results["small_batch_rc"] == 0 and results["full_rc"] == 0:
        logger.info("Alle scenario's geslaagd. De bulk-failure is waarschijnlijk time-afhankelijk.")
    elif results["single"] == 0 and results["full_rc"] != 0:
        logger.info("Report0108 werkt alleen, maar de volledige pipeline faalt. Het probleem is in de pipeline/worker.")
    else:
        logger.info("Verdere analyse nodig.")

    sys.exit(0 if results["full_rc"] == 0 else 1)


if __name__ == "__main__":
    main()

