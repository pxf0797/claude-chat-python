"""
Configuration for Claude chat manager.
"""
import os
from pathlib import Path
from typing import Optional


class Config:
    """Configuration manager."""

    # Default values
    DEFAULT_CLAUDE_DIR = str(Path.home() / ".claude")
    DEFAULT_OUTPUT_DIR = "./claude-chats"
    DEFAULT_EXPORT_FORMAT = "enhanced"  # "basic" or "enhanced"
    DEFAULT_INCLUDE_THINKING = False
    DEFAULT_LIMIT = 20
    DEFAULT_TARGET_FOLDER = "$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/Personal/95_ClaudeCode/2026/02"  # 默认空，表示不复制到其他文件夹

    def __init__(self):
        self.claude_dir = self._get_env_var("CLAUDE_DIR", self.DEFAULT_CLAUDE_DIR)
        self.output_dir = self._get_env_var("CLAUDE_OUTPUT_DIR", self.DEFAULT_OUTPUT_DIR)
        self.export_format = self._get_env_var("CLAUDE_EXPORT_FORMAT", self.DEFAULT_EXPORT_FORMAT)
        self.include_thinking = self._get_bool_env_var("CLAUDE_INCLUDE_THINKING", self.DEFAULT_INCLUDE_THINKING)
        self.limit = self._get_int_env_var("CLAUDE_LIMIT", self.DEFAULT_LIMIT)
        self.target_folder = self._get_env_var("CLAUDE_TARGET_FOLDER", self.DEFAULT_TARGET_FOLDER)

    def _get_env_var(self, name: str, default: str) -> str:
        """Get environment variable or default."""
        value = os.getenv(name)
        return value if value is not None else default

    def _get_bool_env_var(self, name: str, default: bool) -> bool:
        """Get boolean environment variable."""
        value = os.getenv(name)
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "y")

    def _get_int_env_var(self, name: str, default: int) -> int:
        """Get integer environment variable."""
        value = os.getenv(name)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default

    def validate(self) -> bool:
        """Validate configuration."""
        # Check if claude directory exists
        claude_path = Path(self.claude_dir).expanduser()
        if not claude_path.exists():
            print(f"Warning: Claude directory does not exist: {claude_path}")
            return False

        # Check history file
        history_file = claude_path / "history.jsonl"
        if not history_file.exists():
            print(f"Warning: History file not found: {history_file}")
            print("Claude Code may not be installed or no chat history exists.")
            return False

        return True

    def print_summary(self):
        """Print configuration summary."""
        print("Configuration Summary:")
        print(f"  Claude directory: {self.claude_dir}")
        print(f"  Output directory: {self.output_dir}")
        print(f"  Export format: {self.export_format}")
        print(f"  Include thinking: {self.include_thinking}")
        print(f"  Default limit: {self.limit}")
        print(f"  Target folder: {self.target_folder or '未设置'}")

    @classmethod
    def from_args(cls, args) -> 'Config':
        """Create config from command line arguments."""
        config = cls()

        # Override with args if provided
        if hasattr(args, 'claude_dir') and args.claude_dir:
            config.claude_dir = args.claude_dir
        if hasattr(args, 'output_dir') and args.output_dir:
            config.output_dir = args.output_dir
        if hasattr(args, 'format') and args.format:
            config.export_format = args.format
        if hasattr(args, 'include_thinking') and args.include_thinking:
            config.include_thinking = args.include_thinking
        if hasattr(args, 'limit') and args.limit:
            config.limit = args.limit
        if hasattr(args, 'target_folder') and args.target_folder:
            config.target_folder = args.target_folder

        return config


# Global config instance
config = Config()


def get_config() -> Config:
    """Get global configuration instance."""
    return config


def setup_environment():
    """Setup environment for Claude chat manager."""
    # Create output directory if it doesn't exist
    output_path = Path(config.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Expand claude directory path
    claude_path = Path(config.claude_dir).expanduser()

    print(f"Claude directory: {claude_path}")
    print(f"Output directory: {output_path}")

    return config.validate()