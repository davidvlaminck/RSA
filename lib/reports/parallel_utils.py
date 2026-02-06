"""Helper utilities for parallel report execution.

This module provides tools to:
- Detect which database a report uses
- Group reports by database type
- Run reports in parallel respecting database constraints
"""
import logging
from typing import Dict, List
from collections import defaultdict


def detect_report_datasource(report_instance) -> str:
    """Detect which database a report uses.

    Args:
        report_instance: An instantiated and initialized report

    Returns:
        Database name: 'ArangoDB', 'PostGIS', 'Neo4j', or 'Unknown'
    """
    try:
        if hasattr(report_instance, 'report') and report_instance.report is not None:
            if hasattr(report_instance.report, 'datasource'):
                return report_instance.report.datasource
        return 'Unknown'
    except Exception as e:
        logging.warning(f"Could not detect datasource for report: {e}")
        return 'Unknown'


def group_reports_by_datasource(report_names: List[str]) -> Dict[str, List[str]]:
    """Group report names by their datasource.

    This function instantiates and initializes each report to detect its datasource.
    Reports that fail to instantiate are placed in 'Unknown'.

    Args:
        report_names: List of report class names (e.g., ['Report0002', 'Report0035'])

    Returns:
        Dictionary mapping datasource names to lists of report names
        Example: {
            'ArangoDB': ['Report0002', 'Report0030'],
            'PostGIS': ['Report0035', 'Report0040'],
            'Neo4j': ['Report0100'],
            'Unknown': ['Report0999']
        }
    """
    from lib.reports.instantiator import create_report_instance

    groups = defaultdict(list)

    logging.info(f"Grouping {len(report_names)} reports by datasource...")

    for report_name in report_names:
        try:
            # Instantiate and initialize to detect datasource
            report_instance = create_report_instance(report_name)
            if report_instance is None:
                groups['Unknown'].append(report_name)
                continue

            report_instance.init_report()
            datasource = detect_report_datasource(report_instance)
            groups[datasource].append(report_name)

        except Exception as e:
            logging.warning(f"Could not detect datasource for {report_name}: {e}")
            groups['Unknown'].append(report_name)

    # Log summary
    for datasource, reports in groups.items():
        logging.info(f"  {datasource}: {len(reports)} reports")

    return dict(groups)


def create_balanced_batches(groups: Dict[str, List[str]], max_concurrent: int = 3) -> List[List[tuple]]:
    """Create batches of reports that can run in parallel.

    Each batch contains at most one report from each datasource, ensuring no
    database contention. Batches are balanced to keep total execution time minimal.

    Args:
        groups: Dictionary mapping datasource to list of report names
        max_concurrent: Maximum reports per batch (typically 2-3 for 8GB RAM)

    Returns:
        List of batches, where each batch is a list of (datasource, report_name) tuples
        Example: [
            [('ArangoDB', 'Report0002'), ('PostGIS', 'Report0035')],
            [('ArangoDB', 'Report0030'), ('PostGIS', 'Report0040')],
            ...
        ]
    """
    batches = []

    # Create working copies of the groups
    remaining = {ds: list(reports) for ds, reports in groups.items() if reports}

    # Keep creating batches until all reports are assigned
    while any(remaining.values()):
        batch = []

        # Take one report from each datasource that has reports left
        for datasource in sorted(remaining.keys()):
            if remaining[datasource] and len(batch) < max_concurrent:
                report_name = remaining[datasource].pop(0)
                batch.append((datasource, report_name))

        # Remove empty datasource lists
        remaining = {ds: reports for ds, reports in remaining.items() if reports}

        if batch:
            batches.append(batch)

    logging.info(f"Created {len(batches)} balanced batches for parallel execution")
    return batches
