#!/usr/bin/env python3
"""
Comprehensive test runner for Flask Video Enhancement API

This script runs all tests and generates reports before deployment.
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path
import argparse
from datetime import datetime

def run_command(cmd, cwd=None, timeout=300):
    """Run a command and return the result"""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        print(f"Command timed out after {timeout} seconds")
        return False, "", f"Command timed out after {timeout} seconds"
    except Exception as e:
        print(f"Error running command: {e}")
        return False, "", str(e)

def check_dependencies():
    """Check if required testing dependencies are installed"""
    required_packages = [
        'pytest',
        'pytest-cov',
        'pytest-timeout',
        'pytest-mock'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing testing dependencies: {', '.join(missing)}")
        print("Install with: pip install pytest pytest-cov pytest-timeout pytest-mock")
        return False
    
    print("✅ All testing dependencies are installed")
    return True

def run_unit_tests():
    """Run unit tests"""
    print("\n" + "="*60)
    print("🧪 RUNNING UNIT TESTS")
    print("="*60)
    
    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/',
        '-m', 'unit',
        '--tb=short',
        '-v',
        '--durations=10'
    ]
    
    success, stdout, stderr = run_command(cmd)
    
    if success:
        print("✅ Unit tests passed")
    else:
        print("❌ Unit tests failed")
        print("STDOUT:", stdout)
        print("STDERR:", stderr)
    
    return success

def run_integration_tests():
    """Run integration tests"""
    print("\n" + "="*60)
    print("🔗 RUNNING INTEGRATION TESTS")
    print("="*60)
    
    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/',
        '-m', 'integration',
        '--tb=short',
        '-v'
    ]
    
    success, stdout, stderr = run_command(cmd)
    
    if success:
        print("✅ Integration tests passed")
    else:
        print("❌ Integration tests failed")
        print("STDOUT:", stdout)
        print("STDERR:", stderr)
    
    return success

def run_api_tests():
    """Run API tests"""
    print("\n" + "="*60)
    print("🌐 RUNNING API TESTS")
    print("="*60)
    
    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/test_flask_api.py',
        '--tb=short',
        '-v'
    ]
    
    success, stdout, stderr = run_command(cmd)
    
    if success:
        print("✅ API tests passed")
    else:
        print("❌ API tests failed")
        print("STDOUT:", stdout)
        print("STDERR:", stderr)
    
    return success

def run_coverage_tests():
    """Run tests with coverage reporting"""
    print("\n" + "="*60)
    print("📊 RUNNING COVERAGE TESTS")
    print("="*60)
    
    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/',
        '--cov=.',
        '--cov-report=html:htmlcov',
        '--cov-report=term-missing',
        '--cov-report=xml',
        '--tb=short'
    ]
    
    success, stdout, stderr = run_command(cmd, timeout=600)
    
    if success:
        print("✅ Coverage tests completed")
        print("📁 Coverage report generated in htmlcov/")
    else:
        print("❌ Coverage tests failed")
        print("STDOUT:", stdout)
        print("STDERR:", stderr)
    
    return success

def run_static_analysis():
    """Run static code analysis (if tools are available)"""
    print("\n" + "="*60)
    print("🔍 RUNNING STATIC ANALYSIS")
    print("="*60)
    
    tools = ['flake8', 'pylint', 'black --check']
    results = {}
    
    for tool_cmd in tools:
        tool_name = tool_cmd.split()[0]
        print(f"\nRunning {tool_name}...")
        
        try:
            # Check if tool is available
            subprocess.run([tool_name, '--version'], 
                         capture_output=True, 
                         check=True)
            
            if tool_name == 'flake8':
                cmd = [tool_name, '.', '--max-line-length=100', '--exclude=venv,env,.git,__pycache__']
            elif tool_name == 'pylint':
                cmd = [tool_name, '*.py', '--disable=C0111,R0903']
            elif tool_name == 'black':
                cmd = ['black', '--check', '.']
            else:
                continue
                
            success, stdout, stderr = run_command(cmd)
            results[tool_name] = success
            
            if success:
                print(f"✅ {tool_name} passed")
            else:
                print(f"⚠️  {tool_name} found issues")
                
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"⚠️  {tool_name} not available (optional)")
            results[tool_name] = None
    
    return results

def run_security_checks():
    """Run security checks (if tools are available)"""
    print("\n" + "="*60)
    print("🔒 RUNNING SECURITY CHECKS")
    print("="*60)
    
    tools = ['bandit', 'safety']
    results = {}
    
    for tool in tools:
        print(f"\nRunning {tool}...")
        
        try:
            # Check if tool is available
            subprocess.run([tool, '--version'], 
                         capture_output=True, 
                         check=True)
            
            if tool == 'bandit':
                cmd = [tool, '-r', '.', '-f', 'json']
            elif tool == 'safety':
                cmd = [tool, 'check', '--json']
            else:
                continue
                
            success, stdout, stderr = run_command(cmd)
            results[tool] = success
            
            if success:
                print(f"✅ {tool} passed")
            else:
                print(f"⚠️  {tool} found issues")
                
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"⚠️  {tool} not available (optional)")
            results[tool] = None
    
    return results

def generate_test_report(results):
    """Generate a comprehensive test report"""
    report = {
        'timestamp': datetime.now().isoformat(),
        'test_results': results,
        'summary': {
            'total_test_suites': len([k for k in results.keys() if k.endswith('_tests')]),
            'passed_test_suites': len([k for k, v in results.items() if k.endswith('_tests') and v]),
            'overall_success': all(v for k, v in results.items() if k.endswith('_tests'))
        }
    }
    
    # Write JSON report
    with open('test_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    # Write human-readable report
    with open('test_report.txt', 'w') as f:
        f.write("Video Enhancement API - Test Report\n")
        f.write("="*50 + "\n")
        f.write(f"Generated: {report['timestamp']}\n\n")
        
        f.write("Test Results:\n")
        for test_name, result in results.items():
            if test_name.endswith('_tests'):
                status = "✅ PASS" if result else "❌ FAIL"
                f.write(f"  {status} - {test_name.replace('_', ' ').title()}\n")
        
        f.write(f"\nOverall Status: {'✅ PASS' if report['summary']['overall_success'] else '❌ FAIL'}\n")
        f.write(f"Test Suites: {report['summary']['passed_test_suites']}/{report['summary']['total_test_suites']} passed\n")

def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description='Run comprehensive tests for Video Enhancement API')
    parser.add_argument('--quick', action='store_true', help='Run only essential tests')
    parser.add_argument('--unit-only', action='store_true', help='Run only unit tests')
    parser.add_argument('--coverage', action='store_true', help='Run with coverage reporting')
    parser.add_argument('--all', action='store_true', help='Run all tests including optional checks')
    
    args = parser.parse_args()
    
    print("🚀 VIDEO ENHANCEMENT API - TEST SUITE")
    print("="*60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    results = {}
    
    try:
        # Always run unit tests
        results['unit_tests'] = run_unit_tests()
        
        if args.unit_only:
            print("\n✅ Unit tests completed (--unit-only flag)")
        else:
            # Run API tests
            results['api_tests'] = run_api_tests()
            
            if not args.quick:
                # Run integration tests
                results['integration_tests'] = run_integration_tests()
                
                # Run coverage if requested or if --all flag
                if args.coverage or args.all:
                    results['coverage_tests'] = run_coverage_tests()
                
                # Run optional checks if --all flag
                if args.all:
                    static_results = run_static_analysis()
                    security_results = run_security_checks()
                    results.update(static_results)
                    results.update(security_results)
        
        # Generate report
        generate_test_report(results)
        
        # Summary
        print("\n" + "="*60)
        print("📋 TEST SUMMARY")
        print("="*60)
        
        essential_tests = ['unit_tests', 'api_tests', 'integration_tests']
        essential_results = {k: v for k, v in results.items() if k in essential_tests}
        
        for test_name, result in essential_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name.replace('_', ' ').title()}")
        
        overall_success = all(essential_results.values())
        
        print(f"\n🎯 Overall Status: {'✅ READY FOR DEPLOYMENT' if overall_success else '❌ NOT READY FOR DEPLOYMENT'}")
        
        if overall_success:
            print("\n🚀 All essential tests passed! You can proceed with deployment.")
            print("📁 Test reports saved to test_report.json and test_report.txt")
            if 'coverage_tests' in results:
                print("📊 Coverage report available in htmlcov/index.html")
        else:
            print("\n⚠️  Some tests failed. Please fix issues before deployment.")
            print("📁 Check test_report.txt for detailed results")
        
        return overall_success
        
    except KeyboardInterrupt:
        print("\n❌ Test suite interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
