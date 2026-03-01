#!/usr/bin/env python3
"""
Basic usage examples for Claude Chat Manager.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_chat.parser import ClaudeDataParser
from claude_chat.exporter import MarkdownExporter


def example_list_sessions():
    """Example: List recent sessions."""
    print("=== Example 1: List Recent Sessions ===")

    parser = ClaudeDataParser()
    sessions = parser.list_sessions(limit=5)

    if not sessions:
        print("No sessions found. Make sure Claude Code is installed and has chat history.")
        return

    print(f"Found {len(sessions)} recent sessions:")
    for i, session in enumerate(sessions, 1):
        dt = session.get('datetime', 'N/A')
        dt_str = dt.strftime('%Y-%m-%d %H:%M') if hasattr(dt, 'strftime') else str(dt)
        display = session.get('display', 'No title') or 'No title'
        print(f"  {i}. {dt_str} - {display}")

    print()


def example_get_conversation():
    """Example: Get and display a conversation."""
    print("=== Example 2: Get Conversation ===")

    parser = ClaudeDataParser()
    sessions = parser.list_sessions(limit=1)

    if not sessions:
        print("No sessions found.")
        return

    session_id = sessions[0].get('sessionId')
    if not session_id:
        print("No session ID found.")
        return

    conversation = parser.get_conversation(session_id)
    if not conversation:
        print(f"Could not get conversation for ID: {session_id}")
        return

    print(f"Conversation: {conversation.display_title}")
    print(f"Date: {conversation.start_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"Duration: {conversation.duration_seconds:.0f} seconds")
    print(f"Messages: {len(conversation.messages)}")
    print(f"Project: {conversation.project_path}")
    print()


def example_export_conversation():
    """Example: Export a conversation to Markdown."""
    print("=== Example 3: Export Conversation ===")

    parser = ClaudeDataParser()
    sessions = parser.list_sessions(limit=1)

    if not sessions:
        print("No sessions found.")
        return

    session_id = sessions[0].get('sessionId')
    if not session_id:
        print("No session ID found.")
        return

    conversation = parser.get_conversation(session_id)
    if not conversation:
        print(f"Could not get conversation for ID: {session_id}")
        return

    exporter = MarkdownExporter(output_dir="./example-exports")
    filepath = exporter.export_conversation(
        conversation,
        include_thinking=False,
        format_type="basic"
    )

    print(f"Exported conversation to: {filepath}")
    print(f"File size: {filepath.stat().st_size} bytes")
    print()


def example_batch_export():
    """Example: Batch export recent conversations."""
    print("=== Example 4: Batch Export ===")

    parser = ClaudeDataParser()
    exporter = MarkdownExporter(output_dir="./example-exports")

    # Get recent conversations
    conversations = parser.get_recent_conversations(limit=3)

    if not conversations:
        print("No conversations found.")
        return

    print(f"Exporting {len(conversations)} conversations...")
    exported_files = exporter.export_multiple(
        conversations,
        include_thinking=False,
        format_type="enhanced"
    )

    print(f"Successfully exported {len(exported_files)} files:")
    for filepath in exported_files:
        print(f"  • {filepath.name}")
    print()


def main():
    """Run all examples."""
    print("Claude Chat Manager - Examples")
    print("=" * 50)

    try:
        example_list_sessions()
        example_get_conversation()
        example_export_conversation()
        example_batch_export()

        print("All examples completed!")
        print("\nNext steps:")
        print("1. Try the interactive mode: python scripts/interactive.py")
        print("2. Use the CLI: python -m claude_chat.cli --help")
        print("3. Export your chats: python scripts/export_chat.py --recent 5")

    except Exception as e:
        print(f"Error running examples: {e}")
        print("\nCommon issues:")
        print("1. Claude Code may not be installed")
        print("2. No chat history exists yet")
        print("3. Check the path to ~/.claude directory")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())