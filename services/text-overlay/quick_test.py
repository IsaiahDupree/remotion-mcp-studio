#!/usr/bin/env python3
"""
Quick system test for Flask Video Enhancement API

This script performs basic validation that the system components are working.
"""

import os
import sys
import importlib
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing Python imports...")
    
    required_modules = [
        'flask',
        'pandas',
        'numpy',
        'cv2',  # opencv-python
        'openai',
        'moviepy',
        'PIL',  # Pillow
        'whisper',
        'librosa',
        'soundfile',
        'scipy',
        'matplotlib',
        'yt_dlp',
        'dotenv'
    ]
    
    failed_imports = []
    
    for module_name in required_modules:
        try:
            importlib.import_module(module_name)
    print("\n🔍 Testing environment variables...")
    
    # Try to load .env file
    env_file = Path('.env')
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print("  ✅ .env file loaded")
        except ImportError:
            print("  ⚠️  python-dotenv not available, but .env file exists")
    else:
        print("  ⚠️  .env file not found")
    
    # Check important environment variables
    important_vars = ['OPENAI_API_KEY']
    for var in important_vars:
        if os.getenv(var):
            print(f"  ✅ {var} is set")
        else:
            print(f"  ⚠️  {var} not set (AI features may not work)")
    
    return True

def test_basic_functionality():
    """Test basic functionality without actually processing videos"""
    print("\n🔍 Testing basic functionality...")
    
    try:
        # Test CSV logger
        sys.path.insert(0, str(Path(__file__).parent))
        from flask_app import VideoProcessingLogger
        
        # Create a temporary logger
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            temp_csv = f.name
        
        logger = VideoProcessingLogger(temp_csv)
        print("  ✅ VideoProcessingLogger created")
        
        # Test logging a result
        test_result = {
            'success': True,
            'output_video': 'test.mp4',
            'text_overlay': 'Test text',
            'processing_time_seconds': 1.0
        }
        
        logger.log_processing_result(test_result, 'input.mp4', 'Test transcript')
        print("  ✅ CSV logging works")
        
        # Cleanup
        os.unlink(temp_csv)
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error testing basic functionality: {str(e)}")
        return False

def main():
    """Run quick system test"""
    print("🚀 QUICK SYSTEM TEST - Flask Video Enhancement API")
    print("="*60)
    
    tests = [
        ("Python Imports", test_imports),
        ("Flask App", test_flask_app),
        ("Video Processing", test_video_processing),
        ("File Structure", test_file_structure),
        ("Environment Variables", test_environment_variables),
        ("Basic Functionality", test_basic_functionality)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except KeyboardInterrupt:
            print(f"\n❌ Test interrupted by user")
            results[test_name] = False
            break
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*60)
    print("📋 QUICK TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n📊 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 SYSTEM READY!")
        print("The basic system components are working correctly.")
        print("\n🚀 Next steps:")
        print("  • Full testing: python run_tests.py")
        print("  • Deployment check: python deploy_ready.py")
        print("  • Start locally: python start_flask_local.py")
        print("  • Start with Docker: docker-compose up -d")
        return True
    else:
        print("\n⚠️  SYSTEM ISSUES DETECTED")
        print("Please fix the failed tests above before proceeding.")
        print("\n🔧 Common fixes:")
        print("  • Install dependencies: pip install -r requirements.txt")
        print("  • Create .env file with OPENAI_API_KEY=your_key")
        print("  • Ensure all required files are present")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
