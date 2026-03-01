#!/usr/bin/env python3
"""
Wrapper script to run the interactive menu system.
This script adds the current directory to Python path and runs the menu.
"""

import sys
import os
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the main function from menu
from claude_chat.menu import main

if __name__ == "__main__":
    main()