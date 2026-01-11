#!/usr/bin/env python3
"""
Test script to verify ASMO-01 Health Monitoring setup
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 60)
print("🧪 ASMO-01 Health Monitoring - Setup Test")
print("=" * 60)
print()

# Test 1: Python version
print("1️⃣  Checking Python version...")
if sys.version_info >= (3, 8):
    print(f"   ✅ Python {sys.version_info.major}.{sys.version_info.minor} OK")
else:
    print(f"   ❌ Python {sys.version_info.major}.{sys.version_info.minor} (need 3.8+)")
    sys.exit(1)

# Test 2: Required modules
print("\n2️⃣  Checking Python modules...")
required_modules = ['docker', 'psutil']
missing = []

for module in required_modules:
    try:
        __import__(module)
        print(f"   ✅ {module}")
    except ImportError:
        print(f"   ❌ {module} (run: pip3 install -r requirements.txt)")
        missing.append(module)

if missing:
    print(f"\n   ⚠️  Missing modules: {', '.join(missing)}")
    print("   Run: pip3 install -r requirements.txt --break-system-packages")
    sys.exit(1)

# Test 3: Docker connection
print("\n3️⃣  Checking Docker connection...")
try:
    import docker
    client = docker.DockerClient(base_url="unix:///var/run/docker.sock")
    containers = client.containers.list()
    print(f"   ✅ Docker OK ({len(containers)} containers running)")
    client.close()
except Exception as e:
    print(f"   ❌ Docker connection failed: {e}")
    print("   Tip: Add your user to docker group: sudo usermod -aG docker $USER")
    sys.exit(1)

# Test 4: Config file
print("\n4️⃣  Checking configuration...")
config_path = Path(__file__).parent.parent / "config.json"
if config_path.exists():
    print(f"   ✅ config.json exists")
    try:
        with open(config_path) as f:
            config = json.load(f)
        print(f"   ✅ config.json is valid JSON")
    except json.JSONDecodeError as e:
        print(f"   ❌ config.json is invalid: {e}")
        sys.exit(1)
else:
    print(f"   ⚠️  config.json not found")
    print("   Run: python3 src/monitor.py --create-config")

# Test 5: Directory structure
print("\n5️⃣  Checking directory structure...")
dirs_to_check = [
    Path(__file__).parent.parent / "data",
    Path(__file__).parent.parent / "logs",
    Path(__file__).parent.parent / "src" / "utils",
]

for dir_path in dirs_to_check:
    if dir_path.exists():
        print(f"   ✅ {dir_path.name}/")
    else:
        print(f"   ⚠️  {dir_path.name}/ (will be created on first run)")

# Test 6: Scripts are executable
print("\n6️⃣  Checking scripts...")
scripts = [
    Path(__file__).parent / "monitor.py",
    Path(__file__).parent / "reporter.py",
]

for script in scripts:
    if script.exists():
        is_executable = script.stat().st_mode & 0o111
        if is_executable:
            print(f"   ✅ {script.name} (executable)")
        else:
            print(f"   ⚠️  {script.name} (not executable, use: chmod +x)")
    else:
        print(f"   ❌ {script.name} missing!")

# Test 7: Quick metrics collection test
print("\n7️⃣  Testing metrics collection...")
try:
    from utils.metrics import get_all_system_metrics
    metrics = get_all_system_metrics()
    print(f"   ✅ System metrics: CPU {metrics['cpu']['cpu_percent']}%, RAM {metrics['memory']['ram_percent']}%")
except Exception as e:
    print(f"   ❌ Metrics collection failed: {e}")

# Test 8: Storage test
print("\n8️⃣  Testing storage...")
try:
    from utils.storage import HealthStorage
    test_file = Path(__file__).parent.parent / "data" / "test_history.json"
    storage = HealthStorage(str(test_file), retention_days=7)
    
    # Add test entry
    storage.add_entry({'test': 'data', 'timestamp': '2026-01-11T10:00:00'})
    
    # Read it back
    history = storage.load_history()
    if len(history) > 0:
        print(f"   ✅ Storage working ({len(history)} entries)")
    
    # Cleanup
    test_file.unlink(missing_ok=True)
except Exception as e:
    print(f"   ❌ Storage test failed: {e}")

print("\n" + "=" * 60)
print("✅ Setup test complete!")
print("=" * 60)
print()
print("Next steps:")
print("  1. Run: python3 src/monitor.py --test --verbose")
print("  2. Run: python3 src/reporter.py --test --verbose")
print("  3. Configure n8n workflows (see QUICKSTART.md)")
print()
