from __future__ import annotations

"""Compatibility facade for legacy factory imports.

Preferred imports:
- datasources.datasource_factory.make_datasource
- outputs.output_factory.make_output
"""

from datasources.datasource_factory import make_datasource, try_init_postgis_from_settings
from outputs.output_factory import make_output

__all__ = ["make_datasource", "make_output", "try_init_postgis_from_settings"]
