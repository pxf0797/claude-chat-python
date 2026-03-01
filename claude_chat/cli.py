"""
Command-line interface for Claude chat manager.
"""
import argparse
import sys
import shutil
from pathlib import Path
from datetime import datetime

from .parser import ClaudeDataParser
from .exporter import MarkdownExporter

# 尝试导入config模块
try:
    from . import config as cfg_module
except ImportError:
    try:
        import config as cfg_module
    except ImportError:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        import config as cfg_module


def list_sessions_command(args):
    """List chat sessions command."""
    parser = ClaudeDataParser(args.claude_dir)
    sessions = parser.list_sessions(limit=args.limit)

    if not sessions:
        print("未找到任何会话记录")
        return

    print(f"\n📋 Claude Code 会话列表 (共{len(sessions)}条)")
    print("=" * 100)

    for i, session in enumerate(sessions, 1):
        dt = session.get('datetime', datetime.now())
        display = session.get('display', '无标题') or '无标题'
        project = session.get('project', '未知项目') or '未知项目'
        session_id = session.get('sessionId', '未知ID') or '未知ID'

        print(f"{i:3d}. {dt.strftime('%Y-%m-%d %H:%M')} | {display[:60]:60s} | {project[:30]:30s}")
        print(f"     ID: {session_id[:36]:36s}")
        if i < len(sessions):
            print("-" * 100)


def view_conversation_command(args):
    """View specific conversation command."""
    parser = ClaudeDataParser(args.claude_dir)
    conversation = parser.get_conversation(args.session_id)

    if not conversation:
        print(f"❌ 未找到会话: {args.session_id}")
        return

    print(f"\n💬 {conversation.display_title}")
    print(f"   时间: {conversation.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   项目: {conversation.project_path}")
    print(f"   持续时间: {conversation.duration_seconds:.0f}秒")
    print(f"   消息数量: {len(conversation.messages)}")
    print("=" * 80)

    for i, msg in enumerate(conversation.messages, 1):
        time_str = msg.timestamp.strftime("%H:%M:%S")
        role_icon = "👤" if msg.role == "user" else "🤖"
        role_name = "用户" if msg.role == "user" else "Claude"

        print(f"\n{role_icon} [{time_str}] {role_name} ({i}/{len(conversation.messages)})")
        print("-" * 40)

        if msg.role == "assistant" and msg.thinking and args.include_thinking:
            print("[思考过程]")
            print(msg.thinking)
            print("\n[回答]")

        print(msg.content)

    print("\n" + "=" * 80)


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


def export_command(args):
    """Export conversation command."""
    parser = ClaudeDataParser(args.claude_dir)
    exporter = MarkdownExporter(args.output_dir)

    if args.session_id:
        # Export single session
        conversation = parser.get_conversation(args.session_id)
        if conversation:
            filepath = exporter.export_conversation(
                conversation,
                include_thinking=args.include_thinking,
                format_type=args.format
            )
            print(f"✅ 已导出: {filepath}")

            # 复制到目标文件夹（如果设置了）
            target_folder = _get_target_folder(args)
            if target_folder:
                prompt = not args.no_prompt_copy if hasattr(args, 'no_prompt_copy') else True
                _copy_to_target_folder(Path(filepath), target_folder, prompt=prompt)
        else:
            print(f"❌ 未找到会话: {args.session_id}")

    elif args.recent:
        # Export recent N sessions
        sessions = parser.list_sessions(limit=args.recent)
        exported_count = 0

        print(f"导出最近 {args.recent} 个会话...")
        for session in sessions:
            session_id = session.get('sessionId')
            if session_id:
                conversation = parser.get_conversation(session_id)
                if conversation:
                    filepath = exporter.export_conversation(
                        conversation,
                        include_thinking=args.include_thinking,
                        format_type=args.format
                    )
                    exported_count += 1
                    print(f"  ✅ {conversation.display_title}")

                    # 复制到目标文件夹（如果设置了）
                    target_folder = _get_target_folder(args)
                    if target_folder:
                        prompt = not args.no_prompt_copy if hasattr(args, 'no_prompt_copy') else True
                        _copy_to_target_folder(Path(filepath), target_folder, prompt=prompt)

        print(f"\n✅ 已导出 {exported_count} 个会话到: {args.output_dir}")

    elif args.all:
        # Export all sessions (use with caution)
        sessions = parser.list_sessions(limit=None)
        print(f"找到 {len(sessions)} 个会话，开始导出...")

        exported_count = 0
        for session in sessions:
            session_id = session.get('sessionId')
            if session_id:
                conversation = parser.get_conversation(session_id)
                if conversation:
                    try:
                        filepath = exporter.export_conversation(
                            conversation,
                            include_thinking=args.include_thinking,
                            format_type=args.format
                        )
                        exported_count += 1
                        print(f"  ✅ ({exported_count}/{len(sessions)}) {conversation.display_title}")

                        # 复制到目标文件夹（如果设置了）
                        target_folder = _get_target_folder(args)
                        if target_folder:
                            prompt = not args.no_prompt_copy if hasattr(args, 'no_prompt_copy') else True
                            _copy_to_target_folder(Path(filepath), target_folder, prompt=prompt)
                    except Exception as e:
                        print(f"  ❌ 导出失败 {session_id}: {e}")

        print(f"\n✅ 批量导出完成，共导出 {exported_count} 个会话")
        print(f"导出目录: {args.output_dir}")


