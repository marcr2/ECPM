# Critical Data Issues Found in ECPM

## Issue 1: Wrong National Income Series ❌

**Current (WRONG)**:
- Series ID: `A053RC1Q027SBEA`
- Name: "National income: Corporate profits before tax"
- Latest value: 4,284.913 billions
- **Problem**: This is ONLY corporate profits, not total national income!

**Correct**:
- Series ID: `BEA:T11200:L1`
- Name: "National income" (from NIPA Table 1.12, Line 1)
- Latest value: 25,702.85 billions (millions in raw form)
- **This is the total national income needed for Shaikh-Tonak**

## Issue 2: Units Mismatch ⚠️

Current data has mixed units:
- National Income (BEA): **Millions** of dollars (needs /1000 to convert to billions)
- Compensation (FRED A576RC1): **Billions** of dollars
- Fixed Assets (FRED K1PTOTL1ES000): **Millions** of dollars (needs /1000)

### Example Calculation (with correct data):

Using BEA:T11200:L1 and proper units:
- NI = 25,702,850 millions = 25,702.85 billions
- Compensation = ~14,000 billions (typical)
- S = NI - Comp = 25,702.85 - 14,000 = 11,702.85 billions
- C = 70,276,521 millions = 70,276.521 billions  
- r = S/(C+V) = 11,702.85 / (70,276.521 + 14,000) ≈ 0.139 or **13.9%**

This is economically realistic!

### Current Wrong Calculation:

Using A053RC1Q027SBEA (corporate profits):
- "NI" = 4,284.913 billions (actually just profits)
- Compensation = ~14,000 billions
- S = 4,284.913 - 14,000 = **-9,715 billions** (NEGATIVE!)
- C = 70,276,521 (not converted, treated as billions)
- r = -9,715 / (70,276,521 + 14,000) ≈ **-0.000138** (nonsense!)

## Required Fixes:

### 1. Update shaikh_tonak.py

Change series ID from A053RC1Q027SBEA to BEA:T11200:L1:

```python
# OLD (WRONG):
SERIES_NATIONAL_INCOME = "A053RC1Q027SBEA"

# NEW (CORRECT):
SERIES_NATIONAL_INCOME = "BEA:T11200:L1"
```

### 2. Add Units Conversion

The mapper needs to normalize units to billions:

```python
def _normalize_to_billions(self, series: pd.Series, source_units: str) -> pd.Series:
    """Convert series to billions of dollars."""
    if source_units == "Millions of Dollars":
        return series / 1000.0
    return series

def _constant_capital(self, data: dict[str, pd.Series]) -> pd.Series:
    """C = Current-Cost Net Stock (convert millions to billions)."""
    return data[_KEY_ASSETS] / 1000.0  # K1PTOTL1ES000 is in millions

def _national_income_total(self, data: dict[str, pd.Series]) -> pd.Series:
    """Total National Income (convert millions to billions)."""
    return data[_KEY_NI] / 1000.0  # BEA data is in millions
```

### 3. Update computation.py Key Mappings

```python
_FRED_TO_KEY: dict[str, str] = {
    "BEA:T11200:L1": "national_income",  # Changed from A053RC1Q027SBEA
    "A576RC1": "compensation",  # Already in billions
    "K1PTOTL1ES000": "net_fixed_assets_current",  # In millions, needs conversion
}
```

### 4. Update series_config.yaml (if needed)

Ensure BEA:T11200:L1 is being fetched (it already is based on logs).

## Verification After Fix:

Expected indicator values with correct data:
- **Rate of Profit**: ~0.10-0.15 (10-15%) ✓ Realistic
- **OCC**: ~5.0-6.0 ✓ Realistic (capital is 5-6x annual wages)
- **Rate of Surplus Value**: ~0.8-1.0 (80-100%) ✓ Realistic

Current wrong values:
- Rate of Profit: -0.000114 ❌
- OCC: 5825.94 ❌ (should be ~5.8, not 5825!)
