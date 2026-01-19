#!/usr/bin/env python3
"""Verify 100% branch coverage on core modules.

This script is used by CI to enforce coverage requirements on critical business logic.
Exit code 0 = all core modules have 100% coverage
Exit code 1 = one or more core modules below 100%

Usage:
    python scripts/check_core_coverage.py
"""
import subprocess
import sys
import re

# Core modules that MUST have 100% branch coverage
# These contain critical business logic for payments and security
CORE_MODULES = [
    "app/core/auth.py",
    "app/services/payments.py", 
    "app/services/stripe/client.py",
    "app/db/repository.py",
    "app/api/webhooks/stripe.py",
]

REQUIRED_COVERAGE = 100


def run_coverage():
    """Run pytest with coverage and return output."""
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            "--cov=app",
            "--cov-branch", 
            "--cov-report=term-missing",
            "-q",
        ],
        capture_output=True,
        text=True,
    )
    return result.stdout + result.stderr


def parse_coverage(output: str) -> dict[str, int]:
    """Parse coverage output and return module -> coverage mapping."""
    coverage = {}
    # Pattern: app\core\auth.py    15      0      8      0   100%
    # Or:      app/core/auth.py    15      0      8      0   100%
    pattern = r"(app[/\\][^\s]+\.py)\s+\d+\s+\d+\s+\d+\s+\d+\s+(\d+)%"
    
    for match in re.finditer(pattern, output):
        module_path = match.group(1).replace("\\", "/")
        coverage_pct = int(match.group(2))
        coverage[module_path] = coverage_pct
    
    return coverage


def main():
    print("=" * 60)
    print("CORE MODULE COVERAGE CHECK")
    print("=" * 60)
    print(f"\nRequired coverage: {REQUIRED_COVERAGE}%")
    print(f"Core modules: {len(CORE_MODULES)}\n")
    
    # Run coverage
    print("Running tests with branch coverage...")
    output = run_coverage()
    
    # Parse results
    coverage = parse_coverage(output)
    
    if not coverage:
        print("❌ ERROR: Could not parse coverage output")
        print("\nRaw output:")
        print(output)
        return 1
    
    # Check each core module
    failures = []
    successes = []
    
    print("\nCore Module Results:")
    print("-" * 60)
    
    for module in CORE_MODULES:
        if module not in coverage:
            print(f"  [?] {module}: NOT FOUND IN COVERAGE")
            failures.append((module, "NOT FOUND"))
        elif coverage[module] < REQUIRED_COVERAGE:
            print(f"  [FAIL] {module}: {coverage[module]}% (required: {REQUIRED_COVERAGE}%)")
            failures.append((module, coverage[module]))
        else:
            print(f"  [OK] {module}: {coverage[module]}%")
            successes.append(module)
    
    print("-" * 60)
    
    # Summary
    print(f"\nSummary: {len(successes)}/{len(CORE_MODULES)} core modules at 100%")
    
    if failures:
        print("\n[FAILED] COVERAGE CHECK FAILED")
        print("\nModules below required coverage:")
        for module, cov in failures:
            print(f"  - {module}: {cov}")
        print("\nCI will fail until these modules reach 100% branch coverage.")
        return 1
    
    print("\n[PASSED] ALL CORE MODULES HAVE 100% BRANCH COVERAGE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
