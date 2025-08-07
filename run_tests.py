#!/usr/bin/env python3
"""
Test runner for the HRF Newsletter Generation System.
Runs all unit tests and provides detailed reporting.
"""

import unittest
import sys
import os
import time
from io import StringIO

# Fix Windows console encoding issues
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'scripts'))
sys.path.insert(0, os.path.join(project_root, 'tests'))

def run_all_tests():
    """Run all unit tests and provide detailed reporting."""
    
    print("🧪 HRF Newsletter System - Unit Test Runner")
    print("=" * 60)
    print(f"📁 Project Root: {project_root}")
    print(f"🐍 Python Version: {sys.version}")
    print("=" * 60)
    
    # Discover and run tests
    start_time = time.time()
    
    # Create test loader
    loader = unittest.TestLoader()
    
    # Discover tests in the tests directory
    test_dir = os.path.join(project_root, 'tests')
    if not os.path.exists(test_dir):
        print(f"❌ Test directory not found: {test_dir}")
        return False
    
    # Load test suite
    print(f"🔍 Discovering tests in: {test_dir}")
    suite = loader.discover(test_dir, pattern='test_*.py')
    
    # Count total tests
    test_count = suite.countTestCases()
    print(f"📊 Found {test_count} test cases")
    print("=" * 60)
    
    if test_count == 0:
        print("⚠️  No tests found!")
        return False
    
    # Create test runner with custom result class for better reporting
    class DetailedTestResult(unittest.TextTestResult):
        def __init__(self, stream, descriptions, verbosity):
            super().__init__(stream, descriptions, verbosity)
            self.test_results = []
        
        def addSuccess(self, test):
            super().addSuccess(test)
            self.test_results.append(('PASS', test, None))
        
        def addError(self, test, err):
            super().addError(test, err)
            self.test_results.append(('ERROR', test, err))
        
        def addFailure(self, test, err):
            super().addFailure(test, err)
            self.test_results.append(('FAIL', test, err))
        
        def addSkip(self, test, reason):
            super().addSkip(test, reason)
            self.test_results.append(('SKIP', test, reason))
    
    # Run tests
    stream = StringIO()
    runner = unittest.TextTestRunner(
        stream=stream,
        verbosity=2,
        resultclass=DetailedTestResult
    )
    
    print("🚀 Running tests...")
    result = runner.run(suite)
    
    # Calculate execution time
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Print detailed results
    print("\n" + "=" * 60)
    print("📋 DETAILED TEST RESULTS")
    print("=" * 60)
    
    # Group results by status
    passed = []
    failed = []
    errors = []
    skipped = []
    
    for status, test, err in result.test_results:
        test_name = f"{test.__class__.__name__}.{test._testMethodName}"
        if status == 'PASS':
            passed.append(test_name)
        elif status == 'FAIL':
            failed.append((test_name, err))
        elif status == 'ERROR':
            errors.append((test_name, err))
        elif status == 'SKIP':
            skipped.append((test_name, err))
    
    # Print passed tests
    if passed:
        print(f"\n✅ PASSED TESTS ({len(passed)}):")
        for test_name in passed:
            print(f"   ✓ {test_name}")
    
    # Print failed tests
    if failed:
        print(f"\n❌ FAILED TESTS ({len(failed)}):")
        for test_name, err in failed:
            print(f"   ✗ {test_name}")
            if err:
                print(f"     Error: {err[1]}")
    
    # Print error tests
    if errors:
        print(f"\n💥 ERROR TESTS ({len(errors)}):")
        for test_name, err in errors:
            print(f"   💥 {test_name}")
            if err:
                print(f"     Error: {err[1]}")
    
    # Print skipped tests
    if skipped:
        print(f"\n⏭️  SKIPPED TESTS ({len(skipped)}):")
        for test_name, reason in skipped:
            print(f"   ⏭️  {test_name}")
            if reason:
                print(f"     Reason: {reason}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"⏱️  Execution Time: {execution_time:.2f} seconds")
    print(f"🧪 Total Tests: {result.testsRun}")
    print(f"✅ Passed: {len(passed)}")
    print(f"❌ Failed: {len(failed)}")
    print(f"💥 Errors: {len(errors)}")
    print(f"⏭️  Skipped: {len(skipped)}")
    
    # Calculate success rate
    if result.testsRun > 0:
        success_rate = (len(passed) / result.testsRun) * 100
        print(f"📈 Success Rate: {success_rate:.1f}%")
    
    # Overall result
    if result.wasSuccessful():
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("✨ Your credential management system is working correctly!")
    else:
        print(f"\n💥 {len(failed) + len(errors)} TEST(S) FAILED")
        print("🔧 Please review the failed tests and fix the issues.")
    
    print("=" * 60)
    
    return result.wasSuccessful()

def run_specific_test_class(test_class_name):
    """Run tests for a specific test class."""
    print(f"🎯 Running tests for: {test_class_name}")
    
    # Import the test module
    try:
        import tests.test_credential_management as test_module
        test_class = getattr(test_module, test_class_name)
    except (ImportError, AttributeError) as e:
        print(f"❌ Could not find test class: {test_class_name}")
        print(f"Error: {e}")
        return False
    
    # Create test suite for specific class
    suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    # Check command line arguments
    if len(sys.argv) > 1:
        # Run specific test class
        test_class_name = sys.argv[1]
        success = run_specific_test_class(test_class_name)
    else:
        # Run all tests
        success = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
