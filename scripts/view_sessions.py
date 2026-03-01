#!/usr/bin/env python3
"""
Quick script to view Claude chat sessions.
"""
import sys
import argparse
from pathlib import Path

# Add parent directory to path to import claude_chat
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_chat.parser import ClaudeDataParser
from claude_chat.utils import print_table


def main():
    parser = argparse.ArgumentParser(description="View Claude chat sessions")
    parser.add_argument("--claude-dir", default="~/.claude",
                       help="Claude Code data directory")
    parser.add_argument("-l", "--limit", type=int, default=20,
                       help="Number of sessions to show")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Show verbose output")
    parser.add_argument("--format", choices=["table", "list", "json"],
                       default="table", help="Output format")
    parser.add_argument("--search", help="Search in session titles")

    args = parser.parse_args()

    # Initialize parser
    claude_parser = ClaudeDataParser(args.claude_dir)

    # List sessions
    sessions = claude_parser.list_sessions(limit=args.limit)

    if args.search:
        sessions = [s for s in sessions
                   if args.search.lower() in str(s.get('display', '')).lower()]

    if not sessions:
        print("No sessions found.")
        return

    if args.format == "json":
        import json
        print(json.dumps(sessions, indent=2, default=str))
        return

    if args.format == "list":
        for i, session in enumerate(sessions, 1):
            dt = session.get('datetime', '')
            if dt:
                dt_str = dt.strftime('%Y-%m-%d %H:%M')
            else:
                dt_str = 'N/A'

            display = session.get('display', 'No title') or 'No title'
            project = session.get('project', 'Unknown') or 'Unknown'
            session_id = session.get('sessionId', 'N/A') or 'N/A'

            print(f"{i:3d}. {dt_str} | {display}")
            print(f"     ID: {session_id}")
            print(f"     Project: {project}")
            if args.verbose:
                print(f"     Data: {session.keys()}")
            print()

    else:  # table format
        headers = ["#", "Date", "Title", "Project", "Session ID"]
        table_data = []

        for i, session in enumerate(sessions, 1):
            dt = session.get('datetime', '')
            if dt:
                dt_str = dt.strftime('%Y-%m-%d %H:%M')
            else:
                dt_str = 'N/A'

            display = session.get('display', 'No title') or 'No title'
            project = session.get('project', 'Unknown') or 'Unknown'
            session_id = session.get('sessionId', 'N/A') or 'N/A'

            table_data.append([
                i,
                dt_str,
                display[:50],
                project[:30],
                session_id[:20] + "..." if len(session_id) > 20 else session_id
            ])

        print_table(table_data, headers)


if __name__ == "__main__":
    main()