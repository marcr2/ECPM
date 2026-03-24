# ECPM Indicator Audit Report
**Date**: 2026-03-24
**Scope**: Mathematical correctness & NaN/None error analysis

---

## EXECUTIVE SUMMARY

**Critical Issues Found:**
1. ❌ **K1NTOTL1SI000 series has NO DATA** - breaks all Shaikh-Tonak indicators
2. ❌ **Multiple division-by-zero risks** producing NaN without validation
3. ❌ **Pydantic validation errors** from NaN values in cached data
4. ✅ **Mathematical formulas are CORRECT** per Marxist economics theory

---

## PART 1: MATHEMATICAL CORRECTNESS VERIFICATION

### Shaikh-Tonak Methodology ✅ CORRECT

**Source**: `/backend/ecpm/indicators/shaikh_tonak.py`

#### Core Variables:
- **S (Surplus Value)** = National Income - Compensation ✓
  - Formula: `data[NI] - data[COMP]`
  - Theoretically sound: Surplus is the difference between total product and wage bill

- **V (Variable Capital)** = Compensation of Employees ✓
  - Formula: `data[COMP]`
  - Correct: V represents wages paid to workers

- **C (Constant Capital)** = Current-Cost Net Stock of Private Fixed Assets ✓
  - Formula: `data[ASSETS]`
  - Correct: C represents capital stock (machinery, buildings, etc.)
  - Uses replacement-cost valuation (Shaikh/Tonak standard)

#### Computed Indicators:

1. **Rate of Profit**: r = S / (C + V) ✓
   - Line 85: `return s / (c + v)`
   - Theoretically correct per Marx's Capital Vol. 3
   - Measures return on total capital advanced

2. **Organic Composition of Capital (OCC)**: C / V ✓
   - Line 98: `return c / v`
   - Correct: Ratio of constant to variable capital
   - Rising OCC indicates capital intensification

3. **Rate of Surplus Value**: S / V ✓
   - Line 111: `return s / v`
   - Correct: Rate of exploitation formula
   - Measures unpaid labor vs. paid labor

4. **Mass of Profit**: S ✓
   - Line 122: `return self._surplus_value(data)`
   - Correct: Absolute surplus value in billions USD

**Verdict**: ✅ All Shaikh-Tonak formulas match theoretical expectations.

---

### Financial Indicators ✅ CORRECT (with NaN risks)

**Source**: `/backend/ecpm/indicators/financial.py`

1. **Productivity-Wage Gap** (lines 46-49) ✓
   ```python
   output_idx = (output / output.iloc[0]) * 100
   comp_idx = (compensation / compensation.iloc[0]) * 100
   gap = output_idx / comp_idx * 100
   ```
   - Formula correct: Normalizes both to base 100, then compares
   - ⚠️ **NaN Risk**: If `output.iloc[0]` or `compensation.iloc[0]` is 0 or NaN

2. **Credit-GDP Gap** (line 75) ✓
   ```python
   ratio = (credit / gdp) * 100
   ```
   - Formula correct per BIS methodology
   - Uses one-sided HP filter (λ=400,000 for quarterly data)
   - ⚠️ **NaN Risk**: If GDP is 0

3. **Financial-Real Ratio** (line 98) ✓
   ```python
   return data["financial_assets"] / data["real_assets"]
   ```
   - Simple ratio, mathematically correct
   - ⚠️ **NaN Risk**: If real_assets is 0

4. **Debt Service Ratio** (line 117) ✓
   ```python
   return (data["debt_service"] / data["corporate_income"]) * 100
   ```
   - Formula correct: Interest burden as % of income
   - ⚠️ **NaN Risk**: If corporate_income is 0

**Verdict**: ✅ All financial formulas are theoretically sound.

---

## PART 2: CRITICAL DATA ISSUE

### ❌ K1NTOTL1SI000 (Constant Capital) HAS NO DATA

**Evidence from logs:**
```
{"series_id": "K1NTOTL1SI000", "msg": "No observations found in database"}
```

