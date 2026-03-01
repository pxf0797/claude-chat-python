"""
JSONL file parser for Claude Code chat history.
"""
import json
from pathlib import Path
from typing import Iterator, List, Dict, Any, Optional
from datetime import datetime

from .core import Message, Conversation


class ClaudeDataParser:
    """Claude Code JSONL data parser."""

    def __init__(self, claude_dir: Optional[str] = None):
        """
        Initialize parser with Claude Code data directory.

        Args:
            claude_dir: Path to Claude Code directory (default: ~/.claude)
        """
        self.claude_dir = Path(claude_dir or "~/.claude").expanduser()
        self.history_file = self.claude_dir / "history.jsonl"
        self.projects_dir = self.claude_dir / "projects"

    def list_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        List all chat sessions from history.jsonl.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of session dictionaries with metadata
        """
        sessions = []
        if not self.history_file.exists():
            print(f"Warning: History file not found at {self.history_file}")
            return sessions

        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        session_data = json.loads(line)
                        # Convert timestamp to datetime
                        if 'timestamp' in session_data:
                            ts = session_data['timestamp']
                            # Handle both milliseconds and seconds
                            if ts > 1000000000000:  # Likely milliseconds
                                session_data['datetime'] = datetime.fromtimestamp(ts/1000)
                            else:
                                session_data['datetime'] = datetime.fromtimestamp(ts)
                        sessions.append(session_data)
                    except json.JSONDecodeError as e:
                        print(f"Warning: Failed to parse line {line_num}: {e}")
                        continue
        except Exception as e:
            print(f"Error reading history file: {e}")
            return []

        # Sort by timestamp (newest first)
        sessions.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        return sessions[:limit] if limit else sessions

    def get_conversation(self, session_id: str) -> Optional[Conversation]:
        """
        Get complete conversation for a session ID.

        Args:
            session_id: Session ID to retrieve

        Returns:
            Conversation object or None if not found
        """
        # Find session file
        session_file = self._find_session_file(session_id)
        if not session_file:
            print(f"Session file not found for ID: {session_id}")
            return None

        messages = []
        start_time = None
        end_time = None
        display_title = ""
        project_path = ""
        total_tokens = 0

        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)

                        # Parse messages
                        if data.get('type') == 'user':
                            message = self._parse_user_message(data)
                            if message:
                                messages.append(message)

                        elif data.get('type') == 'assistant':
                            message = self._parse_assistant_message(data)
                            if message:
                                messages.append(message)

                        # Extract metadata
                        if 'timestamp' in data:
                            ts = self._parse_timestamp(data['timestamp'])
                            if not start_time or ts < start_time:
                                start_time = ts
                            if not end_time or ts > end_time:
                                end_time = ts

                        if 'display' in data:
                            display_title = data['display']
                        if 'project' in data:
                            project_path = data.get('project', '')
                        if 'usage' in data:
                            usage = data['usage']
                            if isinstance(usage, dict):
                                total_tokens += usage.get('total_tokens', 0)

                    except (json.JSONDecodeError, KeyError) as e:
                        print(f"Warning: Failed to parse line {line_num}: {e}")
                        continue

        except Exception as e:
            print(f"Error reading session file {session_file}: {e}")
            return None

        if not messages:
            print(f"No messages found in session: {session_id}")
            return None

        return Conversation(
            session_id=session_id,
            display_title=display_title or f"Session {session_id[:8]}",
            project_path=project_path,
            start_time=start_time or datetime.now(),
            end_time=end_time or datetime.now(),
            messages=messages,
            total_tokens=total_tokens if total_tokens > 0 else None
        )

    def _find_session_file(self, session_id: str) -> Optional[Path]:
        """
        Find session file in projects directory.

        Args:
            session_id: Session ID to find

        Returns:
            Path to session file or None if not found
        """
        if not self.projects_dir.exists():
            return None

        # Look for session file in all project directories
        for project_dir in self.projects_dir.iterdir():
            if project_dir.is_dir():
                session_file = project_dir / f"{session_id}.jsonl"
                if session_file.exists():
                    return session_file

                # Also check for other naming patterns
                for pattern in [f"*{session_id}*.jsonl", f"{session_id}*.jsonl"]:
                    for file in project_dir.glob(pattern):
                        if file.exists():
                            return file

        return None

    def _parse_timestamp(self, timestamp: Any) -> datetime:
        """Parse timestamp from various formats."""
        try:
            if isinstance(timestamp, (int, float)):
                # Handle milliseconds
                if timestamp > 1000000000000:  # Likely milliseconds
                    return datetime.fromtimestamp(timestamp / 1000)
                else:  # Likely seconds
                    return datetime.fromtimestamp(timestamp)
            elif isinstance(timestamp, str):
                # Try ISO format
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                return datetime.now()
        except (ValueError, TypeError):
            return datetime.now()

    def _parse_user_message(self, data: Dict) -> Optional[Message]:
        """Parse user message from data."""
        try:
            message_data = data['message']
            content_parts = []

            # Extract content based on format
            if isinstance(message_data.get('content'), str):
                content_parts.append(message_data['content'])
            elif isinstance(message_data.get('content'), dict):
                text = message_data['content'].get('text', '')
                if text:
                    content_parts.append(text)
            elif isinstance(message_data.get('content'), list):
                # Handle list of content blocks
                for item in message_data['content']:
                    if isinstance(item, dict):
                        item_type = item.get('type', '')

                        if item_type == 'text':
                            item_text = item.get('text', '')
                            if item_text:
                                content_parts.append(item_text)
                        elif item_type == 'tool_result':
                            # Extract tool result content
                            tool_content = item.get('content', '')
                            if tool_content:
                                content_parts.append(f"[工具结果] {tool_content}")
                        elif item_type == 'image':
                            # Handle image content (marker only)
                            image_info = item.get('source', {})
                            if isinstance(image_info, dict):
                                media_type = image_info.get('media_type', 'image')
                                content_parts.append(f"[{media_type}]")
                            else:
                                content_parts.append("[图像]")
                        else:
                            # Try to extract any text content from various fields
                            item_text = item.get('text', '') or item.get('content', '')
                            if item_text:
                                content_parts.append(item_text)

            content = " ".join(content_parts).strip()

            return Message(
                message_id=data.get('uuid', str(hash(str(data)))),
                role='user',
                content=content,
                timestamp=self._parse_timestamp(data['timestamp'])
            )
        except (KeyError, TypeError) as e:
            print(f"Warning: Failed to parse user message: {e}")
            return None

    def _parse_assistant_message(self, data: Dict) -> Optional[Message]:
        """Parse assistant message from data."""
        try:
            message_data = data['message']
            content_parts = []
            thinking = ""
            model = message_data.get('model', '')

            # Handle content array
            if isinstance(message_data.get('content'), list):
                for item in message_data['content']:
                    if isinstance(item, dict):
                        item_type = item.get('type', '')

                        if item_type == 'thinking':
                            thinking_text = item.get('thinking', '')
                            thinking = thinking_text
                            # Include thinking as part of content with marker
                            if thinking_text:
                                content_parts.append(f"[思考] {thinking_text}")
                        elif item_type == 'text':
                            text_content = item.get('text', '')
                            if text_content:
                                content_parts.append(text_content)
                        elif item_type == 'tool_use':
                            # Extract tool use information
                            tool_name = item.get('name', '')
                            tool_input = item.get('input', {})
                            # Format tool use as text
                            tool_text = f"[工具调用: {tool_name}]"
                            if tool_input:
                                tool_text += f" {str(tool_input)}"
                            content_parts.append(tool_text)
                        elif item_type == 'tool_result':
                            # Extract tool result
                            tool_name = item.get('tool_name', '')
                            tool_result = item.get('result', '')
                            # Format tool result
                            result_text = f"[工具结果: {tool_name}]"
                            if tool_result:
                                # Smart truncation for long results
                                result_str = str(tool_result)
                                if len(result_str) > 500:
                                    # Show first 300 chars and last 100 chars for context
                                    result_str = result_str[:300] + " [...] " + result_str[-100:]
                                result_text += f" {result_str}"
                            content_parts.append(result_text)
                        elif item_type == 'image':
                            # Handle image content (marker only)
                            image_info = item.get('source', {})
                            if isinstance(image_info, dict):
                                media_type = image_info.get('media_type', 'image')
                                content_parts.append(f"[{media_type}]")
                            else:
                                content_parts.append("[图像]")
                        else:
                            # Unknown type, try to extract any text content
                            for key in ['text', 'content', 'result', 'input', 'thinking']:
                                if key in item and item[key]:
                                    val = item[key]
                                    if isinstance(val, str):
                                        content_parts.append(f"[{item_type}] {val}")
                                        break
                                    elif isinstance(val, (dict, list)):
                                        content_parts.append(f"[{item_type}] {str(val)}")
                                        break
            elif isinstance(message_data.get('content'), str):
                content_parts.append(message_data['content'])

            # Join all content parts
            content = "\n".join(content_parts).strip()

            return Message(
                message_id=data.get('uuid', str(hash(str(data)))),
                role='assistant',
                content=content,
                timestamp=self._parse_timestamp(data['timestamp']),
                model=model,
                thinking=thinking.strip() if thinking else None
            )
        except (KeyError, TypeError) as e:
            print(f"Warning: Failed to parse assistant message: {e}")
            return None

    def get_recent_conversations(self, limit: int = 5) -> List[Conversation]:
        """
        Get recent conversations.

        Args:
            limit: Maximum number of conversations to return

        Returns:
            List of Conversation objects
        """
        sessions = self.list_sessions(limit=limit)
        conversations = []

        for session in sessions:
            session_id = session.get('sessionId')
            if session_id:
                conversation = self.get_conversation(session_id)
                if conversation:
                    conversations.append(conversation)

        return conversations