# ECPM Indicator Calculation Guide

## Data Sources & Frequencies

### Series Used (Shaikh-Tonak Methodology)

| Variable | Series ID | Name | Frequency | Units (raw) |
|----------|-----------|------|-----------|-------------|
| **NI** | BEA:T11200:L1 | National Income (total) | Quarterly | Millions USD |
| **V** | A576RC1 | Compensation of Employees | Monthly | Billions USD |
| **C** | K1PTOTL1ES000 | Net Fixed Assets (Private) | Annual | Millions USD |

**Key Issue**: Mixed frequencies!
- Fixed Assets (C): **Annual** (end-of-year, Dec 31)
- National Income (NI): **Quarterly** (every 3 months)
- Compensation (V): **Monthly** (every month)

---

## How Calculations Work

### Step 1: Data Fetching
All raw data is stored in the database with original units and frequencies.

```python
# Example raw data (latest available):
BEA:T11200:L1 (NI):
  - 2024-Q3: 25,702,850 millions
  - 2024-Q2: 25,500,000 millions
  - 2024-Q1: 25,300,000 millions

A576RC1 (Compensation):
  - 2024-12: 14,500 billions
  - 2024-11: 14,450 billions
  - 2024-10: 14,400 billions

K1PTOTL1ES000 (Fixed Assets):
  - 2024: 70,276,521 millions  # ← Only one value per year!
  - 2023: 68,500,000 millions
  - 2022: 65,000,000 millions
```

### Step 2: Data Alignment
When computing indicators, pandas aligns series by **date index**:

```python
# The series are merged on their date indices
# Result: Only dates where ALL required series have data are used

# For Rate of Profit (needs NI, V, C):
# Since C is annual (end-of-year), we can only compute annual values!

Available computation dates:
- 2024-01-01: NI (Q1), V (monthly avg), C (2024 annual)
- 2023-01-01: NI (Q1), V (monthly avg), C (2023 annual)
- 2022-01-01: ...
```

**Result**: Even though NI and V are high-frequency, **indicators are computed annually** because C is annual!

### Step 3: Unit Normalization
Code converts everything to **billions of dollars**:

```python
# In shaikh_tonak.py:
def _surplus_value(self, data):
    ni = data["national_income"] / 1000.0  # millions → billions
    comp = data["compensation"]  # already billions
    return ni - comp

def _constant_capital(self, data):
    return data["net_fixed_assets_current"] / 1000.0  # millions → billions
```

### Step 4: Indicator Computation
Using the normalized data (all in billions):

```python
# Example for 2024:
NI = 25,702.85 billions  # Total national income
V  = 14,500 billions     # Compensation
C  = 70,276.521 billions # Fixed assets

# Calculate surplus value:
S = NI - V
S = 25,702.85 - 14,500
S = 11,202.85 billions

# Rate of Profit:
r = S / (C + V)
r = 11,202.85 / (70,276.521 + 14,500)
r = 11,202.85 / 84,776.521
r = 0.1321 or 13.21%

# Organic Composition of Capital:
OCC = C / V
OCC = 70,276.521 / 14,500
OCC = 4.85

# Rate of Surplus Value:
s/v = S / V
s/v = 11,202.85 / 14,500
s/v = 0.7726 or 77.26%

# Mass of Profit:
M = S
M = 11,202.85 billions
```

---

## What Time Period Are The Numbers For?

### Current Behavior (Important!)

The **"latest_value"** you see is for the **most recent date where all required data exists**.

For example:
```
Rate of Profit latest_value: 0.1321
Latest date: 2024-01-01
```

This means:
- ✓ Using 2024 Fixed Assets data (annual, reported end-of-year)
- ✓ Using Q1 2024 National Income 
- ✓ Using 2024 Compensation data

**HOWEVER**: There's likely a **frequency mismatch issue** in the current code!

### The Problem: Frequency Mismatch

Since Fixed Assets is **annual** (only Dec 31), but NI is **quarterly**:

```python
# What SHOULD happen:
C_2024 = Fixed Assets for end of 2024
NI_2024 = National Income for FULL YEAR 2024 (sum of 4 quarters)
V_2024 = Compensation for FULL YEAR 2024 (sum of 12 months)

# What MIGHT be happening (pandas default):
C_2024 = Fixed Assets for 2024-01-01
NI_2024 = National Income for Q1 2024 only
V_2024 = Compensation for Jan 2024 only

# This causes incorrect calculations!
```

