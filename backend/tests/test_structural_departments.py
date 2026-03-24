"""Tests for Department I/II classification and proportionality conditions.

Tests NAICS-to-Department mapping, aggregation by department, and Marx's
reproduction schema proportionality condition checks.
"""

from __future__ import annotations

import numpy as np
import pytest

# Skip if structural module not implemented yet
departments = pytest.importorskip("ecpm.structural.departments")


class TestDeptICodes:
    """Tests for DEPT_I_CODES constant."""

    def test_dept_i_codes_is_set(self):
        """DEPT_I_CODES should be a set for O(1) lookup."""
        assert isinstance(departments.DEPT_I_CODES, (set, frozenset))

    def test_dept_i_codes_contains_expected(self):
        """DEPT_I_CODES should contain key means of production sectors."""
        # Mining, utilities, construction should be in Dept I
        expected_codes = ["211", "22", "23", "333", "331"]
        for code in expected_codes:
            assert code in departments.DEPT_I_CODES, f"{code} should be in DEPT_I_CODES"

    def test_dept_i_codes_excludes_consumer_sectors(self):
        """DEPT_I_CODES should not contain consumer-facing sectors."""
        # Retail, food services, healthcare typically Dept II
        consumer_codes = ["44", "45", "72", "62"]
        for code in consumer_codes:
            assert (
                code not in departments.DEPT_I_CODES
            ), f"{code} should not be in DEPT_I_CODES"


class TestClassifyDepartments:
    """Tests for classify_departments function."""

    def test_classify_departments_returns_dict(self, synthetic_dept_classification):
        """classify_departments should return a dict mapping codes to departments."""
        naics_codes = list(synthetic_dept_classification.keys())
        result = departments.classify_departments(naics_codes)

        assert isinstance(result, dict)
        assert len(result) == len(naics_codes)

    def test_classify_departments_values(self, synthetic_dept_classification):
        """Classification values should be 'Dept_I' or 'Dept_II'."""
        naics_codes = list(synthetic_dept_classification.keys())
        result = departments.classify_departments(naics_codes)

        for code, dept in result.items():
            assert dept in ("Dept_I", "Dept_II"), f"Invalid department: {dept}"

    def test_classify_departments_matches_expected(self, synthetic_dept_classification):
        """Classification should match expected fixture values."""
        naics_codes = list(synthetic_dept_classification.keys())
        result = departments.classify_departments(naics_codes)

        for code, expected_dept in synthetic_dept_classification.items():
            assert result[code] == expected_dept, f"Mismatch for {code}"


class TestAggregateByDepartment:
    """Tests for aggregate_by_department function."""

    def test_aggregate_by_department_returns_2x2(
        self, synthetic_use_matrix_3x3, synthetic_dept_classification
    ):
        """aggregate_by_department should return 2x2 matrix."""
        sector_codes = list(synthetic_dept_classification.keys())[:3]
        classification = {code: "Dept_I" if i < 2 else "Dept_II" for i, code in enumerate(sector_codes)}

        result = departments.aggregate_by_department(
            use_matrix=synthetic_use_matrix_3x3,
            classification=classification,
            sector_codes=sector_codes,
        )

        assert result.shape == (2, 2)

    def test_aggregate_by_department_sum_preserved(
        self, synthetic_use_matrix_3x3, synthetic_dept_classification
    ):
        """Total flows should be preserved after aggregation."""
        sector_codes = list(synthetic_dept_classification.keys())[:3]
        classification = {code: "Dept_I" if i < 2 else "Dept_II" for i, code in enumerate(sector_codes)}

        result = departments.aggregate_by_department(
            use_matrix=synthetic_use_matrix_3x3,
            classification=classification,
            sector_codes=sector_codes,
        )

        original_sum = synthetic_use_matrix_3x3.sum()
        aggregated_sum = result.sum()
        assert np.isclose(original_sum, aggregated_sum)


