"""
Claude Chat Manager - Python implementation
A tool for viewing and exporting Claude Code chat history.
"""

__version__ = "0.1.0"
__author__ = "xfpan"
__description__ = "Claude Code chat history viewer and exporter"

from .core import Message, Conversation
from .parser import ClaudeDataParser
from .exporter import MarkdownExporter
from .cli import main

__all__ = [
    "Message",
    "Conversation",
    "ClaudeDataParser",
    "MarkdownExporter",
    "main"
]