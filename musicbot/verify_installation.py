#!/usr/bin/env python3
"""
Installation Verification Script
Tests all core components to ensure proper setup
"""

import sys
import os
import asyncio
import importlib.util

def check_python_version():
    """Check Python version requirement"""
    print("🔍 Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Required: 3.10+")
        return False

def check_system_dependencies():
    """Check for required system dependencies"""
    print("\n🔍 Checking system dependencies...")
    
    # Check FFmpeg
    import subprocess
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ FFmpeg - {version_line}")
        else:
            print("❌ FFmpeg - Not working properly")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ FFmpeg - Not found")
        return False
    
    return True

def check_python_packages():
    """Check for required Python packages"""
    print("\n🔍 Checking Python packages...")
    
    required_packages = [
        'pyrogram',
        'tgcrypto', 
        'pytgcalls',
        'yt_dlp',
        'aiohttp',
        'aiofiles'
    ]
    
    optional_packages = [
        'motor',
        'pymongo',
        'redis'
    ]
    
    all_good = True
    
    # Check required packages
    for package in required_packages:
        try:
            importlib.import_module(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Required but not installed")
            all_good = False
    
    # Check optional packages
    print("\n📦 Optional packages:")
    for package in optional_packages:
        try:
            importlib.import_module(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"⚠️  {package} - Optional (some features disabled)")
    
    return all_good

def check_project_structure():
    """Check project file structure"""
    print("\n🔍 Checking project structure...")
    
    required_files = [
        'bot.py',
        'config.py',
        'requirements.txt',
        '.env.example',
        'core/calls.py',
        'core/downloader.py',
        'core/player.py',
        'core/queue.py',
        'handlers/__init__.py',
        'handlers/play.py',
        'handlers/control.py',
        'handlers/queue.py',
        'handlers/admin.py',
        'utils/filters.py',
        'utils/decorators.py',
        'utils/time.py',
        'database/mongo.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    else:
        print("✅ All required files present")
        return True

def check_config_setup():
    """Check configuration setup"""
    print("\n🔍 Checking configuration...")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️  .env file not found - Copy from .env.example")
        return False
    
    # Try to import config
    try:
        from config import config
        print("✅ Configuration module loaded")
        
        # Check required config values
        required_configs = ['BOT_TOKEN', 'API_ID', 'API_HASH']
        missing_configs = []
        
        for config_name in required_configs:
            if not getattr(config, config_name, None):
                missing_configs.append(config_name)
        
        if missing_configs:
            print(f"⚠️  Missing configuration values: {', '.join(missing_configs)}")
            print("   Please set these in your .env file")
            return False
        else:
            print("✅ Required configuration values present")
            return True
            
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

async def test_core_modules():
    """Test core module imports and basic functionality"""
    print("\n🔍 Testing core modules...")
    
    try:
        # Test downloader
        from core.downloader import downloader
        print("✅ Downloader module loaded")
        
        # Test basic downloader functionality
        info = await downloader.extract_info("test")
        print("✅ Downloader basic functionality working")
        
    except Exception as e:
        print(f"⚠️  Core module test warning: {e}")
        print("   This might be normal if not connected to internet")
    
    try:
        # Test queue manager
        from core.queue import queue_manager
        print("✅ Queue manager loaded")
        
        # Test basic queue operations
        queue_info = queue_manager.get_queue_info(-1)  # Test chat ID
        print("✅ Queue manager basic functionality working")
        
    except Exception as e:
        print(f"⚠️  Queue manager test warning: {e}")

def main():
    """Run all verification checks"""
    print("🎵 Telegram Music Bot - Installation Verification")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("System Dependencies", check_system_dependencies),
        ("Python Packages", check_python_packages),
        ("Project Structure", check_project_structure),
        ("Configuration", check_config_setup)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            if asyncio.iscoroutinefunction(check_func):
                result = asyncio.run(check_func())
            else:
                result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name} check failed: {e}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {check_name}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All checks passed! Your bot is ready to run.")
        print("\nNext steps:")
        print("1. Make sure your .env file is properly configured")
        print("2. Run './start.sh' (Linux/Mac) or 'start.bat' (Windows)")
        print("3. Enjoy your music bot!")
    else:
        print(f"\n⚠️  {total - passed} check(s) failed.")
        print("Please fix the issues above before running the bot.")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)