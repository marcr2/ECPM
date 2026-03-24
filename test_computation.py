#!/usr/bin/env python3
"""Test the actual computation logic with sample data."""
import pandas as pd
import numpy as np
import sys
sys.path.insert(0, '/app')

# Test with sample data
print("=" * 60)
print("Testing credit_gdp_gap computation")
print("=" * 60)

# Create sample data matching what we saw
dates = pd.date_range('2020-01-01', periods=10, freq='QE')
credit = pd.Series([2000000, 2050000, 2100000, 2150000, 2200000, 2250000, 2300000, 2350000, 2400000, 2450000], index=dates)
gdp = pd.Series([30000, 30200, 30400, 30600, 30800, 31000, 31200, 31400, 31600, 31800], index=dates)

print(f"Credit series: {credit.head(3).tolist()}")
print(f"GDP series: {gdp.head(3).tolist()}")

# Test the function
from ecpm.indicators.financial import compute_credit_gdp_gap

data = {"credit_total": credit, "nominal_gdp": gdp}
result = compute_credit_gdp_gap(data)

print(f"\nResult length: {len(result)}")
print(f"NaN count: {result.isna().sum()}")
print(f"Non-NaN count: {result.notna().sum()}")
print(f"First 3 values: {result.head(3).tolist()}")
print(f"Last 3 values: {result.tail(3).tolist()}")

print("\n" + "=" * 60)
print("Testing debt_service_ratio computation")
print("=" * 60)

debt_service = pd.Series([150000, 152000, 154000, 156000, 158000, 160000, 162000, 164000, 166000, 168000], index=dates)
corporate_income = pd.Series([3200, 3250, 3300, 3350, 3400, 3450, 3500, 3550, 3600, 3650], index=dates)

print(f"Debt service series: {debt_service.head(3).tolist()}")
print(f"Corporate income series: {corporate_income.head(3).tolist()}")

from ecpm.indicators.financial import compute_debt_service_ratio

data = {"debt_service": debt_service, "corporate_income": corporate_income}
result = compute_debt_service_ratio(data)

print(f"\nResult length: {len(result)}")
print(f"NaN count: {result.isna().sum()}")
print(f"Non-NaN count: {result.notna().sum()}")
print(f"First 3 values: {result.head(3).tolist()}")
print(f"Last 3 values: {result.tail(3).tolist()}")
