"""Test runner script for OEPMS.

Runs all 72 unit test cases (UT-USR, UT-EXM, UT-ATT) via pytest,
and writes the results to a CSV file with columns:
ID, Test Date, Result (Pass/Fail)
"""

import os
import sys

# Ensure backend root is on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import csv
import pytest
from datetime import datetime


class TestResultCollector:
    """Pytest plugin to collect test case execution outcomes."""

    def __init__(self):
        self.results = {}

    def pytest_runtest_logreport(self, report):
        if report.when == "call":
            # Extract test name, e.g. test_UT_USR_01_name_accepts_valid -> UT_USR_01
            parts = report.nodeid.split("::")[-1].split("_")
            if len(parts) >= 4 and parts[0] == "test" and parts[1] == "UT":
                test_id = f"UT_{parts[2]}_{parts[3]}"
                status = "Pass" if report.passed else "Fail"
                self.results[test_id] = status


def main():
    test_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tests")
    collector = TestResultCollector()

    print(f"Running 72 OEPMS Unit Tests from {test_dir}...")
    exit_code = pytest.main(["-v", test_dir], plugins=[collector])

    test_date = datetime.now().strftime("%d/%m/%Y")
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "docs",
        "unit_test_results.csv",
    )
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    # Sort results by module and number
    sorted_ids = sorted(
        collector.results.keys(),
        key=lambda x: (x.split("_")[1], int(x.split("_")[2])),
    )

    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Test Date", "Result (Pass/Fail)"])
        for tid in sorted_ids:
            writer.writerow([tid, test_date, collector.results[tid]])

    total_tests = len(collector.results)
    passed_tests = sum(1 for v in collector.results.values() if v == "Pass")
    failed_tests = total_tests - passed_tests

    print("\n" + "=" * 60)
    print(f"OEPMS UNIT TESTING EXECUTION SUMMARY")
    print(f"Total Test Cases Executed: {total_tests}/72")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"CSV Report written to: {csv_path}")
    print("=" * 60 + "\n")

    return 0 if failed_tests == 0 and total_tests == 72 else 1


if __name__ == "__main__":
    sys.exit(main())
