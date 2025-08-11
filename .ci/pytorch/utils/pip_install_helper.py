#!/usr/bin/env python3
"""
Helper script to handle pip installations in externally-managed environments.

This script provides safe pip installation methods that work across different
Python environments, including externally-managed environments like Homebrew.
"""

import sys
import subprocess
import logging

def is_externally_managed():
    """Check if the current Python environment is externally managed."""
    try:
        # Try a test pip install to see if it's externally managed
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '--dry-run', 'pip'
        ], capture_output=True, text=True)
        
        return 'externally-managed-environment' in result.stderr
    except Exception:
        return False

def is_virtual_env():
    """Check if we're running in a virtual environment."""
    return (hasattr(sys, 'real_prefix') or 
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))

def pip_install_safe(packages, user_install=False, break_system_packages=False):
    """
    Safely install pip packages with appropriate flags for the environment.
    
    Args:
        packages: List of package names to install
        user_install: Force user installation
        break_system_packages: Allow breaking system packages (use with caution)
    
    Returns:
        bool: True if installation succeeded, False otherwise
    """
    if not isinstance(packages, list):
        packages = [packages]
    
    cmd = [sys.executable, '-m', 'pip', 'install', '--progress-bar', 'off']
    
    # Determine installation strategy
    if is_virtual_env():
        logging.info("Virtual environment detected, using standard pip install")
    elif is_externally_managed():
        logging.info("Externally-managed environment detected")
        if user_install:
            logging.info("Using --user installation")
            cmd.append('--user')
        elif break_system_packages:
            logging.warning("Using --break-system-packages (use with caution)")
            cmd.append('--break-system-packages')
        else:
            logging.info("Attempting user installation as safe fallback")
            cmd.append('--user')
    
    cmd.extend(packages)
    
    try:
        logging.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info(f"Successfully installed: {', '.join(packages)}")
            return True
        else:
            logging.error(f"Pip install failed with exit code {result.returncode}")
            logging.error(f"STDERR: {result.stderr}")
            
            # If user install failed and we haven't tried break-system-packages, try it
            if not break_system_packages and '--user' in cmd and is_externally_managed():
                logging.info("Retrying with --break-system-packages")
                return pip_install_safe(packages, user_install=False, break_system_packages=True)
            
            return False
            
    except Exception as e:
        logging.error(f"Exception during pip install: {e}")
        return False

def ensure_packages(packages):
    """
    Ensure packages are installed, trying multiple strategies if needed.
    
    Args:
        packages: List of package names to ensure are installed
        
    Returns:
        bool: True if all packages are available, False otherwise
    """
    if not isinstance(packages, list):
        packages = [packages]
    
    # First, check if packages are already available
    missing_packages = []
    for package in packages:
        try:
            # Try to import the package (handle common name mappings)
            import_name = package.split('==')[0].split('>=')[0].split('<=')[0]
            if import_name == 'ninja':
                # ninja package doesn't have a direct import, check if it's in PATH
                result = subprocess.run(['which', 'ninja'], capture_output=True)
                if result.returncode != 0:
                    missing_packages.append(package)
            else:
                __import__(import_name)
        except ImportError:
            missing_packages.append(package)
    
    if not missing_packages:
        logging.info(f"All packages already available: {', '.join(packages)}")
        return True
    
    logging.info(f"Missing packages: {', '.join(missing_packages)}")
    
    # Try to install missing packages
    return pip_install_safe(missing_packages)

def main():
    """Main entry point for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Safe pip installer for various environments')
    parser.add_argument('packages', nargs='+', help='Packages to install')
    parser.add_argument('--user', action='store_true', help='Force user installation')
    parser.add_argument('--break-system-packages', action='store_true', 
                       help='Allow breaking system packages')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(levelname)s: %(message)s')
    
    # Install packages
    success = pip_install_safe(args.packages, 
                              user_install=args.user,
                              break_system_packages=args.break_system_packages)
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
