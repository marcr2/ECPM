"""SEC EDGAR API client for firm-level revenue data.

Fetches annual revenue from the XBRL CompanyFacts endpoint and company
metadata from the Submissions endpoint.  No API key is required; only a
User-Agent header with a contact email (per SEC fair-access policy).

Rate limit: 10 requests/second.  We enforce 0.12 s between calls to
stay comfortably below that.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import httpx
import structlog
import yaml
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = structlog.get_logger()

# XBRL concept names for "annual revenue", in priority order.
# Post-ASC-606 filers use the second; older filers use the others.
_REVENUE_CONCEPTS: list[tuple[str, str]] = [
    ("us-gaap", "Revenues"),
    ("us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax"),
    ("us-gaap", "RevenueFromContractWithCustomerIncludingAssessedTax"),
    ("us-gaap", "SalesRevenueNet"),
    ("us-gaap", "SalesRevenueGoodsNet"),
    ("us-gaap", "SalesRevenueServicesNet"),
]

# Fiscal period filters — we only want full-year (annual) figures.
_ANNUAL_FORMS = {"10-K", "10-K/A", "20-F", "20-F/A"}

FIRM_REGISTRY_PATH = Path(__file__).parent / "firm_registry.yaml"


def _log_retry(retry_state: RetryCallState) -> None:
    logger.warning(
        "edgar_retry",
        attempt=retry_state.attempt_number,
        url=str(retry_state.args[1]) if len(retry_state.args) > 1 else "?",
    )


class EdgarClient:
    """SEC EDGAR API wrapper with rate limiting and retry.

    Attributes:
        user_agent: User-Agent string required by SEC (e.g.
            ``"ECPM admin@example.com"``).
    """

    BASE_URL = "https://data.sec.gov"

    def __init__(self, user_agent: str) -> None:
        if not user_agent:
            raise ValueError(
                "SEC EDGAR requires a User-Agent header with a contact email. "
                "Set EDGAR_USER_AGENT in your .env (e.g. 'ECPM admin@example.com')."
            )
        self.user_agent = user_agent
        self._rate_limit_delay: float = 0.12  # ~8 req/s, within 10/s limit
        self._last_call_time: float = 0.0
        self._registry: dict[str, Any] | None = None

    # ── internal helpers ──────────────────────────────────────────

    def _throttle(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_call_time
        if elapsed < self._rate_limit_delay:
            time.sleep(self._rate_limit_delay - elapsed)
        self._last_call_time = time.monotonic()

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        before_sleep=_log_retry,
    )
    def _get_json(self, url: str) -> dict[str, Any]:
        """GET a JSON endpoint from data.sec.gov with rate limiting."""
        self._throttle()
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }
        response = httpx.get(url, headers=headers, timeout=20.0)
        if response.status_code == 404:
            return {}
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _pad_cik(cik: int) -> str:
        """Pad CIK to 10 digits with leading zeros."""
        return str(cik).zfill(10)

    # ── firm registry ─────────────────────────────────────────────

    def _load_registry(self) -> dict[str, Any]:
        """Load and cache the curated firm registry YAML."""
        if self._registry is not None:
            return self._registry
        with open(FIRM_REGISTRY_PATH, "r") as f:
            data = yaml.safe_load(f)
        self._registry = data.get("industries", {})
        return self._registry

    def get_registry_naics_codes(self) -> list[str]:
        """Return all NAICS codes present in the curated registry."""
        return list(self._load_registry().keys())

    def get_registry_firms(self, naics_code: str) -> list[dict[str, Any]]:
        """Return the curated firm list for a NAICS sector."""
        registry = self._load_registry()
        entry = registry.get(naics_code, {})
        return entry.get("firms", [])

    def get_registry_industry_name(self, naics_code: str) -> str:
        """Return the human-readable name for a NAICS sector."""
        registry = self._load_registry()
        entry = registry.get(naics_code, {})
        return entry.get("name", naics_code)

    # ── EDGAR endpoints ───────────────────────────────────────────

    def fetch_company_info(self, cik: int) -> dict[str, Any]:
        """Fetch company metadata from the Submissions endpoint.

        Returns dict with keys: name, sic, sic_description, tickers.
        Returns empty dict if CIK not found.
        """
        padded = self._pad_cik(cik)
        url = f"{self.BASE_URL}/submissions/CIK{padded}.json"
        try:
            data = self._get_json(url)
            if not data:
                return {}
            return {
                "cik": cik,
                "name": data.get("name", ""),
                "sic": data.get("sic", ""),
                "sic_description": data.get("sicDescription", ""),
                "tickers": data.get("tickers", []),
                "entity_type": data.get("entityType", ""),
            }
        except Exception:
            logger.warning("edgar_company_info_error", cik=cik, exc_info=True)
            return {}

    def fetch_company_revenue(
        self,
        cik: int,
        fiscal_year: int | None = None,
    ) -> float | None:
        """Fetch annual revenue from the XBRL CompanyFacts endpoint.

        Tries multiple XBRL concept names in priority order and returns
        the most recent 10-K annual revenue figure (in USD).

        Args:
            cik: SEC Central Index Key.
            fiscal_year: If set, return revenue for that specific fiscal
                year.  Otherwise return the most recent available.

        Returns:
            Revenue in USD (raw, not thousands/millions), or None if
            unavailable.
        """
        padded = self._pad_cik(cik)
        url = f"{self.BASE_URL}/api/xbrl/companyfacts/CIK{padded}.json"

        try:
            data = self._get_json(url)
            if not data:
                return None

            facts = data.get("facts", {})

            for taxonomy, concept in _REVENUE_CONCEPTS:
                tax_facts = facts.get(taxonomy, {})
                concept_data = tax_facts.get(concept, {})
                units = concept_data.get("units", {})

                # Revenue is in USD
                usd_entries = units.get("USD", [])
                if not usd_entries:
                    continue

                # Filter to annual 10-K filings only
                annual = [
                    e for e in usd_entries
                    if e.get("form") in _ANNUAL_FORMS
                    and e.get("fp") in ("FY", "CY")
                ]

                if not annual:
                    # Fall back: some filers tag fp differently
                    annual = [
                        e for e in usd_entries
                        if e.get("form") in _ANNUAL_FORMS
                    ]

                if not annual:
                    continue

                if fiscal_year is not None:
                    # Try the exact requested year first
                    year_matches = [
                        e for e in annual
                        if e.get("fy") == fiscal_year
                    ]
                    if year_matches:
                        year_matches.sort(key=lambda e: e.get("filed", ""), reverse=True)
                        return float(year_matches[0]["val"])
                    # If not found, try the previous year (most companies
                    # haven't filed current-year 10-K until Q1 of the next year)
                    year_matches = [
                        e for e in annual
                        if e.get("fy") == fiscal_year - 1
                    ]
                    if year_matches:
                        year_matches.sort(key=lambda e: e.get("filed", ""), reverse=True)
                        return float(year_matches[0]["val"])

                # Take the most recent annual revenue
                annual.sort(key=lambda e: e.get("end", ""), reverse=True)
                return float(annual[0]["val"])

        except Exception:
            logger.warning("edgar_revenue_error", cik=cik, exc_info=True)

        return None

    # ── high-level pipeline methods ───────────────────────────────

    def fetch_industry_firms(
        self,
        naics_code: str,
        fiscal_year: int | None = None,
    ) -> list[dict[str, Any]]:
        """Load firms for a NAICS from the registry and enrich with EDGAR revenue.

        For each firm in the curated list, fetches the latest (or specified)
        annual revenue from CompanyFacts.  Returns a list of dicts suitable
        for CR4/HHI computation and storage in firm_market_share.

        Args:
            naics_code: 3-digit NAICS code.
            fiscal_year: Optional year filter; defaults to latest available.

        Returns:
            List of dicts: name, cik, parent, revenue (USD or None).
        """
        curated_firms = self.get_registry_firms(naics_code)
        if not curated_firms:
            logger.info("edgar_no_registry_firms", naics=naics_code)
            return []

        enriched: list[dict[str, Any]] = []
        for firm in curated_firms:
            cik = firm["cik"]
            revenue = self.fetch_company_revenue(cik, fiscal_year=fiscal_year)

            enriched.append({
                "name": firm["name"],
                "cik": cik,
                "parent": firm.get("parent", firm["name"]),
                "revenue": revenue,
            })

            logger.debug(
                "edgar_firm_revenue",
                firm=firm["name"],
                cik=cik,
                revenue=revenue,
            )

        return enriched

    def compute_industry_concentration(
        self,
        naics_code: str,
        fiscal_year: int | None = None,
    ) -> dict[str, Any] | None:
        """Compute CR4/CR8/HHI for an industry using EDGAR revenue data.

        Aggregates revenue by parent company, computes market shares,
        then derives concentration metrics.

        Returns:
            Dict with cr4, cr8, hhi, num_firms, total_revenue,
            firms (list), or None if insufficient data.
        """
        firms = self.fetch_industry_firms(naics_code, fiscal_year=fiscal_year)
        if not firms:
            return None

        # Filter out firms with no revenue data
        firms_with_revenue = [f for f in firms if f["revenue"] is not None and f["revenue"] > 0]
        if not firms_with_revenue:
            logger.warning("edgar_no_revenue_data", naics=naics_code)
            return None

        # Aggregate by parent company
        parent_revenue: dict[str, float] = {}
        parent_firms: dict[str, list[str]] = {}
        for f in firms_with_revenue:
            parent = f["parent"]
            parent_revenue[parent] = parent_revenue.get(parent, 0.0) + f["revenue"]
            parent_firms.setdefault(parent, []).append(f["name"])

        total_revenue = sum(parent_revenue.values())
        if total_revenue <= 0:
            return None

        # Sort parents by revenue descending
        sorted_parents = sorted(
            parent_revenue.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        # Compute market shares (as percentages)
        shares = [(name, rev / total_revenue * 100) for name, rev in sorted_parents]

        # CR4, CR8
        cr4 = sum(s for _, s in shares[:4])
        cr8 = sum(s for _, s in shares[:8])

        # HHI = sum of squared market shares
        hhi = sum(s ** 2 for _, s in shares)

        # Build firm detail list for storage
        firm_details = []
        for rank, (parent_name, share_pct) in enumerate(shares, 1):
            rev = parent_revenue[parent_name]
            firm_details.append({
                "rank": rank,
                "firm_name": parent_name,
                "parent_company": parent_name,
                "revenue": rev,
                "market_share_pct": share_pct,
            })

        return {
            "cr4": cr4,
            "cr8": cr8,
            "hhi": hhi,
            "num_firms": len(sorted_parents),
            "total_revenue": total_revenue,
            "firms": firm_details,
            "data_source": "edgar",
        }
