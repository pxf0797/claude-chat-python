#!/usr/bin/env python3
"""
Interactive menu system for Claude chat manager.
运行脚本后自动显示会话列表，提供菜单选择进行操作。
"""

import sys
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any

from .parser import ClaudeDataParser
from .exporter import MarkdownExporter
from .core import Conversation

# 尝试导入config模块（可能在不同位置）
try:
    # 首先尝试从当前包导入
    from . import config as cfg_module
except ImportError:
    try:
        # 然后尝试从父目录导入
        import config as cfg_module
    except ImportError:
        # 最后尝试通过添加路径导入
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        import config as cfg_module


# 颜色常量 (ANSI escape codes)
class Colors:
    """终端颜色常量"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"

    # 背景色
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"

    # 样式组合
    ERROR = RED + BOLD
    SUCCESS = GREEN + BOLD
    WARNING = YELLOW + BOLD
    INFO = CYAN
    TITLE = BLUE + BOLD
    HIGHLIGHT = MAGENTA + BOLD


class InteractiveMenu:
    """交互式菜单系统"""

    def __init__(self, claude_dir: str = "~/.claude"):
        """
        初始化交互式菜单

        Args:
            claude_dir: Claude数据目录路径
        """
        self.parser = ClaudeDataParser(claude_dir)

        # 使用全局配置
        self.config = cfg_module.get_config()

        # 覆盖配置中的claude_dir（如果提供了参数）
        if claude_dir != "~/.claude":
            self.config.claude_dir = claude_dir

        # 从配置中读取设置
        self.default_limit = self.config.limit
        self.include_thinking = self.config.include_thinking
        self.output_dir = self.config.output_dir
        self.target_folder = self.config.target_folder

        # 初始化导出器
        self.exporter = MarkdownExporter(self.output_dir)
        self.current_sessions: List[Dict[str, Any]] = []
        self.current_conversation: Optional[Conversation] = None
        self.skip_next_display = False  # 是否跳过下一次显示

    def run(self):
        """运行交互式菜单系统"""
        self._print_welcome()
        self._main_loop()

    def _print_welcome(self):
        """显示欢迎信息"""
        print("\n" + "="*50)
        print("🎯 Claude Chat 交互管理器 (快捷命令模式)")
        print("="*50)
        print("运行后自动显示最近会话，使用快捷命令进行操作")
        print("输入 '?' 查看可用命令，'m' 显示完整菜单")
        print("="*50 + "\n")

    def _main_loop(self):
        """主循环（快捷命令模式）"""
        while True:
            # 显示紧凑会话列表（除非跳过）
            if not self.skip_next_display:
                self._show_compact_list()
            else:
                self.skip_next_display = False

            # 获取并执行快捷命令
            command = self._prompt_quick_command()
            if not self._execute_quick_command(command):
                break

    def _show_compact_list(self, limit: Optional[int] = None, use_existing: bool = False):
        """
        显示紧凑会话列表（单行格式）

        Args:
            limit: 显示数量限制，None使用默认值
            use_existing: 是否使用现有的self.current_sessions，True表示不重新获取
        """
        if limit is None:
            limit = self.default_limit

        # 获取会话列表
        if use_existing:
            # 使用现有列表，即使为空也不重新获取
            pass
        else:
            # 总是重新获取数据，确保使用最新时刻
            self.current_sessions = self.parser.list_sessions(limit=limit)

        if not self.current_sessions:
            print(f"{Colors.ERROR}❌ 未找到任何会话记录{Colors.RESET}")
            return

        # 应用显示限制
        display_sessions = self.current_sessions[:limit]

        # 显示紧凑会话列表
        print(f"\n{Colors.TITLE}📋 最近会话 (显示{len(display_sessions)}个){Colors.RESET}")
        print(f"{Colors.GRAY}{'-' * 80}{Colors.RESET}")

        for i, session in enumerate(display_sessions, 1):
            dt = session.get('datetime', datetime.now())
            display = session.get('display', '无标题') or '无标题'
            project = session.get('project', '未知项目') or '未知项目'
            session_id = session.get('sessionId', '未知ID') or '未知ID'

            # 简化项目路径（将用户目录替换为~）
            if project.startswith('/Users/'):
                parts = project.split('/')
                if len(parts) >= 3:
                    project = f"~/{'/'.join(parts[3:])}" if len(parts) > 3 else "~"

            # 紧凑单行显示：序号 日期时间 标题 项目 ID前8位
            try:
                date_str = dt.strftime('%Y-%m-%d')
                time_str = dt.strftime('%H:%M')
                datetime_str = f"{date_str} {time_str}"
            except (AttributeError, TypeError):
                datetime_str = "未知日期"
            display_short = display[:29] + "..." if len(display) > 29 else display
            project_short = project[:15] + "..." if len(project) > 15 else project
            id_short = session_id[:8] + "..." if len(session_id) > 8 else session_id

            # 彩色显示
            index_color = Colors.BLUE + Colors.BOLD
            datetime_color = Colors.CYAN
            title_color = Colors.WHITE
            project_color = Colors.GRAY
            id_color = Colors.YELLOW
            separator_color = Colors.GRAY

            print(f"{index_color}[{i:2d}]{separator_color} {datetime_color}{datetime_str:16s}{separator_color} | {title_color}{display_short:32s}{separator_color} | {project_color}{project_short:18s}{separator_color} | {id_color}{id_short}{Colors.RESET}")

        print(f"{Colors.GRAY}{'-' * 80}{Colors.RESET}")

    def _prompt_quick_command(self) -> str:
        """
        提示输入快捷命令

        Returns:
            用户输入的命令字符串
        """
        print(f"\n{Colors.INFO}快捷命令: {Colors.HIGHLIGHT}v1{Colors.INFO}(查看) {Colors.HIGHLIGHT}e2{Colors.INFO}(导出) {Colors.HIGHLIGHT}s关键词{Colors.INFO}(搜索) {Colors.HIGHLIGHT}d日期{Colors.INFO}(日期筛选) {Colors.HIGHLIGHT}m{Colors.INFO}(菜单) {Colors.HIGHLIGHT}q{Colors.INFO}(退出)")
        print(f"{Colors.INFO}示例: {Colors.HIGHLIGHT}v1 {Colors.INFO}查看第1个, {Colors.HIGHLIGHT}e3 {Colors.INFO}导出第3个, {Colors.HIGHLIGHT}e1-3 {Colors.INFO}导出1-3个, {Colors.HIGHLIGHT}s python {Colors.INFO}搜索, {Colors.HIGHLIGHT}d 2026-02-28 {Colors.INFO}筛选日期{Colors.RESET}")

        while True:
            try:
                command = input("\n> ").strip()
                if command:
                    return command
                else:
                    print("请输入命令")
            except (KeyboardInterrupt, EOFError):
                print("\n")
                return 'q'

    def _execute_quick_command(self, command: str) -> bool:
        """
        执行快捷命令

        Args:
            command: 命令字符串

        Returns:
            True表示继续循环，False表示退出
        """
        if not command:
            return True

        command = command.lower()

        # 退出命令
        if command in ['q', 'quit', 'exit', '0']:
            print("\n👋 再见！")
            return False

        # 查看命令: v1, v2, ...
        if command.startswith('v'):
            try:
                # 提取数字，支持 v1, v2-5 等
                num_str = command[1:].strip()
                if '-' in num_str:
                    # 范围查看，暂时只处理第一个
                    start = int(num_str.split('-')[0])
                    if 1 <= start <= len(self.current_sessions):
                        self._view_session_by_index(start - 1)
                    else:
                        print(f"{Colors.ERROR}❌ 无效的序号: {start}{Colors.RESET}")
                else:
                    idx = int(num_str)
                    if 1 <= idx <= len(self.current_sessions):
                        self._view_session_by_index(idx - 1)
                    else:
                        print(f"{Colors.ERROR}❌ 无效的序号: {idx}{Colors.RESET}")
            except ValueError:
                print(f"{Colors.ERROR}❌ 无效的命令格式: {command}{Colors.RESET}")
                print("使用格式: v1 (查看第1个会话)")

        # 导出命令: e1, e2, e1-3, ...
        elif command.startswith('e'):
            try:
                num_str = command[1:].strip()
                if '-' in num_str:
                    # 范围导出
                    parts = num_str.split('-')
                    start = int(parts[0])
                    end = int(parts[1]) if len(parts) > 1 else start

                    if 1 <= start <= end <= len(self.current_sessions):
                        self._export_range(start, end)
                    else:
                        print(f"{Colors.ERROR}❌ 无效的范围: {start}-{end}{Colors.RESET}")
                else:
                    idx = int(num_str)
                    if 1 <= idx <= len(self.current_sessions):
                        self._export_single_by_index(idx - 1)
                    else:
                        print(f"{Colors.ERROR}❌ 无效的序号: {idx}{Colors.RESET}")
            except ValueError:
                print(f"{Colors.ERROR}❌ 无效的命令格式: {command}{Colors.RESET}")
                print("使用格式: e1 (导出第1个会话) 或 e1-3 (导出1-3个会话)")

        # 搜索命令: s python, s 关键词
        elif command.startswith('s '):
            keyword = command[2:].strip()
            if keyword:
                self._search_sessions(keyword)
            else:
                print(f"{Colors.ERROR}❌ 请输入搜索关键词{Colors.RESET}")

        # 日期筛选命令: d 2026-02-28, date 2026-02-28
        elif command.startswith('d ') or command.startswith('date '):
            # 提取日期部分，支持 "d 2026-02-28" 或 "date 2026-02-28"
            if command.startswith('d '):
                date_str = command[2:].strip()
            else:
                date_str = command[5:].strip()

            if date_str:
                self._filter_sessions_by_date(date_str)
            else:
                print(f"{Colors.ERROR}❌ 请输入日期，格式如: 2026-02-28 或 02-28{Colors.RESET}")

        # 菜单命令: m
        elif command == 'm':
            self._show_full_menu()

        # 显示更多会话: more, l
        elif command in ['more', 'l']:
            self._show_more_sessions()

        # 统计信息: stats, t
        elif command in ['stats', 't']:
            self._show_stats()

        # 配置选项: config, c
        elif command in ['config', 'c']:
            self._show_settings()

        # 帮助命令: ?, help, h
        elif command in ['?', 'help', 'h']:
            self._show_help()

        else:
            print(f"{Colors.ERROR}❌ 未知命令: {command}{Colors.RESET}")
            print("输入 '?' 查看帮助命令")

        # 命令执行后等待用户按回车继续（除了退出、搜索和日期筛选）
        if (not command.startswith('q') and
            not command.startswith('s ') and
            not command.startswith('d ') and
            not command.startswith('date ')):
            input("\n↵ 按回车键继续...")

        return True

    def _view_session_by_index(self, index: int):
        """通过索引查看会话"""
        if not self.current_sessions or index < 0 or index >= len(self.current_sessions):
            print("❌ 无效的会话索引")
            return

        session = self.current_sessions[index]
        session_id = session.get('sessionId')

        if not session_id:
            print("❌ 会话ID不存在")
            return

        conversation = self.parser.get_conversation(session_id)
        if not conversation:
            print(f"❌ 无法加载会话: {session_id}")
            return

        self.current_conversation = conversation

        # 显示会话详情（使用原有的显示逻辑但简化）
        print(f"\n💬 {conversation.display_title}")
        print(f"   时间: {Colors.CYAN}{conversation.start_time.strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
        print(f"   项目: {conversation.project_path}")
        print(f"   持续时间: {conversation.duration_seconds:.0f}秒")
        print(f"   消息数量: {len(conversation.messages)}")
        print("=" * 80)

        # 显示前3条消息预览
        for i, msg in enumerate(conversation.messages[:3], 1):
            time_str = msg.timestamp.strftime("%H:%M:%S")
            role_icon = "👤" if msg.role == "user" else "🤖"
            role_name = "用户" if msg.role == "user" else "Claude"

            print(f"\n{role_icon} {role_name} ({i}) [{time_str}]")
            print("-" * 40)
            print(msg.content[:300])  # 显示前300字符
            if len(msg.content) > 300:
                print("... [内容已截断]")

        if len(conversation.messages) > 3:
            print(f"\n... 还有 {len(conversation.messages) - 3} 条消息未显示")

        print("\n" + "=" * 80)

        # 提供导出选项
        export_choice = input("\n输入 'e' 导出此会话，或直接按回车返回: ").strip().lower()
        if export_choice == 'e':
            self._export_conversation(conversation)

    def _export_single_by_index(self, index: int):
        """通过索引导出单个会话"""
        if not self.current_sessions or index < 0 or index >= len(self.current_sessions):
            print("❌ 无效的会话索引")
            return

        session = self.current_sessions[index]
        session_id = session.get('sessionId')

        if not session_id:
            print("❌ 会话ID不存在")
            return

        conversation = self.parser.get_conversation(session_id)
        if not conversation:
            print(f"❌ 无法加载会话: {session_id}")
            return

        self._export_conversation(conversation)

    def _export_range(self, start: int, end: int):
        """导出指定范围的会话（start和end都是1-based）"""
        if not self.current_sessions:
            print("❌ 当前没有会话列表")
            return

        if start < 1 or end > len(self.current_sessions) or start > end:
            print(f"❌ 无效的范围: {start}-{end}")
            return

        count = end - start + 1
        include_thinking = self._confirm_include_thinking()

        print(f"\n📤 开始导出 {count} 个会话 ({start}-{end})...")
        exported_count = 0

        for i in range(start - 1, end):
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
                        print(f"  {Colors.SUCCESS}✅ ({exported_count}/{count}) {conversation.display_title}{Colors.RESET}")

                        # 询问是否复制到目标文件夹
                        self._prompt_copy_file(Path(filepath))
                    except Exception as e:
                        print(f"  ❌ 导出失败: {e}")

        print(f"\n{Colors.SUCCESS}✅ 批量导出完成，共导出 {exported_count} 个会话{Colors.RESET}")
        print(f"导出目录: {self.exporter.output_dir}")


    def _show_full_menu(self):
        """显示完整菜单（传统模式）"""
        print("\n📌 完整菜单模式:")
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
                    if choice == '0':
                        print("\n👋 再见！")
                        return False
                    else:
                        self._handle_menu_choice(choice)
                        return True
                else:
                    print("❌ 无效选项，请输入 0-7 之间的数字")
            except (KeyboardInterrupt, EOFError):
                print("\n")
                return True

    def _show_help(self):
        """显示帮助信息"""
        print("\n📖 快捷命令帮助:")
        print("=" * 50)
        print("会话操作:")
        print("  v1, v2, ...     查看第1,2,...个会话")
        print("  v1-3            查看第1-3个会话（暂支持第一个）")
        print("  e1, e2, ...     导出第1,2,...个会话")
        print("  e1-3            导出第1-3个会话")
        print("  s 关键词        搜索包含关键词的会话")
        print("  d 日期, date 日期  筛选指定日期的会话 (格式: 2026-02-28 或 02-28)")
        print()
        print("系统命令:")
        print("  m               显示完整菜单")
        print("  more, l         显示更多会话")
        print("  stats, t        查看统计信息")
        print("  config, c       配置选项")
        print("  ?, help, h      显示此帮助")
        print("  q, quit, exit   退出程序")
        print("=" * 50)

    def _list_sessions_with_menu(self, limit: Optional[int] = None):
        """
        显示会话列表和菜单（兼容旧版本）

        Args:
            limit: 显示数量限制，None使用默认值
        """
        # 调用新的紧凑列表显示
        self._show_compact_list(limit)

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
        print(f"   时间: {Colors.CYAN}{conversation.start_time.strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
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
                        print(f"  {Colors.SUCCESS}✅ ({exported_count}/{count}) {conversation.display_title}{Colors.RESET}")

                        # 询问是否复制到目标文件夹
                        self._prompt_copy_file(Path(filepath))
                    except Exception as e:
                        print(f"  ❌ 导出失败 {session_id}: {e}")

        print(f"\n{Colors.SUCCESS}✅ 批量导出完成，共导出 {exported_count} 个会话{Colors.RESET}")
        print(f"导出目录: {self.exporter.output_dir}")

    def _search_sessions(self, keyword: Optional[str] = None):
        """
        搜索会话

        Args:
            keyword: 搜索关键词，如果为None则提示输入
        """
        if keyword is None:
            keyword = input("请输入搜索关键词: ").strip()
            if not keyword:
                print("❌ 搜索关键词不能为空")
                return

        # 调用带参数的搜索函数
        self._search_sessions_with_keyword(keyword)

    def _search_sessions_with_keyword(self, keyword: str):
        """
        使用关键词搜索会话（内部实现）

        Args:
            keyword: 搜索关键词
        """
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
        self._show_compact_list(len(results), use_existing=True)
        # 设置跳过下一次显示，避免重复显示列表
        self.skip_next_display = True

    def _filter_sessions_by_date(self, date_str: str):
        """
        按日期筛选会话

        Args:
            date_str: 日期字符串，格式为 YYYY-MM-DD 或 MM-DD
        """
        date_str = date_str.strip()

        # 验证日期格式
        if len(date_str) == 10:
            if date_str[4] != '-' or date_str[7] != '-':
                print(f"{Colors.ERROR}❌ 无效的日期格式: '{date_str}'，应为 YYYY-MM-DD{Colors.RESET}")
                return False
        elif len(date_str) == 5:
            if date_str[2] != '-':
                print(f"{Colors.ERROR}❌ 无效的日期格式: '{date_str}'，应为 MM-DD{Colors.RESET}")
                return False
        else:
            print(f"{Colors.ERROR}❌ 无效的日期格式: '{date_str}'，应为 YYYY-MM-DD 或 MM-DD{Colors.RESET}")
            return False

        print(f"\n{Colors.INFO}📅 正在筛选日期为 '{date_str}' 的会话...{Colors.RESET}")

        # 获取所有会话（限制为最近500个，避免性能问题）
        all_sessions = self.parser.list_sessions(limit=500)
        results = []
        match_count = 0
        total_count = 0

        for session in all_sessions:
            if 'datetime' not in session:
                continue
            dt = session.get('datetime')
            if not dt:
                continue
            total_count += 1
            try:
                session_date_str = dt.strftime('%Y-%m-%d')
                session_date_short = dt.strftime('%m-%d')
            except (AttributeError, TypeError) as e:
                # dt 不是有效的 datetime 对象
                continue

            # 根据日期字符串长度决定匹配策略
            match = False
            if len(date_str) == 10:  # YYYY-MM-DD 格式
                match = date_str == session_date_str
            elif len(date_str) == 5:  # MM-DD 格式
                match = date_str == session_date_short
            else:
                # 回退到原始逻辑
                match = date_str == session_date_str or date_str == session_date_short

            if match:
                results.append(session)
                match_count += 1

        if not results:
            print(f"{Colors.ERROR}❌ 未找到日期为 '{date_str}' 的会话{Colors.RESET}")
            return False

        # 更新当前会话列表为筛选结果
        self.current_sessions = results
        print(f"{Colors.SUCCESS}✅ 找到 {len(results)} 个日期为 '{date_str}' 的会话 (检查了 {total_count} 个有日期信息的会话){Colors.RESET}")

        # 调试信息：显示前3个匹配会话的日期
        if results:
            print(f"{Colors.INFO}📅 匹配的会话日期示例:{Colors.RESET}")
            for i, session in enumerate(results[:3]):
                dt = session.get('datetime')
                if dt:
                    date_display = dt.strftime('%Y-%m-%d %H:%M')
                    print(f"  {i+1}. {date_display}")

        # 显示筛选结果
        self._show_compact_list(len(results), use_existing=True)
        # 设置跳过下一次显示，避免重复显示列表
        self.skip_next_display = True
        return True

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
            print(f"{Colors.ERROR}❌ 未找到任何会话记录{Colors.RESET}")
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
        print(f"4. 目标文件夹 (复制用): {self.target_folder or '未设置'}")
        print()

        choice = input("请选择要修改的配置 (1-4) 或按回车返回: ").strip()

        if choice == '1':
            try:
                new_limit = input(f"新的显示数量 (当前: {self.default_limit}): ").strip()
                if new_limit:
                    new_limit = int(new_limit)
                    if new_limit > 0:
                        self.default_limit = new_limit
                        self.config.limit = new_limit  # 更新配置对象
                        print(f"✅ 已更新显示数量为 {new_limit}")
                    else:
                        print("❌ 显示数量必须大于0")
            except ValueError:
                print("❌ 请输入有效的数字")

        elif choice == '2':
            include = input("是否包含思考过程? (y/n): ").strip().lower()
            if include in ['y', 'yes', '是']:
                self.include_thinking = True
                self.config.include_thinking = True  # 更新配置对象
                print("✅ 已启用包含思考过程")
            elif include in ['n', 'no', '否']:
                self.include_thinking = False
                self.config.include_thinking = False  # 更新配置对象
                print("✅ 已禁用包含思考过程")
            else:
                print("❌ 无效输入")

        elif choice == '3':
            new_dir = input(f"新的导出目录 (当前: {self.output_dir}): ").strip()
            if new_dir:
                self.output_dir = new_dir
                self.config.output_dir = new_dir  # 更新配置对象
                self.exporter.output_dir = Path(new_dir)
                # 确保目录存在
                self.exporter.output_dir.mkdir(parents=True, exist_ok=True)
                print(f"✅ 已更新导出目录为 {new_dir}")

        elif choice == '4':
            new_target = input(f"新的目标文件夹 (当前: {self.target_folder or '未设置'}): ").strip()
            if new_target:
                self.target_folder = new_target
                self.config.target_folder = new_target  # 更新配置对象
                # 确保目录存在
                target_path = Path(new_target)
                if target_path.exists() and not target_path.is_dir():
                    print(f"❌ 目标路径存在但不是目录: {new_target}")
                    self.target_folder = ""
                    self.config.target_folder = ""
                else:
                    target_path.mkdir(parents=True, exist_ok=True)
                    print(f"✅ 已更新目标文件夹为 {new_target}")
            else:
                # 清空目标文件夹
                self.target_folder = ""
                self.config.target_folder = ""
                print("✅ 已清除目标文件夹设置")

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
        default_str = "y" if self.include_thinking else "n"
        include = input(f"是否包含思考过程? (y/n, 默认{default_str}): ").strip().lower()
        if include == "":
            return self.include_thinking
        return include in ['y', 'yes', '是']

    def _prompt_copy_file(self, source_path: Path) -> bool:
        """
        询问用户是否将文件复制到目标文件夹

        Args:
            source_path: 源文件路径

        Returns:
            是否执行了复制操作
        """
        # 检查是否设置了目标文件夹
        if not self.target_folder:
            return False

        # 展开环境变量和用户目录
        expanded_path = os.path.expandvars(str(self.target_folder))
        target_dir = Path(expanded_path).expanduser()

        if not target_dir.exists():
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
                print(f"📁 已创建目标文件夹: {target_dir}")
            except Exception as e:
                print(f"❌ 无法创建目标文件夹 {target_dir}: {e}")
                return False

        # 构建目标路径
        target_path = target_dir / source_path.name

        # 检查目标文件是否已存在
        if target_path.exists():
            overwrite = input(f"⚠️  目标文件已存在: {target_path}\n是否覆盖? (y/n, 默认n): ").strip().lower()
            if overwrite not in ['y', 'yes', '是']:
                print("⏭️  跳过复制")
                return False

        # 询问用户是否复制
        copy_choice = input(f"是否复制到目标文件夹 ({target_path})? (y/n, 默认y): ").strip().lower()
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

            # 询问是否复制到目标文件夹
            self._prompt_copy_file(filepath)
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