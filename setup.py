#!/usr/bin/env python3
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="claude-chat-manager",
    version="0.1.0",
    author="xfpan",
    author_email="xfpan@example.com",
    description="Claude Code chat history viewer and exporter",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/xfpan/claude-chat-python",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies, uses standard library only
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "isort>=5.0.0",
            "mypy>=1.0.0",
        ],
        "rich": [
            "rich>=13.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "claude-chat=claude_chat.cli:main",
            "claude-chat-view=scripts.view_sessions:main",
            "claude-chat-export=scripts.export_chat:main",
            "claude-chat-interactive=scripts.interactive:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)