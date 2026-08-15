---
name: competitive-analysis-report-v1
description: 用于创建竞品分析、对标分析、行业/产品竞品报告、采购选型报告、功能体验拆解、商业化定价分析、增长运营分析等任务。Use when the user asks for competitive analysis, competitor report, product comparison, market/player comparison, benchmarking, or wants Codex to first clarify goals, competitors, dimensions, output format, then produce a structured report with sources, matrices, recommendations, Markdown/HTML/PPT-outline outputs.
---

# 竞品分析报告

这个 skill 用于把“帮我做竞品分析”变成可执行工作流：先澄清需求，再输出分析任务卡和报告框架，用户确认后才开始查证、分析和生成报告。

## 核心规则

- 不要在信息不足时直接生成正式报告。
- 每次只问 1 个关键问题；如果必须合并，最多 3 个短问题。
- 优先给 A/B/C/D 选项，必要时允许多选。
- 用户已在原始需求中说明的信息，跳过，不重复提问。
- 不要把“分析目标”“阅读对象”“输出形式”“排版风格”混成一个问题。
- 用户回复字母后，自动识别选择并进入下一步。
- 如果用户选择依赖额外信息的选项但没提供内容，继续追问该内容。
- 所有必要问题问完后，先汇总成“分析任务卡”。
- 任务卡确认后，先输出“报告框架”。
- 用户确认框架后，才正式查资料、分析和生成产出。
- 如果用户要求修改框架，先改框架，不要直接开始报告。
- 默认联网查证现代产品、公司、价格、功能、市场数据、政策、AI 能力和行业动态；只有用户明确说不要联网或只基于材料时才不联网。
- 关键结论要有证据来源。优先使用官网、帮助中心、价格页、公告、财报、开发者文档、官方案例、应用商店、权威报告等来源。

## 默认执行流程

1. 读取 `references/question-flow.md`，按用户已提供的信息跳过对应问题。
2. 读取 `references/handbook-method.md`，使用其中的方法论组织分析。
3. 根据用户选择的分析目标，按需读取 `references/scenario-prompts.md`。
4. 根据输出形式和篇幅，按需读取 `references/report-templates.md`。
5. 如果用户选择 HTML 报告，读取 `references/html-style-presets.md`，并使用 `assets/` 下的模板。
6. 汇总分析任务卡，等待用户确认。
7. 输出报告框架，等待用户确认。
8. 正式查证和生成报告。
9. 若生成 HTML，可使用 `scripts/build_html_report.py` 将 Markdown 转为自包含 HTML；脚本只依赖 Python 标准库。

## 资料使用

- 默认读取 `references/handbook-method.md`，这是从竞品分析入门手册提炼出的可执行规则。
- 只有需要查原文细节时，才读取 `references/source-handbook-full.md`。
- 不强制依赖 `beautiful-html-templates`。默认使用本 skill 内置 HTML 模板；如果用户明确要求更强视觉设计，且环境里可用，再将其作为可选增强。

## 输出要求

正式报告应至少包含：

- 摘要结论：3-7 条关键发现和建议。
- 分析任务卡：目标、对象、范围、维度、口径、输出形式。
- 竞品选择理由：直接竞品、间接竞品、替代方案、潜在竞品。
- 对比分析：按目标选择维度，不堆无关表格。
- 关键洞察：说明事实、原因、机会、风险。
- 行动建议：做什么、不做什么、优先级、下一步。
- 来源列表：列出使用的主要来源和访问口径。

产品/体验类报告还应包含：

- 核心功能矩阵。
- 关键任务路径对比。
- 体验问题清单。
- 差异化功能总结。
- Must / Should / Could 优先级建议。

商业化类报告还应包含：

- 套餐和价格对比。
- 免费到付费边界。
- 权益设计和付费触发点。
- 定价建议和风险。

增长类报告还应包含：

- 漏斗拆解。
- 渠道和内容打法。
- 激活、留存、转化、推荐机制。
- 增长实验清单。

## 交付文件

如果需要生成本地文件，优先写到当前工作区的 `output/` 目录：

- Markdown：`output/<topic>-competitive-analysis.md`
- HTML：`output/<topic>-competitive-analysis.html`

不要把任何密码、API key、内部账号、私有客户数据写入公开报告或准备上传 GitHub 的文件。
