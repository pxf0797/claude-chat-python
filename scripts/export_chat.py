#!/usr/bin/env python3
"""
Quick script to export Claude chats.
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import claude_chat
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_chat.parser import ClaudeDataParser
from claude_chat.exporter import MarkdownExporter


def main():
    parser = argparse.ArgumentParser(description="Export Claude chats to Markdown")
    parser.add_argument("--claude-dir", default="~/.claude",
                       help="Claude Code data directory")
    parser.add_argument("-o", "--output-dir", default="./claude-chats",
                       help="Output directory")
    parser.add_argument("--include-thinking", action="store_true",
                       help="Include assistant thinking process")
    parser.add_argument("--format", choices=["basic", "enhanced"],
                       default="enhanced", help="Export format")

    # Export options
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--session-id", help="Export specific session")
    group.add_argument("--recent", type=int, help="Export recent N sessions")
    group.add_argument("--all", action="store_true", help="Export all sessions")
    group.add_argument("--date", help="Export sessions from specific date (YYYY-MM-DD)")
    group.add_argument("--date-range", nargs=2, metavar=("START", "END"),
                       help="Export sessions within date range")

    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be exported without actually exporting")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")

    args = parser.parse_args()

    # Initialize parser and exporter
    claude_parser = ClaudeDataParser(args.claude_dir)
    exporter = MarkdownExporter(args.output_dir)

    sessions_to_export = []

    if args.session_id:
        # Export specific session
        conversation = claude_parser.get_conversation(args.session_id)
        if conversation:
            sessions_to_export = [conversation]
        else:
            print(f"Error: Session not found: {args.session_id}")
            sys.exit(1)

    elif args.recent:
        # Export recent N sessions
        sessions = claude_parser.list_sessions(limit=args.recent)
        for session in sessions:
            session_id = session.get('sessionId')
            if session_id:
                conversation = claude_parser.get_conversation(session_id)
                if conversation:
                    sessions_to_export.append(conversation)

    elif args.all:
        # Export all sessions
        sessions = claude_parser.list_sessions(limit=None)
        for session in sessions:
            session_id = session.get('sessionId')
            if session_id:
                conversation = claude_parser.get_conversation(session_id)
                if conversation:
                    sessions_to_export.append(conversation)

    elif args.date:
        # Export sessions from specific date
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d")
            sessions = claude_parser.list_sessions(limit=None)
            for session in sessions:
                dt = session.get('datetime')
                if dt and dt.date() == target_date.date():
                    session_id = session.get('sessionId')
                    if session_id:
                        conversation = claude_parser.get_conversation(session_id)
                        if conversation:
                            sessions_to_export.append(conversation)
        except ValueError:
            print(f"Error: Invalid date format: {args.date}. Use YYYY-MM-DD.")
            sys.exit(1)

    elif args.date_range:
        # Export sessions within date range
        try:
            start_date = datetime.strptime(args.date_range[0], "%Y-%m-%d")
            end_date = datetime.strptime(args.date_range[1], "%Y-%m-%d")
            sessions = claude_parser.list_sessions(limit=None)
            for session in sessions:
                dt = session.get('datetime')
                if dt and start_date.date() <= dt.date() <= end_date.date():
                    session_id = session.get('sessionId')
                    if session_id:
                        conversation = claude_parser.get_conversation(session_id)
                        if conversation:
                            sessions_to_export.append(conversation)
        except ValueError:
            print(f"Error: Invalid date format. Use YYYY-MM-DD.")
            sys.exit(1)

    # Show what would be exported
    if args.dry_run:
        print("Dry run - would export the following sessions:")
        for conv in sessions_to_export:
            print(f"  • {conv.display_title} ({conv.start_time.strftime('%Y-%m-%d')})")
        print(f"\nTotal: {len(sessions_to_export)} sessions")
        return

    # Export sessions
    if not sessions_to_export:
        print("No sessions to export.")
        return

    print(f"Exporting {len(sessions_to_export)} sessions...")
    print(f"Output directory: {args.output_dir}")
    print(f"Format: {args.format}")
    print(f"Include thinking: {args.include-thinking}")
    print()

    exported_files = exporter.export_multiple(
        sessions_to_export,
        include_thinking=args.include_thinking,
        format_type=args.format
    )

    print(f"\n✅ Export complete!")
    print(f"Exported {len(exported_files)} files to: {args.output_dir}")

    if args.verbose and exported_files:
        print("\nExported files:")
        for filepath in exported_files[:10]:  # Show first 10
            print(f"  • {filepath.name}")
        if len(exported_files) > 10:
            print(f"  ... and {len(exported_files) - 10} more")


if __name__ == "__main__":
    main()