# Linux ARM KVM邮件列表自动化分析系统

自动化分析Linux ARM KVM邮件列表，支持定期抓取、解析、分析和可视化邮件线程。

## 核心功能

- **自动仓库管理**: 克隆和增量更新lore.kernel.org邮件仓库
- **邮件解析**: 解析邮件内容，提取补丁信息、回复关系等
- **Lore链接生成**: 自动生成可点击的lore.kernel.org链接
- **树形结构构建**: 构建邮件线程的树形结构
- **智能内容分割**: 根据内容复杂度进行智能分块
- **AI分析**: 使用多种AI模型进行技术内容分析
- **多格式报告**: 生成JSON、ASCII、HTML等多种格式的报告

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repo-url> arm-kvm-analyzer
cd arm-kvm-analyzer

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置你的API密钥
```

### 2. 分步测试

```bash
# 测试仓库管理
python analyze.py test repo

# 测试邮件解析
python analyze.py test email

# 测试lore链接生成
python analyze.py test lore-gen

# 测试lore链接验证（需要网络）
python analyze.py test lore-val

# 测试树形结构构建
python analyze.py test tree

# 测试内容分割
python analyze.py test chunk

# 测试AI分析（需要API密钥）
python analyze.py test ai

# 运行所有测试
python analyze.py test all
```

### 3. 完整流程测试

```bash
# 测试完整流程（最近3天的邮件）
python analyze.py test full
```

### 4. 正式运行

```bash
# 分析最近100个commits
python analyze.py --mode recent --limit 100 --debug

# 分析指定时间范围
python analyze.py --mode date_range --since 2025-01-01 --until 2025-01-15 --debug

# 使用不同的AI提供商
python analyze.py --provider gemini --limit 50 --debug

# 自定义输出目录
python analyze.py --output my_results --limit 30 --debug
```

## 项目结构

```
arm-kvm-analyzer/
├── analyze.py              # 主程序和CLI入口
├── models.py               # 数据模型定义
├── repository.py           # Git仓库管理
├── email_parser.py         # 邮件解析
├── lore_links.py          # Lore链接生成和验证
├── tree_builder.py        # 树形结构构建
├── content_chunker.py     # 智能内容分割
├── ai_analyzer.py         # AI分析接口
├── report_generator.py    # 报告生成
├── requirements.txt       # Python依赖
├── .env.example          # 环境变量模板
└── results/              # 输出目录
    └── YYYY-MM-DD/       # 按日期组织的结果
        ├── arm_kvm_analysis.json
        ├── weekly_report.txt
        ├── interactive_report.html
        ├── statistics.json
        └── lore_links.json
```

## 输出说明

### JSON报告 (`arm_kvm_analysis.json`)
包含完整的结构化数据，包括：
- 邮件树形结构
- AI分析结果
- Lore链接验证状态
- 补丁系列信息

### ASCII报告 (`weekly_report.txt`)
人类可读的文本报告，包括：
- 线程树形可视化
- 可点击的Lore链接
- AI分析摘要
- 统计信息

### HTML报告 (`interactive_report.html`)
交互式网页报告，支持：
- 可点击的Lore链接
- 展开/折叠的线程结构
- 美化的AI分析结果

### 统计报告 (`statistics.json`)
详细的统计信息，包括：
- 消息类型分布
- 贡献者活动分析
- 内容分块统计
- Lore验证成功率

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `OPENAI_API_KEY` | OpenAI API密钥 | - |
| `GEMINI_API_KEY` | Google Gemini API密钥 | - |
| `AI_PROVIDER` | 默认AI提供商 | openai |
| `MAX_TOKENS_PER_CHUNK` | 每个分块的最大token数 | 8000 |
| `ENABLE_LORE_VALIDATION` | 是否启用Lore验证 | true |

## API密钥获取

### OpenAI
1. 访问 [OpenAI API](https://openai.com/api/)
2. 创建账户并获取API密钥
3. 设置环境变量：`export OPENAI_API_KEY="your-key"`

### Google Gemini
1. 访问 [Google AI Studio](https://makersuite.google.com/app/apikey)
2. 创建API密钥
3. 设置环境变量：`export GEMINI_API_KEY="your-key"`

## 常见问题

### Q: 仓库克隆失败
A: 检查网络连接，确保可以访问lore.kernel.org

### Q: AI分析失败
A: 检查API密钥是否正确设置，确认账户有足够的额度

### Q: Lore链接验证失败
A: 这是正常的，部分邮件可能在lore上不可访问，系统会记录验证状态

### Q: 内存不足
A: 减少`--limit`参数的值，或增加`MAX_TOKENS_PER_CHUNK`以减少分块数量

## 开发和贡献

### 添加新的AI提供商
1. 在`ai_analyzer.py`中继承`AIProvider`类
2. 实现`analyze_chunk`和`merge_analyses`方法
3. 在`AIAnalyzer._init_provider`中添加新提供商

### 添加新的报告格式
1. 在`report_generator.py`中添加新的生成方法
2. 在`generate_reports`中调用新方法

### 自定义邮件过滤
修改`email_parser.py`中的解析逻辑，添加自定义过滤条件。

## 许可证

MIT License

## 联系方式

如有问题请提交Issue或Pull Request。