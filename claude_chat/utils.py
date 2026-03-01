"""
Utility functions for Claude chat manager.
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional


def read_jsonl_file(filepath: Path) -> list:
    """
    Read and parse a JSONL file.

    Args:
        filepath: Path to JSONL file

    Returns:
        List of parsed JSON objects
    """
    data = []
    if not filepath.exists():
        return data

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    item = json.loads(line)
                    data.append(item)
                except json.JSONDecodeError as e:
                    print(f"Warning: Failed to parse line {line_num} in {filepath}: {e}")
                    continue
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")

    return data


def write_jsonl_file(filepath: Path, data: list) -> bool:
    """
    Write data to a JSONL file.

    Args:
        filepath: Path to output file
        data: List of objects to write

    Returns:
        True if successful, False otherwise
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            for item in data:
                json_line = json.dumps(item, ensure_ascii=False)
                f.write(json_line + '\n')
        return True
    except Exception as e:
        print(f"Error writing file {filepath}: {e}")
        return False


def parse_timestamp(timestamp: Any) -> datetime:
    """
    Parse timestamp from various formats.

    Args:
        timestamp: Timestamp value (int, float, or str)

    Returns:
        Datetime object
    """
    try:
        if isinstance(timestamp, (int, float)):
            # Handle milliseconds
            if timestamp > 1000000000000:  # Likely milliseconds
                return datetime.fromtimestamp(timestamp / 1000)
            else:  # Likely seconds
                return datetime.fromtimestamp(timestamp)
        elif isinstance(timestamp, str):
            # Try ISO format
            if 'T' in timestamp:
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                # Try other common formats
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%H:%M:%S']:
                    try:
                        return datetime.strptime(timestamp, fmt)
                    except ValueError:
                        continue
                return datetime.now()
        else:
            return datetime.now()
    except (ValueError, TypeError, OverflowError):
        return datetime.now()


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.0f}秒"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}分钟"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}小时"


def safe_filename(filename: str, max_length: int = 100) -> str:
    """
    Create a safe filename by removing invalid characters.

    Args:
        filename: Original filename
        max_length: Maximum length of filename

    Returns:
        Safe filename
    """
    import re

    # Remove invalid characters
    invalid_chars = r'<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')

    # Remove control characters
    filename = re.sub(r'[\x00-\x1F\x7F]', '', filename)

    # Replace multiple spaces with single space
    filename = re.sub(r'\s+', ' ', filename).strip()

    # Limit length
    if len(filename) > max_length:
        filename = filename[:max_length]

    return filename


def print_table(data: list, headers: list = None, max_width: int = 80):
    """
    Print data as a table.

    Args:
        data: List of rows (each row is a list of values)
        headers: List of header names
        max_width: Maximum table width
    """
    if not data:
        print("(无数据)")
        return

    # Determine column widths
    if headers:
        col_widths = [len(str(h)) for h in headers]
    else:
        col_widths = [0] * len(data[0])

    for row in data:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    # Limit column widths to fit max_width
    total_width = sum(col_widths) + (len(col_widths) - 1) * 3  # 3 spaces between columns
    if total_width > max_width:
        scale = max_width / total_width
        col_widths = [int(w * scale) for w in col_widths]

    # Print headers
    if headers:
        header_row = " | ".join(f"{str(h):{w}}" for h, w in zip(headers, col_widths))
        print(header_row)
        print("-" * len(header_row))

    # Print data rows
    for row in data:
        row_str = " | ".join(f"{str(cell):{w}}" for cell, w in zip(row, col_widths))
        print(row_str)


def find_claude_dir() -> Optional[Path]:
    """
    Find Claude Code data directory.

    Returns:
        Path to Claude Code directory or None if not found
    """
    # Common locations
    common_paths = [
        Path.home() / ".claude",
        Path.home() / "Library/Application Support/claude",
        Path.home() / ".config/claude",
        Path("/usr/local/share/claude"),
        Path("/var/lib/claude"),
    ]

    for path in common_paths:
        if path.exists() and (path / "history.jsonl").exists():
            return path

    return None


def get_session_info(session_id: str, claude_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """
    Get basic information about a session.

    Args:
        session_id: Session ID
        claude_dir: Claude Code directory (optional)

    Returns:
        Session information dictionary or None if not found
    """
    from .parser import ClaudeDataParser

    parser = ClaudeDataParser(str(claude_dir) if claude_dir else None)
    conversation = parser.get_conversation(session_id)

    if not conversation:
        return None

    return conversation.to_dict()