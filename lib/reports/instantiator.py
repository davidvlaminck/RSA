"""Report instantiation helper shared by report runners.

Provides `create_report_instance(report_name)` which encapsulates the import-and-instantiate
logic for a Reports.<module> that defines a class named after the module (e.g. Report0002).

This centralizes behavior so the single-report runner and loop runner can both reuse it.
"""
import importlib
import importlib.util
import logging


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
            module_spec = importlib.util.find_spec(f"Reports.{report_name}")
            if module_spec is None:
                logging.error("No module spec found for Reports.%s", report_name)
                return None
            module = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(module)
            class_ = getattr(module, report_name, None)
            if class_ is None:
                logging.error("Module Reports.%s does not expose class %s after legacy load", report_name, report_name)
                return None
            return class_()
        except Exception as exc:
            logging.error("Failed to import/instantiate report %s: %s", report_name, exc)
            return None
