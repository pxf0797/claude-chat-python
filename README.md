# Claude Chat Manager - Python Edition

一个用Python实现的Claude Code历史聊天记录查看与导出工具。

## ✨ 功能特性

### 🔍 查看功能
- **查看会话列表**：显示所有历史会话的基本信息（时间、标题、项目）
- **查看会话详情**：展示单个会话的完整对话内容
- **交互式浏览器**：支持搜索和筛选的交互式界面

### 📤 导出功能
- **导出为Markdown**：将会话转换为格式化的Markdown文件
- **多种导出格式**：支持基础版和增强版导出格式
- **批量导出**：支持按日期范围或会话数量批量导出
- **智能分类**：自动按日期、项目组织文件

### 🛠️ 工具集
- **完整命令行界面**：支持list、view、export、stats等命令
- **独立脚本**：提供快速查看和导出脚本
- **配置管理**：支持环境变量和配置文件

## 📦 安装

### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/xfpan/claude-chat-python.git
cd claude-chat-python

# 安装依赖（Python标准库，无需额外安装）
# 确保Python 3.8+已安装

# 安装为可执行包（可选）
pip install -e .
```

### 直接使用

```bash
# 直接运行
python -m claude_chat.cli --help

# 或使用提供的脚本
python scripts/view_sessions.py --limit 10
```

## 🚀 快速开始

### 1. 查看会话列表

```bash
# 列出最近20个会话
python -m claude_chat.cli list

# 列出最近50个会话
python -m claude_chat.cli list -l 50

# 使用独立脚本
python scripts/view_sessions.py --limit 30 --format table
```

### 2. 查看会话详情

```bash
# 查看指定会话
python -m claude_chat.cli view --id <session_id>

# 查看会话并包含思考过程
python -m claude_chat.cli view --id <session_id> --include-thinking
```

### 3. 导出会话

```bash
# 导出单个会话
python -m claude_chat.cli export --id <session_id> --output-dir ./my-chats

# 导出最近5个会话
python -m claude_chat.cli export --recent 5

# 导出所有会话（谨慎使用）
python -m claude_chat.cli export --all

# 导出增强格式（推荐）
python -m claude_chat.cli export --recent 10 --format enhanced --include-thinking
```

### 4. 交互式界面

```bash
# 启动交互式浏览器
python scripts/interactive.py

# 在交互式界面中：
#   list 10      # 列出10个会话
#   view 3       # 查看第3个会话
#   search python # 搜索包含python的会话
#   export       # 导出当前会话
#   stats        # 查看统计信息
#   exit         # 退出
```

### 5. 批量导出脚本

```bash
# 导出今天的会话
python scripts/export_chat.py --date $(date "+%Y-%m-%d")

# 导出日期范围
python scripts/export_chat.py --date-range 2024-01-01 2024-01-31

# 干运行模式（预览）
python scripts/export_chat.py --recent 5 --dry-run
```

## 📁 项目结构

```
claude-chat-python/
├── claude_chat/           # 主包
│   ├── __init__.py
│   ├── core.py           # 数据模型 (Message, Conversation)
│   ├── parser.py         # JSONL文件解析器
│   ├── exporter.py       # Markdown导出器
│   ├── cli.py           # 命令行接口
│   └── utils.py         # 工具函数
├── scripts/              # 独立脚本
│   ├── view_sessions.py # 查看会话脚本
│   ├── export_chat.py   # 导出脚本
│   └── interactive.py   # 交互式查看脚本
├── config.py            # 配置文件
├── requirements.txt     # 依赖列表
├── README.md           # 使用说明
└── examples/           # 使用示例
```

## ⚙️ 配置

### 环境变量

```bash
# Claude数据目录
export CLAUDE_DIR="$HOME/.claude"

# 输出目录
export CLAUDE_OUTPUT_DIR="./claude-chats"

# 导出格式 (basic 或 enhanced)
export CLAUDE_EXPORT_FORMAT="enhanced"

# 是否包含思考过程
export CLAUDE_INCLUDE_THINKING="true"

# 默认显示数量
export CLAUDE_LIMIT=20
```

### 命令行参数

所有配置都可以通过命令行参数覆盖：

```bash
python -m claude_chat.cli list --claude-dir ~/.claude --limit 50
python -m claude_chat.cli export --output-dir ./exports --format basic
```

## 📊 导出格式

### 基础格式
包含基本Frontmatter和对话内容，适合简单查看。

### 增强格式（默认）
包含丰富的元数据、标签系统、统计信息和美观的排版，适合导入到Obsidian等双链笔记工具。

**增强格式特性：**
- 完整的Frontmatter元数据
- 对话摘要框
- 自动标签提取
- 时间线和序号标记
- 相关链接生成
- 支持思考过程显示

## 🔧 开发

### 运行测试

```bash
# 运行基本功能测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/test_parser.py
```

### 代码规范

```bash
# 格式化代码
black claude_chat/ scripts/

# 排序导入
isort claude_chat/ scripts/

# 类型检查
mypy claude_chat/
```

### 添加新功能

1. 在`claude_chat/`包中添加新模块
2. 更新`cli.py`添加新命令
3. 添加相应的脚本文件到`scripts/`
4. 更新文档和测试

## 📝 示例

### 导出文件示例

```markdown
---
id: 3e0c354e-03a6-4080-b199-41b488a1d8d4
title: 如何管理claude code的历史聊天记录
date: 2024-01-15
time: 14:48:22
week: 2024-W03
project: /Users/xfpan/claude
duration: 125s
message_count: 12
tags: ["claude/conversation", "date/2024-01-15", "week/2024-W03", "claude-code"]
---

# 💬 如何管理claude code的历史聊天记录

**会话ID**: `3e0c354e-03a6-4080-b199-41b488a1d8d4`
**时间**: 2024-01-15 14:48:22
**持续时间**: 125秒
**消息数量**: 12 (👤6 | 🤖6)

## 👤 用户 (1)
<small>14:48:22</small>

如何管理claude code的历史聊天记录

---

## 🤖 Claude (1)
<small>14:48:30 · claude-3-opus-20240229</small>

我已经为您创建了一个完整的Claude Code聊天记录管理方案...
```

## 🤝 贡献

欢迎提交Issue和Pull Request！

### 开发流程
1. Fork本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

### 代码规范
- 使用Black进行代码格式化
- 使用isort排序导入
- 添加类型注解
- 编写文档字符串

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Claude Code](https://claude.com/claude-code) - 优秀的AI编程助手
- [Obsidian](https://obsidian.md/) - 强大的双链笔记工具
- 所有贡献者和用户

## 📞 支持与反馈

- **问题报告**: [GitHub Issues](https://github.com/xfpan/claude-chat-python/issues)
- **功能建议**: [GitHub Discussions](https://github.com/xfpan/claude-chat-python/discussions)
- **文档改进**: 提交Pull Request

---

**提示**: 详细的设计方案请查看 [Python-Claude-Code-History-Management-Scheme.md](../Python-Claude-Code-History-Management-Scheme.md)