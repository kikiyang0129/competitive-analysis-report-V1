# Competitive Analysis Report V1
[中文说明](README.md)
A Codex Skill for creating AI-powered competitive analysis, product benchmarking, market research, competitor comparison, UX analysis, and multi-format reports.
This skill turns a vague request like “help me make a competitive analysis report” into a structured workflow: clarify the brief, create an analysis task card, propose a report framework, then research, compare, and generate the final deliverable after user confirmation.
## What It Is For
- Competitive analysis reports
- Product benchmarking
- Feature comparison
- UX and user journey analysis
- Market and player comparison
- Procurement/vendor selection reports
- Pricing and monetization analysis
- Growth and lifecycle analysis
- AI product and capability comparison
## Key Features
- Clarify before writing: asks about industry/product/category, analysis goal, audience, competitor scope, dimensions, output format, length, and visual style.
- Multiple-choice intake flow: uses A/B/C/D options whenever possible to reduce user effort.
- Method-driven analysis: includes competitive analysis methods, workflow rules, reusable dimensions, and scenario-specific prompts.
- Flexible competitor scope: supports direct competitors, indirect competitors, substitutes, and potential competitors.
- Multiple analysis scenarios: strategy, product/UX, pricing, growth, procurement, AI capability comparison, and more.
- Multi-format output: Markdown, HTML reports, PPT outlines, and competitor comparison tables.
- Built-in HTML visualization: creates insight cards, heatmaps, radar charts, quadrant charts, task flows, and priority boards without requiring extra template skills.
## Installation
Install with the local Codex skill installer:
```bash
python ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py --repo kikiyang0129/competitive-analysis-report-V1 --path . --name competitive-analysis-report-v1
```
Windows example:
```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py" --repo kikiyang0129/competitive-analysis-report-V1 --path . --name competitive-analysis-report-v1
```
The skill will be available from the next Codex turn.
If a skill with the same name already exists locally, remove the old folder first or install with another name.
## Usage Examples
You can say:
```text
I want to create a competitive analysis report for the EV charging station market.
```
Or be more specific:
```text
Use the competitive-analysis-report-v1 skill to create a competitive analysis report for office collaboration products, focusing on product planning and UX optimization.
```
Codex will ask the necessary questions first, such as:
- What industry, product, or category should be analyzed?
- What is the goal of the analysis?
- Who is the audience?
- Should competitors be user-defined or selected by Codex?
- Which dimensions matter most?
- Should the output be Markdown, HTML, a PPT outline, or a competitor comparison table?
## Built-In Deliverables
A standard report usually includes:
- Executive summary
- Analysis task card
- Competitor selection rationale
- Core feature matrix
- Key task flow comparison
- UX issue list
- Differentiated feature summary
- Must / Should / Could priority recommendations
- Source list
- HTML output automatically enhances summary cards, score heatmaps, competitor radar charts, quadrant charts, score rankings, task flows, and priority boards.
The structure adapts by scenario. For example, pricing analysis adds plans, pricing tiers, value boundaries, and monetization recommendations. Growth analysis adds funnel breakdowns, channels, activation, retention, conversion, referrals, and experiment ideas.
## File Structure
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
## Dependencies
This skill does not require `beautiful-html-templates`.
By default, it uses built-in HTML templates to generate structured, formatted reports with visual charts. If other visual template skills are installed, they can be used as optional enhancements for specific tasks.
`scripts/build_html_report.py` only depends on the Python standard library.
## Notes
- The skill defaults to web verification for modern products, companies, pricing, features, market data, policies, AI capabilities, and industry updates. If you only want to analyze provided materials, say so in the task.
- Do not include passwords, API keys, internal accounts, or private customer data in public reports or files prepared for GitHub.
- Competitive analysis conclusions should include sources whenever possible, prioritizing official websites, help centers, pricing pages, announcements, financial reports, developer docs, official cases, and authoritative reports.
## License
MIT