class TestCheckProportionality:
    """Tests for check_proportionality function."""

    def test_proportionality_simple_holds(self):
        """Simple reproduction: I(v+s) = II(c) should be detected."""
        # Simple reproduction: I(v+s) = II(c)
        # Dept I: c=50, v=25, s=25  -> v+s = 50
        # Dept II: c=50, v=30, s=20 -> c = 50
        result = departments.check_proportionality(
            dept_i_c=50.0,
            dept_i_v=25.0,
            dept_i_s=25.0,
            dept_ii_c=50.0,
            dept_ii_v=30.0,
            dept_ii_s=20.0,
        )

        assert isinstance(result, dict)
        assert result["simple_reproduction_holds"] is True
        assert np.isclose(result["i_v_plus_s"], 50.0)
        assert np.isclose(result["ii_c"], 50.0)

    def test_proportionality_expanded_holds(self):
        """Expanded reproduction: I(v+s) > II(c) should be detected."""
        # Expanded reproduction: I(v+s) > II(c)
        # Dept I: c=100, v=50, s=50 -> v+s = 100
        # Dept II: c=80, v=30, s=20 -> c = 80
        result = departments.check_proportionality(
            dept_i_c=100.0,
            dept_i_v=50.0,
            dept_i_s=50.0,
            dept_ii_c=80.0,
            dept_ii_v=30.0,
            dept_ii_s=20.0,
        )

        assert result["expanded_reproduction_holds"] is True
        assert result["i_v_plus_s"] > result["ii_c"]
        assert result["surplus_ratio"] > 1.0

    def test_proportionality_breakdown(self):
        """When I(v+s) < II(c), proportionality breaks down."""
        # Breakdown: I(v+s) < II(c)
        # Dept I: c=100, v=20, s=10 -> v+s = 30
        # Dept II: c=50, v=30, s=20 -> c = 50
        result = departments.check_proportionality(
            dept_i_c=100.0,
            dept_i_v=20.0,
            dept_i_s=10.0,
            dept_ii_c=50.0,
            dept_ii_v=30.0,
            dept_ii_s=20.0,
        )

        assert result["simple_reproduction_holds"] is False
        assert result["expanded_reproduction_holds"] is False
        assert result["surplus_ratio"] < 1.0

    def test_proportionality_formula_display(self):
        """Formula display string should be present."""
        result = departments.check_proportionality(
            dept_i_c=50.0,
            dept_i_v=25.0,
            dept_i_s=25.0,
            dept_ii_c=50.0,
            dept_ii_v=30.0,
            dept_ii_s=20.0,
        )

        assert "formula_display" in result
        assert "I(v+s)" in result["formula_display"]
        assert "II(c)" in result["formula_display"]


class TestComputeReproductionFlows:
    """Tests for compute_reproduction_flows function."""

    def test_compute_reproduction_flows_returns_dict(
        self, synthetic_use_matrix_3x3, synthetic_dept_classification
    ):
        """compute_reproduction_flows should return dict with all components."""
        sector_codes = list(synthetic_dept_classification.keys())[:3]
        classification = {code: "Dept_I" if i < 2 else "Dept_II" for i, code in enumerate(sector_codes)}
        value_added = np.array([30.0, 40.0, 50.0])

        result = departments.compute_reproduction_flows(
            use_matrix=synthetic_use_matrix_3x3,
            value_added=value_added,
            classification=classification,
            sector_codes=sector_codes,
        )

        assert isinstance(result, dict)
        assert "dept_i" in result
        assert "dept_ii" in result
        assert "flows" in result
        assert "proportionality" in result

    def test_compute_reproduction_flows_dept_structure(
        self, synthetic_use_matrix_3x3, synthetic_dept_classification
    ):
        """Department dicts should contain c, v, s values."""
        sector_codes = list(synthetic_dept_classification.keys())[:3]
        classification = {code: "Dept_I" if i < 2 else "Dept_II" for i, code in enumerate(sector_codes)}
        value_added = np.array([30.0, 40.0, 50.0])

        result = departments.compute_reproduction_flows(
            use_matrix=synthetic_use_matrix_3x3,
            value_added=value_added,
            classification=classification,
            sector_codes=sector_codes,
        )

        for dept_key in ["dept_i", "dept_ii"]:
            dept = result[dept_key]
            assert "c" in dept
            assert "v" in dept
            assert "s" in dept

    def test_compute_reproduction_flows_includes_proportionality(
        self, synthetic_use_matrix_3x3, synthetic_dept_classification
    ):
        """Result should include proportionality check."""
        sector_codes = list(synthetic_dept_classification.keys())[:3]
        classification = {code: "Dept_I" if i < 2 else "Dept_II" for i, code in enumerate(sector_codes)}
        value_added = np.array([30.0, 40.0, 50.0])

        result = departments.compute_reproduction_flows(
            use_matrix=synthetic_use_matrix_3x3,
            value_added=value_added,
            classification=classification,
            sector_codes=sector_codes,
        )

        prop = result["proportionality"]
        assert "simple_reproduction_holds" in prop
        assert "expanded_reproduction_holds" in prop
