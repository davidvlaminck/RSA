import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import requests

logger = logging.getLogger(__name__)


class PipelineStatusReporter:
    """Reports pipeline status to the RSA_Health FastAPI server."""

    def __init__(self, settings: dict, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        cfg = settings.get("pipeline_status", {}) if isinstance(settings, dict) else {}
        self.enabled = cfg.get("enabled", True)
        self.base_url = cfg.get("base_url", base_url).rstrip("/")
        self.timeout = cfg.get("timeout_seconds", 5)

    def update(self, phase: str, status: str, message: str = "") -> None:
        if not self.enabled:
            return
        try:
            requests.post(
                f"{self.base_url}/pipeline/update",
                json={"phase": phase, "status": status, "message": message},
                timeout=self.timeout,
            )
        except Exception as exc:
            logger.warning(f"Pipeline status update failed: {exc}")
