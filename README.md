# AI PR Review Assistant

智能 PR 代码评审工具，基于智谱 GLM-4-Flash 实现真实代码分析。

## 功能

- 输入 GitHub PR 链接，自动获取代码变更
- 生成变更总结（中文）
- 识别风险代码，带置信度（0-100%）和严重度等级
- 风险分级：P0（必须修复）、P1（建议修复）、P2（可选优化）
- 风险定位：显示具体文件名和行号
- 一键复制为 GitHub 评论
- PR 摘要卡片：文件数、新增/删除行数、风险分布
- 历史记录 SQLite 存储，可追溯

## 技术架构

- 后端：FastAPI + SQLite
- 前端：原生 HTML/CSS/JS
- AI：智谱 GLM-4-Flash（四层降级：DeepSeek → 智谱 → Ollama → 模拟数据）

## 模型选择

- 智谱 GLM-4-Flash：永久免费，当前主用
- DeepSeek：代码理解强，已预留接口
- Ollama：本地部署，数据安全

## 上下文获取

用户输入 PR URL → 解析 owner/repo/number → 调用 GitHub API 获取 diff → 发送 LLM 分析 → 返回结构化结果

## 误报控制

- 每条风险带置信度
- 颜色编码：90%+红(高危)、70-89%橙(中等)、50-69%黄(低风险)
- 每条风险带判断依据（reasoning）
- P0/P1/P2 分级，P0 高风险强制关注

## 使用方式

```bash
# 启动后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# 打开前端
双击 frontend/index.html

项目结构
frontend/     # 前端页面
backend/      # FastAPI 后端
database/     # SQLite 数据库

未来扩展
支持 GitLab、Gitee
一键评论到 GitHub PR
自定义规则配置
PR 质量评分

参赛信息
XEngineer 新工科计划 | 题目三：AI PR Review 助手 | 2026.05.29 - 2026.05.31

链接
GitHub：https://github.com/pan-522401/ai-pr-review-assistant

演示视频：待补充
