#!/usr/bin/env python3
"""
Wrapper script to run claude_chat.simple_cli from the project root.
This script adds the current directory to Python path and runs the CLI.
"""
import sys
import os
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the main function from simple_cli
from claude_chat.simple_cli import main

if __name__ == "__main__":
    main()