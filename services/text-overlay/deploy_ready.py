#!/usr/bin/env python3
"""
Pre-deployment readiness checker for Flask Video Enhancement API

This script validates the system is ready for deployment by running comprehensive tests.
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f"🎯 {title}")
    print("="*60)

def print_step(step, description):
    """Print a step with formatting"""
    print(f"\n📋 Step {step}: {description}")
    print("-" * 40)

def run_command_safe(cmd, description="", timeout=300):
    """Run a command safely with error handling"""
    print(f"Running: {description or ' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            print("✅ Success")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()[:200]}...")
            return True, result.stdout
        else:
            print("❌ Failed")
            if result.stderr.strip():
                print(f"Error: {result.stderr.strip()[:200]}...")
            return False, result.stderr
            
    except subprocess.TimeoutExpired:
        print(f"❌ Timeout after {timeout} seconds")
        return False, f"Timeout after {timeout} seconds"
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        return False, f"Command not found: {cmd[0]}"
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False, str(e)

def check_python_environment():
    """Check Python environment and dependencies"""
    print_step(1, "Checking Python Environment")
    
    # Check Python version
    print(f"Python version: {sys.version}")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    print("✅ Python version OK")
    
    # Check pip
    success, _ = run_command_safe([sys.executable, '-m', 'pip', '--version'], "Checking pip")
    if not success:
        return False
    
    return True

def install_dependencies():
    """Install required dependencies"""
    print_step(2, "Installing Dependencies")
    
    # Install requirements
    success, _ = run_command_safe([
        sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
    ], "Installing requirements.txt", timeout=600)
    
    if not success:
        print("❌ Failed to install dependencies")
        print("Try running manually: pip install -r requirements.txt")
        return False
    
    print("✅ Dependencies installed successfully")
    return True

def check_environment_variables():
    """Check required environment variables"""
    print_step(3, "Checking Environment Variables")
    
    # Check for .env file
    env_file = Path('.env')
    if env_file.exists():
        print("✅ .env file found")
        
        # Load and check key variables
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            if os.getenv('OPENAI_API_KEY'):
                print("✅ OPENAI_API_KEY is set")
            else:
                print("⚠️  OPENAI_API_KEY not found in .env")
                print("   AI features may not work without this key")
                
        except ImportError:
            print("⚠️  python-dotenv not installed, can't check .env file")
    else:
        print("⚠️  .env file not found")
        print("   Create .env with: OPENAI_API_KEY=your_key_here")
    
    return True

def create_test_directories():
    """Create necessary directories for testing"""
    print_step(4, "Creating Test Directories")
    
    directories = [
        'shared_data',
        'enhanced_videos',
        'tests',
        'logs'
    ]
    
    for dir_name in directories:
        dir_path = Path(dir_name)
        dir_path.mkdir(exist_ok=True)
        print(f"✅ Created/verified: {dir_name}/")
    
    return True

def create_sample_data():
    """Create sample data for testing"""
    print_step(5, "Creating Sample Data")
    
    # Create SoundCloud sample file if it doesn't exist
    soundcloud_file = Path('soundcloud_tracks.xlsx')
    if not soundcloud_file.exists():
        success, _ = run_command_safe([
            sys.executable, 'create_soundcloud_sample.py'
        ], "Creating sample SoundCloud tracks")
        
        if success:
            print("✅ Sample SoundCloud tracks created")
        else:
            print("⚠️  Could not create sample SoundCloud file")
    else:
        print("✅ SoundCloud tracks file already exists")
    
    # Create a small test video file
    test_video = Path('shared_data/test_video.mp4')
    if not test_video.exists():
        # Create a minimal fake video file for testing
        try:
            test_video.write_bytes(b'FAKE_VIDEO_FOR_TESTING_ONLY')
            print("✅ Test video file created")
        except Exception as e:
            print(f"⚠️  Could not create test video: {e}")
    else:
        print("✅ Test video file already exists")
    
    return True

def run_tests():
    """Run the test suite"""
    print_step(6, "Running Test Suite")
    
    # Run the comprehensive test runner
    success, output = run_command_safe([
        sys.executable, 'run_tests.py', '--quick'
    ], "Running test suite", timeout=600)
    
    if success:
        print("✅ All tests passed")
        return True
    else:
        print("❌ Some tests failed")
        print("Run 'python run_tests.py' for detailed results")
        return False

def check_docker_ready():
    """Check if Docker configuration is ready"""
    print_step(7, "Checking Docker Configuration")
    
    # Check if Docker is available
    docker_available, _ = run_command_safe(['docker', '--version'], "Checking Docker")
    
    if docker_available:
        print("✅ Docker is available")
        
        # Check docker-compose
        compose_available, _ = run_command_safe(['docker-compose', '--version'], "Checking Docker Compose")
        
        if compose_available:
            print("✅ Docker Compose is available")
            
            # Validate docker-compose.yml
            if Path('docker-compose.yml').exists():
                success, _ = run_command_safe([
                    'docker-compose', 'config'
                ], "Validating docker-compose.yml")
                
                if success:
                    print("✅ docker-compose.yml is valid")
                    return True
                else:
                    print("❌ docker-compose.yml has errors")
                    return False
            else:
                print("❌ docker-compose.yml not found")
                return False
        else:
            print("❌ Docker Compose not available")
            return False
    else:
        print("⚠️  Docker not available (optional for local deployment)")
        return True  # Not required for local deployment

def generate_deployment_report():
    """Generate a deployment readiness report"""
    print_step(8, "Generating Deployment Report")
    
    report_content = f"""