### Correct Annual Calculation

For a proper annual Rate of Profit for year 2024:

1. **C (Constant Capital)**: Use end-of-year 2024 value
2. **NI (National Income)**: Sum all 4 quarters of 2024
3. **V (Compensation)**: Sum all 12 months of 2024

```python
# Proper calculation:
C_2024 = 70,276.521 billions (end of year)

NI_2024 = NI_Q1 + NI_Q2 + NI_Q3 + NI_Q4
        = (quarterly data needs aggregation)

V_2024 = sum of all 12 monthly compensation values

S_2024 = NI_2024 - V_2024
r_2024 = S_2024 / (C_2024 + V_2024)
```

---

## Historical Time Series

When you request the full indicator:
```bash
GET /api/indicators/rate_of_profit
```

You get a time series like:
```json
{
  "data": [
    {"date": "1959-01-01", "value": 0.1523},
    {"date": "1960-01-01", "value": 0.1498},
    {"date": "1961-01-01", "value": 0.1467},
    ...
    {"date": "2024-01-01", "value": 0.1321}
  ]
}
```

Each data point represents **one year**:
- `1959-01-01`: Rate of profit for calendar year 1959
- `1960-01-01`: Rate of profit for calendar year 1960
- etc.

The date `YYYY-01-01` is a **convention** meaning "this year's annual value".

---

## Economic Interpretation

### Rate of Profit (r = S/(C+V))
**What it means**: For every $1 of total capital invested (buildings, machines, wages), how many cents of profit?

**Example**: r = 0.13 (13%)
- If capitalists invest $100 billion total
- They get back $13 billion in profit
- This is the **annual** return on invested capital

**Historical trend**: US rate of profit fell from ~15% (1950s) to ~10-13% (2000s+)

### Organic Composition of Capital (OCC = C/V)
**What it means**: Ratio of capital equipment to wages

**Example**: OCC = 4.85
- For every $1 paid in wages
- There's $4.85 worth of machinery, buildings, etc.
- Higher OCC = more capital-intensive production

**Historical trend**: Rising (capitalism becomes more mechanized over time)

### Rate of Surplus Value (s/v = S/V)
**What it means**: Rate of exploitation - ratio of unpaid to paid labor

**Example**: s/v = 0.77 (77%)
- Workers are paid $14,500 billion in wages
- They produce $11,203 billion in surplus value (profits, rent, interest)
- For every $1 in wages, $0.77 goes to capital

**Interpretation**: 
- If s/v = 1.0: Workers work half the day for themselves, half for capital
- If s/v = 0.77: Workers work ~56% of the day for themselves, 44% for capital

### Mass of Profit (M = S)
**What it means**: Total dollars of surplus value produced

**Example**: M = $11,203 billion
- This is the total profit mass available to all capitalists
- Even if rate falls, mass can rise if economy grows

**Historical trend**: Generally rising (economy grows) even as rate of profit falls

---

## Potential Issues to Fix

### 1. Frequency Aggregation
The current code may not properly aggregate quarterly/monthly data to annual. Should add:

```python
# Resample to annual frequency before computation
ni_annual = ni_quarterly.resample('Y').sum()
v_annual = v_monthly.resample('Y').sum()
c_annual = c_annual  # already annual
```

### 2. Flow vs Stock Timing
- **C (Fixed Assets)**: Stock measured at **end of year**
- **NI, V**: Flows measured **during the year**

Should we use end-of-year-1 capital or average of year-1 and year-2?

### 3. Latest Value Definition
"Latest" should mean "most recent complete year", not "whatever date pandas aligns to"

---

## Verification Checklist

To verify calculations are correct:

1. **Check latest values make economic sense**:
   - ✓ Rate of profit: 8-15%
   - ✓ OCC: 3-7
   - ✓ Rate of surplus value: 60-100%
   - ✓ Mass of profit: positive, in trillions

2. **Check historical trends**:
   - ✓ Rate of profit: declining or flat
   - ✓ OCC: rising
   - ✓ Mass of profit: rising
   - ✓ Rate of surplus value: varies

3. **Check data frequency alignment**:
   - All points should be annual (Jan 1 of each year)
   - No weird quarterly values leaking through

4. **Check units are consistent**:
   - All values in billions USD
   - No million/billion mismatches
