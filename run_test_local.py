#!/usr/bin/env python3
"""
Local wrapper for running PyTorch CI test.sh script
This helps understand the script behavior for migration to Python
"""

import os
import subprocess
import sys
import time
from pathlib import Path

def setup_environment():
    """Setup minimal environment variables for local testing"""
    env = os.environ.copy()
    
    # Required environment variables
    env.update({
        'BUILD_ENVIRONMENT': 'local-macos',
        'TEST_CONFIG': 'smoke',  # Start with smoke tests (minimal)
        'LANG': 'C.UTF-8',
        'TORCH_SERIALIZATION_DEBUG': '1',
        'VALGRIND': 'ON',
        'SHARD_NUMBER': '1',
        'NUM_TEST_SHARDS': '1',
        'PAGER': 'cat'
    })
    
    return env

def run_test_script(timeout=300):
    """Run the test.sh script with proper environment and logging"""
    
    # Change to PyTorch root directory
    pytorch_root = Path(__file__).parent
    os.chdir(pytorch_root)
    
    print(f"🔧 Running from: {pytorch_root}")
    print(f"📁 Current directory: {os.getcwd()}")
    
    # Setup environment
    env = setup_environment()
    
    print("\n🌍 Environment variables set:")
    for key, value in env.items():
        if key.startswith(('BUILD_', 'TEST_', 'TORCH_', 'SHARD_', 'NUM_')):
            print(f"  {key}={value}")
    
    # Run the test script
    cmd = ['bash', '.ci/pytorch/test.sh']
    
    print(f"\n🚀 Running command: {' '.join(cmd)}")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            env=env,
            cwd=pytorch_root,
            capture_output=False,  # Show output in real-time
            text=True,
            timeout=timeout
        )
        
        execution_time = time.time() - start_time
        
        print("=" * 60)
        print(f"✅ Script completed in {execution_time:.2f} seconds")
        print(f"📊 Exit code: {result.returncode}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"⏰ Script timed out after {timeout} seconds")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Script interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Script failed with error: {e}")
        return False

def analyze_test_script():
    """Analyze the test.sh script structure for migration planning"""
    
    script_path = Path('.ci/pytorch/test.sh')
    
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return
    
    print("\n📋 Analyzing test.sh structure...")
    
    with open(script_path, 'r') as f:
        content = f.read()
    
    # Extract key sections
    sections = {
        'Environment Setup': content.count('export '),
        'Conditional Blocks': content.count('if [[ '),
        'Function Calls': content.count('()'),
        'Python Commands': content.count('python '),
        'Test Execution': content.count('test_'),
    }
    
    print("\n📊 Script Analysis:")
    for section, count in sections.items():
        print(f"  {section}: {count} occurrences")
    
    # Find test functions
    import re
    test_functions = re.findall(r'(\w+_test\w*)\s*\(\)', content)
    if test_functions:
        print(f"\n🧪 Test functions found:")
        for func in set(test_functions):
            print(f"  - {func}")

def main():
    """Main execution function"""
    
    print("🐍 PyTorch CI Test Script Local Runner")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--analyze':
        analyze_test_script()
        return
    
    print("This script will help you run test.sh locally for migration analysis.")
    print("The script may fail on some CI-specific parts, but you'll see the core logic.")
    
    response = input("\n🤔 Continue with test execution? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("👋 Exiting...")
        return
    
    # First analyze the script
    analyze_test_script()
    
    print("\n" + "=" * 50)
    print("🚀 Starting test execution...")
    
    success = run_test_script(timeout=600)  # 10 minute timeout
    
    if success:
        print("\n✅ Test script completed successfully!")
        print("You can now analyze the output to understand the migration requirements.")
    else:
        print("\n⚠️  Test script had issues, but you should have seen the core logic.")
        print("This is expected for local runs - focus on understanding the flow.")

if __name__ == '__main__':
    main()
