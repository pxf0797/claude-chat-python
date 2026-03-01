"""
Markdown exporter for Claude chat conversations.
"""
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import re

from .core import Conversation


class MarkdownExporter:
    """Markdown format exporter for conversations."""

    def __init__(self, output_dir: str = "./claude-chats"):
        """
        Initialize exporter with output directory.

        Args:
            output_dir: Directory to save exported Markdown files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_conversation(self, conversation: Conversation,
                           include_thinking: bool = False,
                           format_type: str = "basic") -> Path:
        """
        Export single conversation to Markdown file.

        Args:
            conversation: Conversation to export
            include_thinking: Whether to include assistant thinking process
            format_type: Export format ("basic" or "enhanced")

        Returns:
            Path to exported file
        """
        # Generate filename
        date_str = conversation.start_time.strftime("%Y-%m-%d")
        safe_title = self._sanitize_filename(conversation.display_title[:50])
        filename = f"{date_str}_{safe_title}_{conversation.session_id[:8]}.md"
        filepath = self.output_dir / filename

        # Generate content based on format type
        if format_type == "enhanced":
            content = self._generate_enhanced_markdown(conversation, include_thinking)
        else:
            content = self._generate_basic_markdown(conversation, include_thinking)

        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        return filepath

    def _generate_basic_markdown(self, conversation: Conversation,
                                include_thinking: bool) -> str:
        """Generate basic Markdown content."""
        lines = []

        # Frontmatter
        lines.append("---")
        lines.append(f"id: {conversation.session_id}")
        lines.append(f"title: {conversation.display_title}")
        lines.append(f"date: {conversation.start_time.strftime('%Y-%m-%d')}")
        lines.append(f"time: {conversation.start_time.strftime('%H:%M:%S')}")
        lines.append(f"project: {conversation.project_path}")
        lines.append(f"duration: {conversation.duration_seconds:.0f}s")
        lines.append("tags: [claude/conversation]")
        lines.append("---\n")

        # Title
        lines.append(f"# 💬 {conversation.display_title}\n")

        # Metadata
        lines.append(f"**会话ID**: `{conversation.session_id}`  ")
        lines.append(f"**时间**: {conversation.start_time.strftime('%Y-%m-%d %H:%M:%S')}  ")
        lines.append(f"**项目**: `{conversation.project_path}`  ")
        if conversation.total_tokens:
            lines.append(f"**总token数**: {conversation.total_tokens}  ")
        lines.append(f"**持续时间**: {conversation.duration_seconds:.0f}秒  ")
        lines.append(f"**消息数量**: {len(conversation.messages)}  \n")

        lines.append("---\n")

        # Conversation content
        for msg in conversation.messages:
            time_str = msg.timestamp.strftime("%H:%M:%S")

            if msg.role == "user":
                lines.append(f"## 👤 用户")
                lines.append(f"> *{time_str}*\n")
                lines.append(f"{msg.content}\n")
                lines.append("---\n")

            elif msg.role == "assistant":
                lines.append(f"## 🤖 Claude")
                lines.append(f"> *{time_str}*")
                if msg.model:
                    lines.append(f"> *模型: {msg.model}*\n")
                else:
                    lines.append("\n")

                # Include thinking process if requested
                if include_thinking and msg.thinking:
                    lines.append("### 💭 思考过程")
                    lines.append(f"```\n{msg.thinking}\n```\n")
                    lines.append("### 📝 回答\n")

                lines.append(f"{msg.content}\n")
                lines.append("---\n")

        return "\n".join(lines)

    def _generate_enhanced_markdown(self, conversation: Conversation,
                                   include_thinking: bool) -> str:
        """Generate enhanced Markdown content with more features."""
        lines = []

        # Enhanced frontmatter
        lines.append("---")
        lines.append(f"id: {conversation.session_id}")
        lines.append(f"title: {conversation.display_title}")
        lines.append(f"date: {conversation.start_time.strftime('%Y-%m-%d')}")
        lines.append(f"time: {conversation.start_time.strftime('%H:%M:%S')}")
        lines.append(f"week: {conversation.start_time.strftime('%Y-W%W')}")
        lines.append(f"project: {conversation.project_path}")
        lines.append(f"duration: {conversation.duration_seconds:.0f}s")
        lines.append(f"message_count: {len(conversation.messages)}")
        if conversation.total_tokens:
            lines.append(f"total_tokens: {conversation.total_tokens}")

        # Extract tags from content
        tags = self._extract_tags(conversation)
        tags_line = "tags: [" + ", ".join([f'"{tag}"' for tag in tags]) + "]"
        lines.append(tags_line)

        lines.append("---\n")

        # Enhanced header
        lines.append(f"# 💬 {conversation.display_title}\n")

        # Summary box
        lines.append("```ad-info")
        lines.append("title: 对话摘要")
        lines.append(f"**会话ID**: `{conversation.session_id[:12]}...`  ")
        lines.append(f"**时间**: {conversation.start_time.strftime('%Y-%m-%d %H:%M:%S')}  ")
        lines.append(f"**持续时间**: {conversation.duration_minutes:.1f}分钟  ")
        lines.append(f"**消息数量**: {len(conversation.messages)} (👤{len(conversation.user_messages)} | 🤖{len(conversation.assistant_messages)})  ")
        if conversation.total_tokens:
            lines.append(f"**Token用量**: {conversation.total_tokens}  ")
        lines.append(f"**项目路径**: `{conversation.project_path}`  ")
        lines.append("```\n")

        # Conversation content with improved formatting
        for i, msg in enumerate(conversation.messages):
            time_str = msg.timestamp.strftime("%H:%M:%S")

            if msg.role == "user":
                lines.append(f"## 👤 用户 ({i//2 + 1})")
                lines.append(f"<small>{time_str}</small>\n")
                lines.append(f"{msg.content}\n")

                # Add separator
                if i < len(conversation.messages) - 1:
                    lines.append("---\n")

            elif msg.role == "assistant":
                lines.append(f"## 🤖 Claude ({i//2 + 1})")
                lines.append(f"<small>{time_str}")
                if msg.model:
                    lines.append(f" · {msg.model}")
                lines.append("</small>\n")

                # Include thinking process
                if include_thinking and msg.thinking:
                    lines.append("### 💭 思考过程")
                    lines.append("```thinking")
                    lines.append(msg.thinking)
                    lines.append("```\n")
                    lines.append("### 📝 回答\n")

                lines.append(f"{msg.content}\n")

                # Add separator
                if i < len(conversation.messages) - 1:
                    lines.append("---\n")

        # Footer with links and actions
        lines.append("\n## 🔗 相关链接")
        lines.append(f"- [[Claude对话索引]]")
        lines.append(f"- [[{conversation.start_time.strftime('%Y-%m-%d')}的对话]]")
        lines.append(f"- [[{conversation.start_time.strftime('%Y-W%W')}周对话]]")
        if conversation.project_path and conversation.project_path != "unknown":
            lines.append(f"- [[项目:{conversation.project_path}]]")
        lines.append("")

        # Tags section
        if tags:
            lines.append("## 🏷️ 标签")
            for tag in tags:
                lines.append(f"#{tag}")
            lines.append("")

        return "\n".join(lines)

    def export_multiple(self, conversations: List[Conversation],
                       include_thinking: bool = False,
                       format_type: str = "basic") -> List[Path]:
        """
        Export multiple conversations.

        Args:
            conversations: List of conversations to export
            include_thinking: Whether to include thinking process
            format_type: Export format

        Returns:
            List of paths to exported files
        """
        exported_files = []

        for conv in conversations:
            try:
                filepath = self.export_conversation(
                    conv,
                    include_thinking=include_thinking,
                    format_type=format_type
                )
                exported_files.append(filepath)
                print(f"✅ 已导出: {conv.display_title}")
            except Exception as e:
                print(f"❌ 导出失败 {conv.session_id}: {e}")

        return exported_files

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename by removing invalid characters.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Remove invalid characters for filenames
        invalid_chars = r'<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')

        # Remove control characters and extra spaces
        filename = re.sub(r'[\x00-\x1F\x7F]', '', filename)
        filename = re.sub(r'\s+', ' ', filename).strip()

        # Limit length
        if len(filename) > 100:
            filename = filename[:100]

        return filename

    def _extract_tags(self, conversation: Conversation) -> List[str]:
        """
        Extract tags from conversation content.

        Args:
            conversation: Conversation to extract tags from

        Returns:
            List of tags
        """
        tags = set()

        # Base tags
        tags.add("claude/conversation")
        tags.add(f"date/{conversation.start_time.strftime('%Y-%m-%d')}")
        tags.add(f"week/{conversation.start_time.strftime('%Y-W%W')}")

        # Extract hashtags from content
        all_text = " ".join([msg.content for msg in conversation.messages])
        hashtags = re.findall(r'#(\w+)', all_text)
        for tag in hashtags[:10]:  # Limit to 10 hashtags
            tags.add(tag.lower())

        # Extract project-based tag
        if conversation.project_path and conversation.project_path != "unknown":
            project_name = Path(conversation.project_path).name
            if project_name:
                tags.add(f"project/{project_name}")

        return sorted(tags)