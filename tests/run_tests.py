import unittest
import coverage
import sys
import os
from pathlib import Path
import json
from datetime import datetime

def setup_coverage():
    """Initialize coverage.py"""
    cov = coverage.Coverage(
        branch=True,
        source=['src'],
        omit=[
            '*/tests/*',
            '*/site-packages/*',
            '*/dist-packages/*'
        ]
    )
    cov.start()
    return cov

def run_tests():
    """Run all test cases"""
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run tests with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)

def save_coverage_report(cov, results_dir):
    """Generate and save coverage reports"""
    # Create results directory
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Stop coverage measurement
    cov.stop()
    cov.save()
    
    # Generate reports
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # HTML report
    html_dir = results_dir / 'html' / timestamp
    cov.html_report(directory=str(html_dir))
    
    # XML report for CI tools
    xml_file = results_dir / f'coverage_{timestamp}.xml'
    cov.xml_report(outfile=str(xml_file))
    
    # JSON report
    total = cov.report()
    data = {
        'timestamp': datetime.now().isoformat(),
        'total_coverage': total,
        'coverage_by_file': {}
    }
    
    # Get coverage data for each file
    for filename in cov.get_data().measured_files():
        file_coverage = cov.analysis2(filename)
        data['coverage_by_file'][filename] = {
            'total_lines': len(file_coverage[1]),
            'missing_lines': len(file_coverage[3]),
            'coverage_percent': (
                (len(file_coverage[1]) - len(file_coverage[3])) /
                len(file_coverage[1]) * 100
                if len(file_coverage[1]) > 0 else 0
            )
        }
    
    # Save JSON report
    json_file = results_dir / f'coverage_{timestamp}.json'
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    return total, html_dir, xml_file, json_file

def main():
    """Main test runner function"""
    try:
        # Setup coverage
        cov = setup_coverage()
        
        # Run tests
        print("\nRunning tests...")
        result = run_tests()
        
        # Generate coverage reports
        print("\nGenerating coverage reports...")
        total, html_dir, xml_file, json_file = save_coverage_report(
            cov,
            'test_results'
        )
        
        # Print summary
        print("\nTest Summary:")
        print(f"Tests Run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print(f"Skipped: {len(result.skipped)}")
        
        print("\nCoverage Summary:")
        print(f"Total Coverage: {total:.2f}%")
        print(f"HTML Report: {html_dir}")
        print(f"XML Report: {xml_file}")
        print(f"JSON Report: {json_file}")
        
        # Set exit code based on test results and coverage
        min_coverage = 80  # Minimum required coverage percentage
        if len(result.failures) > 0 or len(result.errors) > 0 or total < min_coverage:
            sys.exit(1)
        sys.exit(0)
        
    except Exception as e:
        print(f"Error running tests: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 