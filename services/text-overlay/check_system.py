#!/usr/bin/env python3
"""
Command-line interface for system compatibility checker.
"""

import argparse
import sys
from utils.system_check import main as run_system_check

def main():
    """Parse command-line arguments and run system check."""
    parser = argparse.ArgumentParser(
        description="Check system compatibility for Smart Text-on-Video Overlay Tool"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Show detailed information about system components"
    )
    parser.add_argument(
        "--export", "-e", 
        type=str, 
        help="Export results to file (json or txt)"
    )
    
    args = parser.parse_args()
    
    # Run system check
    run_system_check(verbose=args.verbose, export_file=args.export)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