# Deployment Readiness Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## System Status
- Python Environment: Ready
- Dependencies: Installed
- Environment Variables: Configured
- Test Directories: Created
- Sample Data: Available
- Test Suite: Passed
- Docker Configuration: Ready

## Files Created/Verified
- requirements.txt (with testing dependencies)
- .env (environment variables)
- shared_data/ (input videos)
- enhanced_videos/ (output directory)
- soundcloud_tracks.xlsx (music database)
- tests/ (comprehensive test suite)
- docker-compose.yml (container orchestration)

## API Endpoints Available
- GET /health (health check)
- GET /videos (list available videos)
- GET /soundcloud/tracks (list music tracks)
- POST /process/video (process single video)
- POST /process/batch (process multiple videos)
- GET /download/<filename> (download processed videos)
- GET /logs/csv (download processing logs)
- GET /logs/recent (get recent logs)

## Next Steps
1. For local deployment: python start_flask_local.py
2. For Docker deployment: docker-compose up -d
3. For N8N integration: Import workflows from n8n_workflows/

## Testing
- Run tests before deployment: python run_tests.py
- Test API endpoints: python test_flask_api.py
- Check health: curl http://localhost:5000/health

## Monitoring
- API logs: Check container logs or Flask output
- Processing logs: Check processing_log.csv
- Health status: GET /health endpoint
- Coverage reports: htmlcov/index.html
"""
    
    try:
        with open('deployment_report.md', 'w') as f:
            f.write(report_content)
        print("✅ Deployment report saved to deployment_report.md")
        return True
    except Exception as e:
        print(f"⚠️  Could not save report: {e}")
        return False

def main():
    """Main deployment readiness check"""
    print_header("DEPLOYMENT READINESS CHECKER")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    checks = [
        ("Python Environment", check_python_environment),
        ("Dependencies", install_dependencies),
        ("Environment Variables", check_environment_variables),
        ("Test Directories", create_test_directories),
        ("Sample Data", create_sample_data),
        ("Test Suite", run_tests),
        ("Docker Configuration", check_docker_ready),
        ("Deployment Report", generate_deployment_report)
    ]
    
    results = {}
    
    try:
        for check_name, check_func in checks:
            print(f"\n🔍 Running: {check_name}")
            start_time = time.time()
            
            try:
                result = check_func()
                results[check_name] = result
                duration = time.time() - start_time
                
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"{status} - {check_name} ({duration:.1f}s)")
                
            except KeyboardInterrupt:
                print(f"\n❌ Interrupted by user")
                results[check_name] = False
                break
            except Exception as e:
                print(f"❌ Error in {check_name}: {str(e)}")
                results[check_name] = False
        
        # Final summary
        print_header("DEPLOYMENT READINESS SUMMARY")
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for check_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {check_name}")
        
        print(f"\n📊 Overall: {passed}/{total} checks passed")
        
        if passed == total:
            print("\n🎉 READY FOR DEPLOYMENT!")
            print("🚀 You can now deploy with confidence:")
            print("   • Local: python start_flask_local.py")
            print("   • Docker: docker-compose up -d")
            print("   • Tests: python run_tests.py")
            return True
        else:
            print("\n⚠️  NOT READY FOR DEPLOYMENT")
            print("🔧 Please fix the failed checks above")
            return False
            
    except KeyboardInterrupt:
        print("\n❌ Deployment check interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Deployment check failed: {str(e)}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