**Impact**: ALL Shaikh-Tonak indicators return NaN because:
- C (constant capital) = empty/NaN series
- Rate of Profit = S / (NaN + V) = NaN
- OCC = NaN / V = NaN
- Mass of profit works (doesn't need C)
- Rate of surplus value works (doesn't need C)

**Series Configuration**:
- ✅ Series IS configured in `series_config.yaml` (line 79-80)
- ❌ Data was NOT fetched successfully from FRED

**Possible Causes**:
1. FRED series ID changed or was discontinued
2. API key lacks access to Fixed Assets table
3. Fetch task failed silently for this series
4. Database constraint prevented insertion

**Verification Needed**:
```bash
# Check if series exists in FRED
curl "https://api.stlouisfed.org/fred/series?series_id=K1NTOTL1SI000&api_key=YOUR_KEY"

# Check database
docker-compose exec timescaledb psql -U ecpm -d ecpm -c \
  "SELECT * FROM series_metadata WHERE series_id='K1NTOTL1SI000';"
```

---

## PART 3: NaN/NONE VALIDATION ERRORS

### Already Fixed ✅
- `/backend/ecpm/api/indicators.py` (lines 293-296, 386-389): NaN filtering in data points
- `/backend/ecpm/indicators/computation.py` (lines 326-329): NaN filtering in sparklines

### Still Vulnerable ⚠️

#### 1. Division-by-Zero in Indicator Computations
All division operations lack pre-checks:

**Shaikh-Tonak** (`shaikh_tonak.py`):
- Line 85: `s / (c + v)` - if C+V = 0
- Line 98: `c / v` - if V = 0
- Line 111: `s / v` - if V = 0

**Financial** (`financial.py`):
- Line 49: `output_idx / comp_idx * 100` - if comp_idx = 0
- Line 75: `credit / gdp * 100` - if GDP = 0
- Line 98: `financial / real` - if real = 0
- Line 117: `debt_service / corporate_income * 100` - if income = 0

**Recommendation**: Add defensive checks:
```python
def safe_divide(num, denom, default=np.nan):
    """Safely divide two series, returning default where denom is 0/NaN."""
    return np.where((denom == 0) | pd.isna(denom), default, num / denom)
```

#### 2. Pydantic Schemas Don't Allow None

**Vulnerable Fields** (all require `float`, no `Optional`):
- `IndicatorDataPoint.value` (`schemas/indicators.py:21`)
- `ConcentrationDataPoint.cr4/cr8/hhi` (`schemas/concentration.py:23-25`)
- `TrendInfo.slope/r_squared` (`schemas/concentration.py:71-72`)
- `CrisisIndex.current_value` (`schemas/modeling.py:91`)
- `ForecastPoint.point/lower_68/upper_68/lower_95/upper_95` (`schemas/modeling.py:46-50`)

**When NaN → null → None → Pydantic validation fails**

**Recommendation**: Either:
1. Make fields `Optional[float] = None`
2. Add Pydantic `@field_validator` to convert NaN to None
3. Filter NaN in ALL API endpoints before serialization (current partial fix)

#### 3. Cache Deserialization Risk

**Location**: `/backend/ecpm/api/indicators.py:123`
```python
return IndicatorOverviewResponse.model_validate_json(cached)
```

**Risk**: Old cached data contains `null` values (from NaN), validation fails.

**Current Mitigation**: Redis was flushed, sparkline filtering added.

**Long-term Fix**: Add cache versioning or validation wrapper:
```python
try:
    return IndicatorOverviewResponse.model_validate_json(cached)
except ValidationError:
    logger.warning("cache.invalid", key=cache_key)
    # Recompute and update cache
```

---

## PART 4: MISSING SERIES VERIFICATION

### Required Series Status

| Series ID | Name | Status | Used By |
|-----------|------|--------|---------|
| A053RC1Q027SBEA | National Income | ✅ HAS DATA (315 obs) | S, r, s/v, M |
| A576RC1 | Compensation | ✅ HAS DATA (805 obs) | V, S, r, s/v, OCC |
| **K1NTOTL1SI000** | **Net Fixed Assets** | **❌ NO DATA** | **C, r, OCC** |
| OPHNFB | Output Per Hour | ✅ HAS DATA | Productivity Gap |
| PRS85006092 | Real Comp/Hour | ✅ HAS DATA | Productivity Gap |
| BOGZ1FL073164003Q | Credit Total | ✅ HAS DATA | Credit Gap, Fin/Real |
| GDP | Nominal GDP | ✅ HAS DATA | Credit Gap |
| BOGZ1FU106130001Q | Debt Service | ❌ NO DATA | Debt Service Ratio |
| A445RC1Q027SBEA | Corporate Profits | ✅ HAS DATA (315 obs) | Debt Service Ratio |

**Critical Missing**:
1. **K1NTOTL1SI000** (Net Fixed Assets) - BLOCKS Rate of Profit & OCC
2. **BOGZ1FA096130001Q** (Debt Service) - BLOCKS Debt Service Ratio

---

## PART 5: RECOMMENDATIONS

### IMMEDIATE (Critical)

1. **Diagnose K1NTOTL1SI000 fetch failure**
   ```bash
   # Check FRED API directly
   curl "https://api.stlouisfed.org/fred/series/observations?series_id=K1NTOTL1SI000&api_key=$FRED_API_KEY"
   
   # Check fetch task logs
   docker-compose logs celery_worker | grep K1NTOTL1SI000
   ```

2. **Add defensive division** in all indicator computations
   ```python
   import numpy as np
   
   def compute_rate_of_profit(self, data):
       s = self._surplus_value(data)
       c = self._constant_capital(data)
       v = self._variable_capital(data)
       denom = c + v
       return np.where((denom == 0) | pd.isna(denom), np.nan, s / denom)
   ```

3. **Clear Redis cache** after fixes (already done)

### SHORT-TERM (Important)

4. **Add cache validation recovery**
   ```python
   def safe_deserialize(cache_key, model_class, redis):
       cached = cache_get(cache_key, redis)
       if cached:
           try:
               return model_class.model_validate_json(cached)
           except ValidationError as e:
               logger.warning("cache.validation_failed", key=cache_key, error=str(e))
               cache_delete(cache_key, redis)  # Invalidate bad cache
       return None
   ```

5. **Make numeric fields Optional where NaN is possible**
   ```python
   class IndicatorDataPoint(BaseModel):
       date: datetime
       value: Optional[float] = None  # Allow None for missing data
   ```

6. **Add data quality metrics** to /health endpoint
   ```python
   {
       "status": "healthy",
       "data_quality": {
           "required_series_present": 8,
           "required_series_missing": 2,
           "missing": ["K1NTOTL1SI000", "BOGZ1FA096130001Q"]
       }
   }
   ```

### LONG-TERM (Best Practice)

7. **Implement data validation layer**
   - Pre-computation data quality checks
   - Fail-fast if required series missing
   - Return 503 Service Unavailable instead of NaN-filled responses

8. **Add indicator computation tests**
   - Unit tests with mock data (including edge cases: zeros, NaN)
   - Integration tests against real FRED data
   - Regression tests for formula changes

9. **Document data requirements**
   - Which indicators need which series
   - Graceful degradation strategy (which indicators can work with partial data)
   - Clear error messages when data missing

---

## PART 6: SAFE OPERATIONS (No Changes Needed)

### ✅ Correctly Handles NaN
- `ingestion/pipeline.py:161,254` - Stores NaN as NULL with gap_flag
- `indicators/financial.py:123` - Replaces NaN with 0.0 in correlations (intentional)

### ✅ No Division Risk
- `compute_mass_of_profit()` - Just returns S (subtraction, no division)
- Data ingestion pipeline - No arithmetic operations

---

## CONCLUSION

**Mathematical Correctness**: ✅ All formulas are theoretically sound and correctly implement Marxist economic theory.

**Data Completeness**: ❌ Critical series K1NTOTL1SI000 missing, breaking 2 of 4 core indicators.

**NaN Handling**: ⚠️ Partial - endpoint filtering works, but root cause (division-by-zero) not addressed.

**Priority Actions**:
1. Fix K1NTOTL1SI000 data fetch (CRITICAL)
2. Add defensive division guards (HIGH)
3. Implement cache validation recovery (MEDIUM)
4. Add data quality monitoring (MEDIUM)
