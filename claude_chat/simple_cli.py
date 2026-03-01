#!/usr/bin/env python3
"""
Simplified CLI for Claude chat manager.
只保留核心功能：查看会话列表和导出会话。
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime

from claude_chat.parser import ClaudeDataParser
from claude_chat.exporter import MarkdownExporter


def list_sessions(parser, limit=20):
    """List recent chat sessions."""
    sessions = parser.list_sessions(limit=limit)

    if not sessions:
        print("未找到任何会话记录")
        return []

    print(f"\n📋 Claude Code 会话列表 (最近{len(sessions)}个)")
    print("=" * 90)

    for i, session in enumerate(sessions, 1):
        dt = session.get('datetime', datetime.now())
        display = session.get('display', '无标题') or '无标题'
        project = session.get('project', '未知项目') or '未知项目'
        session_id = session.get('sessionId', '未知ID') or '未知ID'

        print(f"{i:3d}. {dt.strftime('%Y-%m-%d %H:%M')} | {display[:50]:50s} | {project[:20]:20s}")
        print(f"     ID: {session_id}")

        if i < len(sessions):
            print("-" * 90)

    return sessions


def view_conversation(parser, session_id, include_thinking=False):
    """View specific conversation."""
    conversation = parser.get_conversation(session_id)

    if not conversation:
        print(f"❌ 未找到会话: {session_id}")
        return None

    print(f"\n💬 {conversation.display_title}")
    print(f"   时间: {conversation.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   项目: {conversation.project_path}")
    print(f"   持续时间: {conversation.duration_seconds:.0f}秒")
    print(f"   消息数量: {len(conversation.messages)}")
    print("=" * 80)

    # Show first 3 messages as preview
    for i, msg in enumerate(conversation.messages[:3], 1):
        time_str = msg.timestamp.strftime("%H:%M:%S")
        role_icon = "👤" if msg.role == "user" else "🤖"
        role_name = "用户" if msg.role == "user" else "Claude"

        print(f"\n{role_icon} [{time_str}] {role_name} ({i}/{len(conversation.messages)})")
        print("-" * 40)
        print(msg.content[:300])  # Show first 300 characters
        if len(msg.content) > 300:
            print("... [内容已截断，使用完整查看模式查看全部]")

    if len(conversation.messages) > 3:
        print(f"\n... 还有 {len(conversation.messages) - 3} 条消息未显示")
        print("使用 --full 参数查看完整对话")

    print("\n" + "=" * 80)
    return conversation


def export_conversation(parser, exporter, session_id, output_dir, include_thinking=False):
    """Export single conversation."""
    conversation = parser.get_conversation(session_id)
    if not conversation:
        print(f"❌ 未找到会话: {session_id}")
        return None

    filepath = exporter.export_conversation(
        conversation,
        include_thinking=include_thinking,
        format_type="enhanced"  # Always use enhanced format for simplicity
    )
    print(f"✅ 已导出: {filepath}")
    return filepath


def export_recent(parser, exporter, count, output_dir, include_thinking=False):
    """Export recent conversations."""
    sessions = parser.list_sessions(limit=count)
    exported_count = 0

    print(f"导出最近 {count} 个会话...")
    for session in sessions:
        session_id = session.get('sessionId')
        if session_id:
            conversation = parser.get_conversation(session_id)
            if conversation:
                try:
                    filepath = exporter.export_conversation(
                        conversation,
                        include_thinking=include_thinking,
                        format_type="enhanced"
                    )
                    exported_count += 1
                    print(f"  ✅ {conversation.display_title}")
                except Exception as e:
                    print(f"  ❌ 导出失败 {session_id}: {e}")

    print(f"\n✅ 已导出 {exported_count} 个会话到: {output_dir}")
    return exported_count


def main():
    """Simplified main CLI."""
    parser = argparse.ArgumentParser(
        description="Claude Code 聊天记录管理工具 (简化版)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s                     # 列出最近20个会话
  %(prog)s -l 10               # 列出最近10个会话
  %(prog)s -e <session_id>     # 导出指定会话
  %(prog)s -r 5                # 导出最近5个会话
  %(prog)s -v <session_id>     # 查看会话内容
  %(prog)s -o ./my-chats       # 指定输出目录

提示: 会话ID可以从列表中获得。
        """
    )

    # Basic options
    parser.add_argument('--claude-dir', default='~/.claude',
                       help='Claude Code 数据目录 (默认: ~/.claude)')
    parser.add_argument('-o', '--output-dir', default='./claude-chats',
                       help='输出目录 (默认: ./claude-chats)')
    parser.add_argument('-l', '--limit', type=int, default=20,
                       help='显示/导出数量限制 (默认: 20)')

    # Action options (mutually exclusive)
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument('-e', '--export',
                            help='导出指定会话ID')
    action_group.add_argument('-r', '--recent', type=int,
                            help='导出最近N个会话')
    action_group.add_argument('-v', '--view',
                            help='查看指定会话ID的内容')

    # Additional options
    parser.add_argument('--include-thinking', action='store_true',
                       help='包含助手的思考过程 (仅导出时有效)')
    parser.add_argument('--full', action='store_true',
                       help='查看完整对话内容 (与-v一起使用)')

    args = parser.parse_args()

    # Initialize parser and exporter
    claude_parser = ClaudeDataParser(args.claude_dir)
    exporter = MarkdownExporter(args.output_dir)

    # Ensure output directory exists
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    # Determine action
    if args.export:
        # Export specific session
        export_conversation(
            claude_parser, exporter,
            args.export, args.output_dir,
            include_thinking=args.include_thinking
        )

    elif args.recent:
        # Export recent sessions
        export_recent(
            claude_parser, exporter,
            args.recent, args.output_dir,
            include_thinking=args.include_thinking
        )

    elif args.view:
        # View conversation
        if args.full:
            # Full view (using original view function)
            from claude_chat.cli import view_conversation_command
            # Create a simple args object
            class Args:
                pass
            view_args = Args()
            view_args.claude_dir = args.claude_dir
            view_args.session_id = args.view
            view_args.include_thinking = args.include_thinking
            view_conversation_command(view_args)
        else:
            # Preview view
            view_conversation(
                claude_parser, args.view,
                include_thinking=args.include_thinking
            )

    else:
        # Default: list sessions
        list_sessions(claude_parser, limit=args.limit)

        print("\n💡 提示:")
        print("  使用 -e <ID> 导出指定会话")
        print("  使用 -r 5 导出最近5个会话")
        print("  使用 -v <ID> 查看会话内容")


if __name__ == "__main__":
    main()