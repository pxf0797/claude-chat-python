#!/usr/bin/env python3
"""
Interactive menu system for Claude chat manager.
运行脚本后自动显示会话列表，提供菜单选择进行操作。
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any

from .parser import ClaudeDataParser
from .exporter import MarkdownExporter
from .core import Conversation


class InteractiveMenu:
    """交互式菜单系统"""

    def __init__(self, claude_dir: str = "~/.claude"):
        """
        初始化交互式菜单

        Args:
            claude_dir: Claude数据目录路径
        """
        self.parser = ClaudeDataParser(claude_dir)
        self.default_limit = 10  # 默认显示数量
        self.include_thinking = False  # 默认不包含思考过程
        self.output_dir = "./claude-chats"  # 默认输出目录

        # 初始化导出器
        self.exporter = MarkdownExporter(self.output_dir)
        self.current_sessions: List[Dict[str, Any]] = []
        self.current_conversation: Optional[Conversation] = None

    def run(self):
        """运行交互式菜单系统"""
        self._print_welcome()
        self._main_loop()

    def _print_welcome(self):
        """显示欢迎信息"""
        print("\n" + "="*50)
        print("🎯 Claude Chat 交互管理器")
        print("="*50)
        print("运行后自动显示最近会话，通过数字菜单选择操作")
        print("="*50 + "\n")

    def _main_loop(self):
        """主循环"""
        while True:
            # 显示会话列表
            self._list_sessions_with_menu()

            # 显示操作菜单
            choice = self._show_menu()

            # 处理选择
            if not self._handle_menu_choice(choice):
                break

    def _list_sessions_with_menu(self, limit: Optional[int] = None):
        """
        显示会话列表和菜单

        Args:
            limit: 显示数量限制，None使用默认值
        """
        if limit is None:
            limit = self.default_limit

        # 获取会话列表
        self.current_sessions = self.parser.list_sessions(limit=limit)

        if not self.current_sessions:
            print("❌ 未找到任何会话记录")
            return

        # 显示会话列表
        print(f"\n📋 最近会话 (显示{len(self.current_sessions)}个)")
        print("-" * 90)

        for i, session in enumerate(self.current_sessions, 1):
            dt = session.get('datetime', datetime.now())
            display = session.get('display', '无标题') or '无标题'
            project = session.get('project', '未知项目') or '未知项目'
            session_id = session.get('sessionId', '未知ID') or '未知ID'

            # 显示序号、时间、标题、项目
            print(f"{i:3d}. {dt.strftime('%Y-%m-%d %H:%M')} | {display[:50]:50s}")
            print(f"     项目: {project[:40]:40s}")
            print(f"     ID: {session_id[:36]:36s}")

            if i < len(self.current_sessions):
                print("-" * 90)

        print("-" * 90)

    def _show_menu(self) -> str:
        """
        显示主菜单并获取用户选择

        Returns:
            用户选择的菜单编号
        """
        print("\n📌 请选择操作:")
        print("  [1] 查看会话详情")
        print("  [2] 导出单个会话")
        print("  [3] 导出多个会话")
        print("  [4] 搜索会话")
        print("  [5] 显示更多会话")
        print("  [6] 查看统计信息")
        print("  [7] 配置选项")
        print("  [0] 退出")
        print()

        while True:
            try:
                choice = input("请输入选项编号 [0-7]: ").strip()
                if choice in ['0', '1', '2', '3', '4', '5', '6', '7']:
                    return choice
                else:
                    print("❌ 无效选项，请输入 0-7 之间的数字")
            except (KeyboardInterrupt, EOFError):
                print("\n")
                return '0'

    def _handle_menu_choice(self, choice: str) -> bool:
        """
        处理菜单选择

        Args:
            choice: 用户选择

        Returns:
            True表示继续循环，False表示退出
        """
        if choice == '0':
            print("\n👋 再见！")
            return False

        elif choice == '1':
            self._view_session()
        elif choice == '2':
            self._export_single()
        elif choice == '3':
            self._export_multiple()
        elif choice == '4':
            self._search_sessions()
        elif choice == '5':
            self._show_more_sessions()
        elif choice == '6':
            self._show_stats()
        elif choice == '7':
            self._show_settings()

        # 操作完成后等待用户按回车继续
        if choice != '0':
            input("\n↵ 按回车键返回主菜单...")

        return True

    def _view_session(self):
        """查看会话详情"""
        if not self.current_sessions:
            print("❌ 当前没有会话列表，请先显示会话")
            return

        session_idx = self._get_session_index("查看")
        if session_idx is None:
            return

        session = self.current_sessions[session_idx]
        session_id = session.get('sessionId')

        if not session_id:
            print("❌ 会话ID不存在")
            return

        conversation = self.parser.get_conversation(session_id)
        if not conversation:
            print(f"❌ 无法加载会话: {session_id}")
            return

        self.current_conversation = conversation

        # 显示会话详情
        print(f"\n💬 {conversation.display_title}")
        print(f"   时间: {conversation.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   项目: {conversation.project_path}")
        print(f"   持续时间: {conversation.duration_seconds:.0f}秒")
        print(f"   消息数量: {len(conversation.messages)} (👤{len([m for m in conversation.messages if m.role == 'user'])} | 🤖{len([m for m in conversation.messages if m.role == 'assistant'])})")
        print("=" * 80)

        # 显示完整对话内容
        for i, msg in enumerate(conversation.messages, 1):
            time_str = msg.timestamp.strftime("%H:%M:%S")
            role_icon = "👤" if msg.role == "user" else "🤖"
            role_name = "用户" if msg.role == "user" else "Claude"

            print(f"\n{role_icon} {role_name} ({i}) [{time_str}]")
            print("-" * 40)

            if msg.role == "assistant" and msg.thinking and self.include_thinking:
                print("[思考过程]")
                print(msg.thinking[:300])
                if len(msg.thinking) > 300:
                    print("... [思考内容已截断]")
                print("\n[回答]")

            print(msg.content[:500])  # 显示前500字符
            if len(msg.content) > 500:
                print("... [内容已截断，导出后查看完整内容]")

        print("\n" + "=" * 80)

        # 提供额外选项
        export_choice = input("\n输入 'e' 导出此会话，或直接按回车返回: ").strip().lower()
        if export_choice == 'e':
            self._export_conversation(conversation)

    def _export_single(self):
        """导出单个会话"""
        if not self.current_sessions:
            print("❌ 当前没有会话列表，请先显示会话")
            return

        session_idx = self._get_session_index("导出")
        if session_idx is None:
            return

        session = self.current_sessions[session_idx]
        session_id = session.get('sessionId')

        if not session_id:
            print("❌ 会话ID不存在")
            return

        conversation = self.parser.get_conversation(session_id)
        if not conversation:
            print(f"❌ 无法加载会话: {session_id}")
            return

        self._export_conversation(conversation)

    def _export_multiple(self):
        """导出多个会话"""
        if not self.current_sessions:
            print("❌ 当前没有会话列表，请先显示会话")
            return

        # 获取导出数量
        try:
            count = input(f"请输入要导出的会话数量 (1-{len(self.current_sessions)}): ").strip()
            count = int(count)
            if count < 1 or count > len(self.current_sessions):
                print(f"❌ 请输入 1-{len(self.current_sessions)} 之间的数字")
                return
        except ValueError:
            print("❌ 请输入有效的数字")
            return

        # 确认包含思考过程
        include_thinking = self._confirm_include_thinking()

        print(f"\n📤 开始导出 {count} 个会话...")
        exported_count = 0

        for i in range(count):
            session = self.current_sessions[i]
            session_id = session.get('sessionId')

            if session_id:
                conversation = self.parser.get_conversation(session_id)
                if conversation:
                    try:
                        filepath = self.exporter.export_conversation(
                            conversation,
                            include_thinking=include_thinking,
                            format_type="enhanced"
                        )
                        exported_count += 1
                        print(f"  ✅ ({exported_count}/{count}) {conversation.display_title}")
                    except Exception as e:
                        print(f"  ❌ 导出失败 {session_id}: {e}")

        print(f"\n✅ 批量导出完成，共导出 {exported_count} 个会话")
        print(f"导出目录: {self.exporter.output_dir}")

    def _search_sessions(self):
        """搜索会话"""
        keyword = input("请输入搜索关键词: ").strip()
        if not keyword:
            print("❌ 搜索关键词不能为空")
            return

        print(f"\n🔍 正在搜索包含 '{keyword}' 的会话...")

        # 搜索最近100个会话
        all_sessions = self.parser.list_sessions(limit=100)
        results = []

        for session in all_sessions:
            display = str(session.get('display', '')).lower()
            project = str(session.get('project', '')).lower()
            if keyword.lower() in display or keyword.lower() in project:
                results.append(session)

        if not results:
            print(f"❌ 未找到包含 '{keyword}' 的会话")
            return

        # 更新当前会话列表为搜索结果
        self.current_sessions = results
        print(f"✅ 找到 {len(results)} 个相关会话")

        # 显示搜索结果
        self._list_sessions_with_menu(len(results))

    def _show_more_sessions(self):
        """显示更多会话"""
        try:
            new_limit = input(f"请输入要显示的会话数量 (当前: {self.default_limit}): ").strip()
            if new_limit:
                new_limit = int(new_limit)
                if new_limit > 0:
                    self.default_limit = new_limit
                    print(f"✅ 已更新显示数量为 {new_limit}")
                else:
                    print("❌ 显示数量必须大于0")
        except ValueError:
            print("❌ 请输入有效的数字")

    def _show_stats(self):
        """显示统计信息"""
        all_sessions = self.parser.list_sessions(limit=None)

        if not all_sessions:
            print("❌ 未找到任何会话记录")
            return

        print("\n📊 统计信息")
        print("=" * 40)
        print(f"总会话数: {len(all_sessions)}")

        # 日期分布
        date_counts = {}
        for session in all_sessions:
            dt = session.get('datetime', datetime.now())
            date_str = dt.strftime('%Y-%m-%d')
            date_counts[date_str] = date_counts.get(date_str, 0) + 1

        if date_counts:
            print(f"日期范围: {min(date_counts.keys())} 到 {max(date_counts.keys())}")
            print(f"活跃天数: {len(date_counts)}")

            # 最活跃日期
            print("\n📅 最活跃日期:")
            for date, count in sorted(date_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {date}: {count} 个会话")

        # 项目分布
        project_counts = {}
        for session in all_sessions:
            project = session.get('project', '未知')
            project_counts[project] = project_counts.get(project, 0) + 1

        if project_counts:
            print("\n📁 项目分布:")
            for project, count in sorted(project_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {project}: {count} 个会话")

    def _show_settings(self):
        """显示配置选项"""
        print("\n⚙️ 配置选项")
        print("=" * 40)
        print(f"1. 默认显示数量: {self.default_limit}")
        print(f"2. 包含思考过程: {'是' if self.include_thinking else '否'}")
        print(f"3. 导出目录: {self.output_dir}")
        print()

        choice = input("请选择要修改的配置 (1-3) 或按回车返回: ").strip()

        if choice == '1':
            try:
                new_limit = input(f"新的显示数量 (当前: {self.default_limit}): ").strip()
                if new_limit:
                    new_limit = int(new_limit)
                    if new_limit > 0:
                        self.default_limit = new_limit
                        print(f"✅ 已更新显示数量为 {new_limit}")
                    else:
                        print("❌ 显示数量必须大于0")
            except ValueError:
                print("❌ 请输入有效的数字")

        elif choice == '2':
            include = input("是否包含思考过程? (y/n): ").strip().lower()
            if include in ['y', 'yes', '是']:
                self.include_thinking = True
                print("✅ 已启用包含思考过程")
            elif include in ['n', 'no', '否']:
                self.include_thinking = False
                print("✅ 已禁用包含思考过程")
            else:
                print("❌ 无效输入")

        elif choice == '3':
            new_dir = input(f"新的导出目录 (当前: {self.output_dir}): ").strip()
            if new_dir:
                self.output_dir = new_dir
                self.exporter.output_dir = Path(new_dir)
                # 确保目录存在
                self.exporter.output_dir.mkdir(parents=True, exist_ok=True)
                print(f"✅ 已更新导出目录为 {new_dir}")

    def _get_session_index(self, action: str) -> Optional[int]:
        """
        获取用户选择的会话序号

        Args:
            action: 操作名称（用于提示）

        Returns:
            会话序号（0-based），None表示取消
        """
        if not self.current_sessions:
            return None

        try:
            idx_str = input(f"请输入要{action}的会话编号 (1-{len(self.current_sessions)}): ").strip()
            if not idx_str:
                return None

            idx = int(idx_str) - 1
            if 0 <= idx < len(self.current_sessions):
                return idx
            else:
                print(f"❌ 编号必须在 1-{len(self.current_sessions)} 范围内")
                return None
        except ValueError:
            print("❌ 请输入有效的数字")
            return None

    def _confirm_include_thinking(self) -> bool:
        """确认是否包含思考过程"""
        include = input("是否包含思考过程? (y/n, 默认n): ").strip().lower()
        return include in ['y', 'yes', '是']

    def _export_conversation(self, conversation: Conversation):
        """导出会话"""
        include_thinking = self._confirm_include_thinking()

        try:
            filepath = self.exporter.export_conversation(
                conversation,
                include_thinking=include_thinking,
                format_type="enhanced"
            )
            print(f"\n✅ 已导出: {filepath}")
        except Exception as e:
            print(f"❌ 导出失败: {e}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Claude Chat 交互式菜单系统",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--claude-dir', default='~/.claude',
                       help='Claude Code 数据目录 (默认: ~/.claude)')

    args = parser.parse_args()

    try:
        menu = InteractiveMenu(args.claude_dir)
        menu.run()
    except KeyboardInterrupt:
        print("\n\n👋 程序被中断，再见！")
    except Exception as e:
        print(f"❌ 程序错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()