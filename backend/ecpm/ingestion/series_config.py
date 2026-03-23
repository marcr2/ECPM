"""Series configuration loader for YAML-based series definitions.

Loads and validates the series_config.yaml file that drives all data
ingestion. The config is the single source of truth for which FRED
series and BEA tables to ingest.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog
import yaml

logger = structlog.get_logger()

# Default config path relative to the backend directory
DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / "series_config.yaml"


def load_series_config(
    config_path: str | Path | None = None,
) -> dict[str, Any]:
    """Load and validate the series configuration from YAML.

    Args:
        config_path: Path to series_config.yaml. Defaults to
            backend/series_config.yaml.

    Returns:
        Validated configuration dict with 'fred' and 'bea' keys.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        ValueError: If config is missing required sections or has
            invalid structure.
    """
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH

    if not path.exists():
        raise FileNotFoundError(f"Series config not found: {path}")

    with open(path) as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise ValueError("Series config must be a YAML mapping")

    _validate_config(config)

    fred_count = len(config.get("fred", []))
    bea_nipa_count = len(config.get("bea", {}).get("nipa", []))
    bea_fa_count = len(config.get("bea", {}).get("fixed_assets", []))

    logger.info(
        "series_config_loaded",
        path=str(path),
        fred_series=fred_count,
        bea_nipa_tables=bea_nipa_count,
        bea_fixed_assets_tables=bea_fa_count,
    )

    return config


def _validate_config(config: dict[str, Any]) -> None:
    """Validate the structure of the series configuration.

    Checks that required sections exist and entries have the minimum
    required fields.

    Args:
        config: Parsed YAML config dict.

    Raises:
        ValueError: If validation fails.
    """
    # FRED section validation
    fred_series = config.get("fred", [])
    if not isinstance(fred_series, list):
        raise ValueError("'fred' section must be a list of series entries")

    for i, entry in enumerate(fred_series):
        if not isinstance(entry, dict):
            raise ValueError(f"FRED entry {i} must be a mapping")
        if "id" not in entry:
            raise ValueError(f"FRED entry {i} missing required 'id' field")
        if "name" not in entry:
            raise ValueError(f"FRED entry {i} missing required 'name' field")

    # BEA section validation
    bea = config.get("bea", {})
    if not isinstance(bea, dict):
        raise ValueError("'bea' section must be a mapping")

    for section in ("nipa", "fixed_assets"):
        tables = bea.get(section, [])
        if not isinstance(tables, list):
            raise ValueError(f"'bea.{section}' must be a list")
        for i, entry in enumerate(tables):
            if not isinstance(entry, dict):
                raise ValueError(f"BEA {section} entry {i} must be a mapping")
            if "table" not in entry:
                raise ValueError(
                    f"BEA {section} entry {i} missing required 'table' field"
                )
