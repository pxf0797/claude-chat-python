#!/usr/bin/env python3
"""
Simplified CLI for Claude chat manager.
只保留核心功能：查看会话列表和导出会话。
"""
import argparse
import sys
import shutil
from pathlib import Path
from datetime import datetime

from claude_chat.parser import ClaudeDataParser
from claude_chat.exporter import MarkdownExporter

# 尝试导入config模块
try:
    from claude_chat import config as cfg_module
except ImportError:
    try:
        import config as cfg_module
    except ImportError:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        import config as cfg_module


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


def _copy_to_target_folder(source_path: Path, target_folder: str, prompt: bool = True) -> bool:
    """
    将文件复制到目标文件夹。

    Args:
        source_path: 源文件路径
        target_folder: 目标文件夹路径
        prompt: 是否提示用户

    Returns:
        是否执行了复制操作
    """
    if not target_folder:
        return False

    target_dir = Path(target_folder)
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"❌ 无法创建目标文件夹 {target_dir}: {e}")
        return False

    target_path = target_dir / source_path.name

    # 检查目标文件是否已存在
    if target_path.exists():
        if prompt:
            # 提示模式：询问是否覆盖
            if sys.stdin.isatty():
                overwrite = input(f"⚠️  目标文件已存在: {target_path}\n是否覆盖? (y/n, 默认n): ").strip().lower()
                if overwrite not in ['y', 'yes', '是']:
                    print("⏭️  跳过复制")
                    return False
            else:
                # 非交互式，不覆盖
                print(f"⏭️  目标文件已存在，跳过复制: {target_path}")
                return False
        else:
            # 非提示模式：自动覆盖
            print(f"⚠️  目标文件已存在，自动覆盖: {target_path}")

    # 询问是否复制（如果提示且是交互式终端）
    if prompt and sys.stdin.isatty():
        copy_choice = input(f"是否复制到目标文件夹? (y/n, 默认y): ").strip().lower()
        if copy_choice in ['n', 'no', '否']:
            print("⏭️  跳过复制")
            return False

    # 执行复制
    try:
        shutil.copy2(source_path, target_path)  # copy2 保留元数据
        print(f"✅ 已复制到: {target_path}")
        return True
    except Exception as e:
        print(f"❌ 复制失败: {e}")
        return False


def _get_target_folder(args) -> str:
    """
    获取目标文件夹路径，优先级：命令行参数 > 配置文件 > 空字符串

    Returns:
        目标文件夹路径，如果没有设置则返回空字符串
    """
    # 首先检查命令行参数
    if hasattr(args, 'target_folder') and args.target_folder:
        return args.target_folder

    # 然后检查配置文件
    try:
        config = cfg_module.get_config()
        if config.target_folder:
            return config.target_folder
    except (AttributeError, ImportError):
        pass

    return ""


def export_conversation(parser, exporter, session_id, output_dir, include_thinking=False,
                        target_folder=None, no_prompt_copy=False):
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

    # 复制到目标文件夹（如果设置了）
    if target_folder:
        prompt = not no_prompt_copy
        _copy_to_target_folder(Path(filepath), target_folder, prompt=prompt)

    return filepath


def export_recent(parser, exporter, count, output_dir, include_thinking=False,
                  target_folder=None, no_prompt_copy=False):
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

                    # 复制到目标文件夹（如果设置了）
                    if target_folder:
                        prompt = not no_prompt_copy
                        _copy_to_target_folder(Path(filepath), target_folder, prompt=prompt)
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
    parser.add_argument('--target-folder',
                       help='目标文件夹，导出后可选择复制到此文件夹')
    parser.add_argument('--no-prompt-copy', action='store_true',
                       help='不提示直接复制到目标文件夹（如果设置了目标文件夹）')

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
            include_thinking=args.include_thinking,
            target_folder=_get_target_folder(args),
            no_prompt_copy=args.no_prompt_copy if hasattr(args, 'no_prompt_copy') else False
        )

    elif args.recent:
        # Export recent sessions
        export_recent(
            claude_parser, exporter,
            args.recent, args.output_dir,
            include_thinking=args.include_thinking,
            target_folder=_get_target_folder(args),
            no_prompt_copy=args.no_prompt_copy if hasattr(args, 'no_prompt_copy') else False
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