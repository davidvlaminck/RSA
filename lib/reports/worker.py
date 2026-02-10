"""Worker script to run a single report in an isolated subprocess.

This worker is invoked by ReportLoopRunner to execute reports in separate processes.
Each process:
- Re-initializes database connections (critical for thread-safety)
- Runs the report with timeout protection
- Returns exit code 0 on success, non-zero on failure

Usage:
    python -m lib.reports.worker --report Report0002 --settings /path/to/settings.json
"""
import argparse
import logging
import sys
from pathlib import Path
from contextvars import ContextVar

# Add project root to path so we can import modules
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Context variable to track current report name for logging
current_report: ContextVar[str] = ContextVar('current_report', default='')


class ReportContextFilter(logging.Filter):
    """Add current report name to all log records."""
    def filter(self, record):
        report_name = current_report.get()
        if report_name:
            record.report_name = report_name
        else:
            record.report_name = 'System'
        return True


def setup_logging():
    """Configure logging for the worker process."""
    handler = logging.StreamHandler()
    handler.addFilter(ReportContextFilter())
    formatter = logging.Formatter(
        '[Worker %(process)d] [%(report_name)s] %(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)


def reinitialize_database_connections(settings):
    """Re-initialize all database singletons in this child process.

    Critical: Forked processes inherit parent connections which are NOT safe to use.
    Each child must create fresh connections.
    """
    try:
        # PostGIS connector
        postgis_settings = settings['databases']['PostGIS']
        from lib.connectors.PostGISConnector import SinglePostGISConnector
        SinglePostGISConnector.init(
            host=postgis_settings['host'],
            port=postgis_settings['port'],
            user=postgis_settings['user'],
            password=postgis_settings['password'],
            database=postgis_settings['database']
        )
        logging.info("✓ Reinitialized PostGIS connection")
    except Exception as e:
        logging.warning(f"Could not reinitialize PostGIS: {e}")

    try:
        # ArangoDB connector
        arango_settings = settings['databases']['ArangoDB']
        from datasources.arango import SingleArangoConnector
        SingleArangoConnector.init(
            host=arango_settings['host'],
            port=arango_settings['port'],
            user=arango_settings['user'],
            password=arango_settings['password'],
            database=arango_settings['database']
        )
        logging.info("✓ Reinitialized ArangoDB connection")
    except Exception as e:
        logging.warning(f"Could not reinitialize ArangoDB: {e}")

    try:
        # Neo4J connector
        neo4j_settings = settings['databases']['Neo4j']
        from lib.connectors.Neo4JConnector import SingleNeo4JConnector
        SingleNeo4JConnector.init(
            uri=neo4j_settings['uri'],
            user=neo4j_settings['user'],
            password=neo4j_settings['password'],
            database=neo4j_settings['database']
        )
        logging.info("✓ Reinitialized Neo4J connection")
    except Exception as e:
        logging.warning(f"Could not reinitialize Neo4J: {e}")

    try:
        # Sheets wrapper (required for GoogleSheetsOutput)
        from outputs.sheets_wrapper import SingleSheetsWrapper
        creds_path = settings.get('google_api', {}).get('credentials_path')
        if creds_path:
            SingleSheetsWrapper.init(service_cred_path=creds_path, readonly_scope=False)
            logging.info("✓ Reinitialized Google Sheets wrapper")
        else:
            logging.warning("Google API credentials_path not set; Sheets wrapper not initialized")
    except Exception as e:
        logging.warning(f"Could not reinitialize Sheets wrapper: {e}")


def run_single_report(report_name: str, settings: dict, skip_db_init: bool = False) -> int:
    """Run a single report and return exit code.

    Args:
        report_name: Name of report class (e.g., "Report0002")
        settings: Full settings dictionary
        skip_db_init: If True, skip DB reinitialization (already done for pipeline)

    Returns:
        0 on success, 1 on failure
    """
    # Set the current report in context for logging
    current_report.set(report_name)

    try:
        logging.info(f"Starting report")

        # Re-initialize database connections only if this is the first report or a single run
        if not skip_db_init:
            reinitialize_database_connections(settings)

        # Import and instantiate the report
        from lib.reports.instantiator import create_report_instance
        report_instance = create_report_instance(report_name)

        if report_instance is None:
            logging.error(f"Failed to instantiate")
            return 1

        # Initialize the report
        report_instance.init_report()
        logging.info(f"Initialized")

        # Create a MailSender for this worker
        from lib.mail.MailSender import MailSender
        mail_sender = MailSender(mail_settings=settings['smtp_options'])

        # Run the report
        report_instance.run_report(sender=mail_sender)
        logging.info(f"✓ Completed successfully")

        return 0

    except Exception as e:
        logging.error(f"✗ Failed: {e}", exc_info=True)
        return 1


def run_reports(report_names: list[str], settings: dict) -> int:
    """Run multiple reports sequentially in the same worker process.

    Reinitializes database connections once at the start of the pipeline,
    then reuses them for all subsequent reports in the pipeline.

    Returns:
        0 if all reports succeed, 1 if any report fails
    """
    # Reinitialize DB connections ONCE at the start of the pipeline
    logging.info(f"Pipeline starting with {len(report_names)} reports")
    reinitialize_database_connections(settings)

    failed = []
    for report_name in report_names:
        exit_code = run_single_report(report_name, settings, skip_db_init=True)
        if exit_code != 0:
            failed.append(report_name)

    if failed:
        logging.error("One or more reports failed in worker: %s", ", ".join(failed))
        return 1
    return 0


def main():
    """Main entry point for the worker."""
    parser = argparse.ArgumentParser(description='Run a single report in isolation')
    parser.add_argument('--report', help='Single report name (e.g., Report0002)')
    parser.add_argument('--reports', nargs='+', help='Multiple report names (e.g., Report0002 Report0004)')
    parser.add_argument('--settings', required=True, help='Path to settings JSON file')

    args = parser.parse_args()

    setup_logging()

    # Load settings
    import json
    with open(args.settings, 'r') as f:
        settings = json.load(f)

    # Run the report(s)
    if args.report:
        report_list = [args.report]
    elif args.reports:
        report_list = args.reports
    else:
        logging.error("You must provide --report or --reports")
        sys.exit(2)

    exit_code = run_reports(report_list, settings)

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
