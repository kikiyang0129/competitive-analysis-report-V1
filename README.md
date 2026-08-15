# Competitive Analysis Report V1
[English](README_EN.md)
一个用于生成竞品分析、产品对标、市场研究和体验分析报告的 Codex Skill。
它会先通过结构化问题澄清需求，再生成分析任务卡和报告框架，用户确认后再开始查证资料、对比分析并输出报告。
## 适合做什么
- 竞品分析报告
- 产品功能对标
- 用户体验分析
- 市场玩家对比
- 采购选型报告
- 商业化与定价分析
- 增长运营分析
- AI 产品/功能能力对比
## 核心能力
- 先问问题，再写报告：自动澄清行业/产品/赛道、分析目标、阅读对象、竞品名单、分析维度、输出形式和排版风格。
- 选择题式需求收集：优先提供 A/B/C/D 选项，降低用户表达成本。
- 基于方法论产出：内置竞品分析入门方法、分析流程、维度框架和多场景提示词。
- 支持多种竞品范围：直接竞品、间接竞品、替代方案、潜在竞品。
- 支持多种分析场景：战略机会、产品功能与体验、商业化定价、增长运营、采购选型、AI 能力对比等。
- 支持多种输出格式：Markdown、HTML 报告、PPT 大纲和竞品对比表格。
- 支持 HTML 可视化排版：内置摘要卡片、热力矩阵、雷达图、四象限、任务路径和优先级看板。
## 安装
在 Codex 中使用本地 skill installer 安装：
```bash
python ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py --repo kikiyang0129/competitive-analysis-report-V1 --path . --name competitive-analysis-report-v1
```
Windows 示例：
```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py" --repo kikiyang0129/competitive-analysis-report-V1 --path . --name competitive-analysis-report-v1
```
安装后，下一轮对话即可使用。
如果本地已经存在同名 skill，需要先删除旧目录或换一个安装名称。
## 使用示例
你可以直接说：
```text
我要做一份新能源汽车充电桩行业的竞品分析报告。
```
也可以更明确地指定：
```text
请使用 competitive-analysis-report-v1 skill，帮我做一份办公协作产品的竞品分析报告，重点分析功能规划和用户体验优化。
```
Codex 会先追问必要信息，例如：
- 分析对象是什么行业、产品或赛道？
- 这份报告用于什么场景？
- 阅读对象是谁？
- 竞品名单是用户指定，还是由 Codex 辅助界定？
- 重点分析哪些维度？
- 最终输出成 Markdown、HTML、PPT 大纲还是竞品对比表格？
## 内置输出
正式报告通常包含：
- 摘要结论
- 分析任务卡
- 竞品选择理由
- 核心功能矩阵
- 关键任务路径对比
- 体验问题清单
- 差异化功能总结
- Must / Should / Could 优先级建议
- 资料来源列表
- HTML 版本会自动增强摘要卡片、评分热力表、竞品能力雷达图、定位四象限、综合评分排行、任务流程和优先级看板。
不同场景会自动调整结构，例如商业化分析会增加价格/套餐/权益边界，增长分析会增加漏斗、渠道、激活、留存、转化和增长实验。
## 文件结构
```text
competitive-analysis-report-V1/
├── SKILL.md
├── assets/
│   └── html-report-template.html
├── references/
│   ├── handbook-method.md
│   ├── html-style-presets.md
│   ├── question-flow.md
│   ├── report-templates.md
│   ├── scenario-prompts.md
│   └── source-handbook-full.md
└── scripts/
    └── build_html_report.py
```
## 依赖说明
这个 skill 不要求用户额外安装 `beautiful-html-templates`。
默认会使用内置 HTML 模板生成有结构、有排版、有可视化图表的报告。如果用户已经安装其他视觉模板类 skill，也可以在具体任务中作为增强使用。
`scripts/build_html_report.py` 只依赖 Python 标准库。
## 注意事项
- 默认会联网查证现代产品、公司、价格、功能、市场数据、政策、AI 能力和行业动态；如果只想基于指定材料分析，请在任务中说明。
- 不要把密码、API key、内部账号、私有客户数据写入公开报告或上传到公开仓库。
- 竞品分析结论应尽量附来源，优先使用官网、帮助中心、价格页、公告、财报、开发者文档、官方案例和权威报告。
## License
MIT