def stats_command(args):
    """Show statistics command."""
    parser = ClaudeDataParser(args.claude_dir)
    sessions = parser.list_sessions(limit=None)

    print("=== Claude 聊天记录统计 ===")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    print("📈 原始数据统计:")
    print(f"总会话数: {len(sessions)}")

    # Count files in projects directory
    if parser.projects_dir.exists():
        jsonl_files = list(parser.projects_dir.rglob("*.jsonl"))
        print(f"JSONL文件数: {len(jsonl_files)}")

        # Calculate total size
        total_size = sum(f.stat().st_size for f in jsonl_files if f.exists())
        print(f"总大小: {total_size / 1024 / 1024:.2f} MB")

    print(f"项目目录数: {len(list(parser.projects_dir.iterdir())) if parser.projects_dir.exists() else 0}\n")

    print("📊 最近活跃:")
    recent_sessions = sessions[:5]
    for i, session in enumerate(recent_sessions, 1):
        dt = session.get('datetime', datetime.now())
        display = session.get('display', '无标题') or '无标题'
        print(f"  {i}. {dt.strftime('%Y-%m-%d %H:%M')} - {display[:50]}")

    # Date distribution
    print("\n📅 日期分布:")
    date_counts = {}
    for session in sessions:
        dt = session.get('datetime', datetime.now())
        date_str = dt.strftime('%Y-%m-%d')
        date_counts[date_str] = date_counts.get(date_str, 0) + 1

    for date, count in sorted(date_counts.items(), reverse=True)[:10]:
        print(f"  {date}: {count} 个会话")

    # Check export directory
    if args.output_dir:
        export_dir = Path(args.output_dir)
        if export_dir.exists():
            md_files = list(export_dir.glob("*.md"))
            print(f"\n📤 导出统计:")
            print(f"导出文件数: {len(md_files)}")

            if md_files:
                total_size = sum(f.stat().st_size for f in md_files if f.exists())
                print(f"导出大小: {total_size / 1024:.2f} KB")

    print("\n💡 建议:")
    print("1. 定期导出重要对话到笔记工具")
    print("2. 使用 'claude-chat export --recent 10' 导出最近对话")
    print("3. 查看 'claude-chat view --id <session_id>' 查看具体对话")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Claude Code 聊天记录管理工具 (Python版)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s list -l 10              # 列出最近10个会话
  %(prog)s view --id <session_id>  # 查看指定会话
  %(prog)s export --recent 5       # 导出最近5个会话
  %(prog)s export --id <session_id> # 导出指定会话
  %(prog)s stats                   # 显示统计信息
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='命令')

    # list command
    list_parser = subparsers.add_parser('list', help='列出会话')
    list_parser.add_argument('--claude-dir', default='~/.claude',
                           help='Claude Code 数据目录 (默认: ~/.claude)')
    list_parser.add_argument('-l', '--limit', type=int, default=20,
                           help='显示数量限制 (默认: 20)')

    # view command
    view_parser = subparsers.add_parser('view', help='查看会话详情')
    view_parser.add_argument('--claude-dir', default='~/.claude',
                           help='Claude Code 数据目录')
    view_parser.add_argument('--id', '--session-id', dest='session_id', required=True,
                           help='会话ID')
    view_parser.add_argument('--include-thinking', action='store_true',
                           help='包含助手的思考过程')

    # export command
    export_parser = subparsers.add_parser('export', help='导出会话')
    export_parser.add_argument('--claude-dir', default='~/.claude',
                             help='Claude Code 数据目录')
    export_parser.add_argument('-o', '--output-dir', default='./claude-chats',
                             help='输出目录 (默认: ./claude-chats)')
    export_parser.add_argument('--include-thinking', action='store_true',
                             help='包含助手的思考过程')
    export_parser.add_argument('--format', choices=['basic', 'enhanced'],
                             default='enhanced', help='导出格式 (默认: enhanced)')
    export_parser.add_argument('--target-folder',
                             help='目标文件夹，导出后可选择复制到此文件夹')
    export_parser.add_argument('--no-prompt-copy', action='store_true',
                             help='不提示直接复制到目标文件夹（如果设置了目标文件夹）')

    # Export mode options (mutually exclusive)
    export_group = export_parser.add_mutually_exclusive_group(required=True)
    export_group.add_argument('--id', '--session-id', dest='session_id',
                            help='导出指定会话ID')
    export_group.add_argument('-r', '--recent', type=int,
                            help='导出最近N个会话')
    export_group.add_argument('--all', action='store_true',
                            help='导出所有会话（谨慎使用）')

    # stats command
    stats_parser = subparsers.add_parser('stats', help='显示统计信息')
    stats_parser.add_argument('--claude-dir', default='~/.claude',
                            help='Claude Code 数据目录')
    stats_parser.add_argument('-o', '--output-dir', default='./claude-chats',
                            help='导出目录 (用于统计导出文件)')

    args = parser.parse_args()

    if args.command == 'list':
        list_sessions_command(args)
    elif args.command == 'view':
        view_conversation_command(args)
    elif args.command == 'export':
        export_command(args)
    elif args.command == 'stats':
        stats_command(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()