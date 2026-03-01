#!/usr/bin/env python3
"""
Interactive viewer for Claude chats.
"""
import sys
import cmd
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import claude_chat
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_chat.parser import ClaudeDataParser
from claude_chat.exporter import MarkdownExporter


class ClaudeChatShell(cmd.Cmd):
    """Interactive shell for Claude chat management."""

    intro = """
    ========================================
    Claude Chat Interactive Manager
    ========================================
    输入 help 或 ? 查看命令列表
    输入 exit 或 Ctrl-D 退出
    """
    prompt = "claude-chat> "

    def __init__(self, claude_dir="~/.claude"):
        super().__init__()
        self.parser = ClaudeDataParser(claude_dir)
        self.exporter = MarkdownExporter()
        self.current_sessions = []
        self.current_conversation = None

    def do_list(self, arg):
        """列出会话: list [数量]
        示例: list 10 (列出最近10个会话)
        """
        try:
            limit = int(arg) if arg else 20
        except ValueError:
            print("请输入有效的数字")
            return

        sessions = self.parser.list_sessions(limit=limit)
        self.current_sessions = sessions

        if not sessions:
            print("未找到会话记录")
            return

        print(f"\n📋 会话列表 (最近{len(sessions)}个)")
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

    def do_view(self, arg):
        """查看会话: view [序号|会话ID]
        示例: view 3 (查看列表中的第3个会话)
               view abc123 (查看指定ID的会话)
        """
        if not arg:
            print("请输入会话序号或ID")
            return

        # Try as index first
        try:
            idx = int(arg) - 1
            if 0 <= idx < len(self.current_sessions):
                session = self.current_sessions[idx]
                session_id = session.get('sessionId')
                if session_id:
                    self._view_conversation(session_id)
                else:
                    print("会话ID不存在")
            else:
                print(f"序号超出范围 (1-{len(self.current_sessions)})")
        except ValueError:
            # Not a number, treat as session ID
            self._view_conversation(arg)

    def _view_conversation(self, session_id):
        """Internal method to view conversation."""
        conversation = self.parser.get_conversation(session_id)

        if not conversation:
            print(f"未找到会话: {session_id}")
            return

        self.current_conversation = conversation

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
            print(msg.content[:500])  # Show first 500 characters
            if len(msg.content) > 500:
                print("... [内容已截断]")

        print("\n" + "=" * 80)
        print("输入 'export' 导出此会话，或 'back' 返回列表")

    def do_export(self, arg):
        """导出当前会话: export [输出目录]
        示例: export ./chats
        """
        if not self.current_conversation:
            print("请先使用 'view' 命令选择一个会话")
            return

        output_dir = arg if arg else "./claude-chats"
        self.exporter.output_dir = Path(output_dir)
        self.exporter.output_dir.mkdir(parents=True, exist_ok=True)

        try:
            filepath = self.exporter.export_conversation(
                self.current_conversation,
                include_thinking=True,
                format_type="enhanced"
            )
            print(f"✅ 已导出到: {filepath}")
        except Exception as e:
            print(f"❌ 导出失败: {e}")

    def do_search(self, arg):
        """搜索会话: search [关键词]
        示例: search python (搜索包含python的会话)
        """
        if not arg:
            print("请输入搜索关键词")
            return

        sessions = self.parser.list_sessions(limit=100)  # Search in recent 100
        results = []

        for session in sessions:
            display = str(session.get('display', '')).lower()
            if arg.lower() in display:
                results.append(session)

        if not results:
            print(f"未找到包含 '{arg}' 的会话")
            return

        print(f"\n🔍 搜索结果 ({len(results)} 个):")
        print("=" * 90)

        for i, session in enumerate(results, 1):
            dt = session.get('datetime', datetime.now())
            display = session.get('display', '无标题') or '无标题'
            session_id = session.get('sessionId', '未知ID') or '未知ID'

            print(f"{i:3d}. {dt.strftime('%Y-%m-%d %H:%M')} | {display[:60]}")
            print(f"     ID: {session_id}")

            if i < len(results):
                print("-" * 90)

        self.current_sessions = results

    def do_stats(self, arg):
        """显示统计信息: stats"""
        sessions = self.parser.list_sessions(limit=None)

        print("\n📊 统计信息")
        print("=" * 40)
        print(f"总会话数: {len(sessions)}")

        # Count by date
        date_counts = {}
        for session in sessions:
            dt = session.get('datetime', datetime.now())
            date_str = dt.strftime('%Y-%m-%d')
            date_counts[date_str] = date_counts.get(date_str, 0) + 1

        print(f"日期范围: {min(date_counts.keys())} 到 {max(date_counts.keys())}")
        print(f"活跃天数: {len(date_counts)}")

        # Most active dates
        print("\n📅 最活跃日期:")
        for date, count in sorted(date_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {date}: {count} 个会话")

        # Recent activity
        recent_count = sum(1 for s in sessions[:10])
        print(f"\n最近10个会话: {recent_count} 个")

    def do_back(self, arg):
        """返回会话列表"""
        self.current_conversation = None
        print("返回会话列表")

    def do_exit(self, arg):
        """退出程序"""
        print("\n再见！")
        return True

    def do_quit(self, arg):
        """退出程序"""
        return self.do_exit(arg)

    def do_EOF(self, arg):
        """处理Ctrl-D"""
        print()
        return self.do_exit(arg)

    def postcmd(self, stop, line):
        """After command processing."""
        if self.current_conversation:
            self.prompt = f"claude-chat [{self.current_conversation.display_title[:20]}]> "
        else:
            self.prompt = "claude-chat> "
        return stop


def main():
    parser = argparse.ArgumentParser(description="Interactive Claude chat manager")
    parser.add_argument("--claude-dir", default="~/.claude",
                       help="Claude Code data directory")

    args = parser.parse_args()

    try:
        shell = ClaudeChatShell(args.claude_dir)
        shell.cmdloop()
    except KeyboardInterrupt:
        print("\n\n程序被中断")
    except Exception as e:
        print(f"错误: {e}")


if __name__ == "__main__":
    main()