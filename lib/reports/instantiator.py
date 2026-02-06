"""Report instantiation helper shared by report runners.

Provides `create_report_instance(report_name)` which encapsulates the import-and-instantiate
logic for a Reports.<module> that defines a class named after the module (e.g. Report0002).

Also provides `discover_and_instantiate_reports(reports_dir)` to scan and instantiate all
reports in a directory, with a default path relative to this module.

This centralizes behavior so the single-report runner and loop runner can both reuse it.
"""
import importlib
import importlib.util
import logging
import pkgutil
from pathlib import Path


# Default Reports directory relative to this module
_DEFAULT_REPORTS_DIR = Path(__file__).parent.parent / "Reports"


def create_report_instance(report_name: str):
    """Import Reports.<report_name> and instantiate the class named `report_name`.

    Returns an instance if successful, otherwise returns None.
    """
    try:
        module = importlib.import_module(f"Reports.{report_name}")
        class_ = getattr(module, report_name, None)
        if class_ is None:
            logging.error("Module Reports.%s does not expose class %s", report_name, report_name)
            return None
        return class_()
    except Exception:
        try:
            # Fallback: load directly from file using relative path
            report_file = _DEFAULT_REPORTS_DIR / f"{report_name}.py"
            if not report_file.exists():
                logging.error("Report file not found: %s", report_file)
                return None
            module_spec = importlib.util.spec_from_file_location(report_name, report_file)
            if module_spec is None or module_spec.loader is None:
                logging.error("Could not create module spec for %s", report_file)
                return None
            module = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(module)
            class_ = getattr(module, report_name, None)
            if class_ is None:
                logging.error("Module %s does not expose class %s", report_file, report_name)
                return None
            return class_()
        except Exception as exc:
            logging.error("Failed to import/instantiate report %s: %s", report_name, exc)
            return None


def discover_and_instantiate_reports(reports_dir: Path = None) -> list:
    """Discover all report modules in the given directory and instantiate them.

    Args:
        reports_dir: Path to the directory containing report modules.
                     Defaults to Reports/ relative to this module.

    Returns:
        List of instantiated report objects (excludes failed instantiations).
    """
    if reports_dir is None:
        reports_dir = _DEFAULT_REPORTS_DIR

    reports = []
    if not reports_dir.exists():
        logging.error("Reports directory not found: %s", reports_dir)
        return reports

    for importer, module_name, is_pkg in pkgutil.iter_modules([str(reports_dir)]):
        if not is_pkg:  # Skip packages, only load .py modules
            instance = create_report_instance(module_name)
            if instance is not None:
                reports.append(instance)

    return reports

