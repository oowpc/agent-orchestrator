# 开发路线图

本项目建议按照“先可控、再自动化”的顺序开发。

## 阶段 0：项目初始化

目标：完成仓库基础准备。

- [x] 创建 README
- [x] 创建架构文档
- [x] 创建项目配置模板
- [x] 创建 Agent 角色说明
- [x] 创建环境变量模板

## 阶段 1：命令行 Planner MVP

目标：输入一个需求，自动生成任务拆分和风险分析。

功能：

- [ ] CLI 接收用户需求
- [ ] Planner Agent 输出结构化任务列表
- [ ] 输出每个任务的验收标准
- [ ] 输出风险分析
- [ ] 生成 Markdown 计划报告

建议命令：

```bash
python -m backend.main "给报表 Agent 增加数据质量检查功能"
```

输出：

```text
outputs/plans/plan_xxx.md
```

## 阶段 2：任务状态管理

目标：让任务可以被保存、追踪和流转。

功能：

- [ ] 定义 Task 数据模型
- [ ] 使用 SQLite 保存任务
- [ ] 支持任务状态更新
- [ ] 支持任务依赖关系
- [ ] 支持查看任务列表

状态：

```text
pending / running / reviewing / testing / needs_fix / done / failed / blocked
```

## 阶段 3：Agent 执行链路

目标：让不同 Agent 按流程处理任务。

功能：

- [ ] Worker Agent 根据任务生成执行方案
- [ ] Reviewer Agent 审查 Worker 输出
- [ ] Reporter Agent 汇总任务结果
- [ ] 支持 needs_fix 返工流程

第一版 Worker 可以只生成文字方案，不直接改代码。

## 阶段 4：目标项目接入

目标：支持读取实际项目仓库里的 `.agents/project.yaml`。

功能：

- [ ] 定义项目配置规范
- [ ] 读取本地项目路径
- [ ] 读取 GitHub 仓库信息
- [ ] 根据项目技术栈选择 Agent
- [ ] 根据项目测试命令生成任务计划

## 阶段 5：GitHub Issues 派单

目标：总控系统可以把任务自动变成 GitHub Issues。

功能：

- [ ] GitHub API 配置
- [ ] 创建 Issue
- [ ] Issue 模板
- [ ] 按 Agent 类型添加标签
- [ ] 在 Issue 中写清验收标准

示例标签：

```text
agent:backend
agent:frontend
agent:test
agent:review
priority:high
status:planned
```

## 阶段 6：代码执行与测试

目标：接入代码执行能力，但必须放在安全环境中。

功能：

- [ ] Docker 沙箱
- [ ] 限制运行时间
- [ ] 限制 CPU / 内存
- [ ] 运行 pytest / npm test
- [ ] 收集测试日志
- [ ] 自动生成测试报告

## 阶段 7：PR 工作流

目标：让 Orchestrator 可以创建分支和 PR。

功能：

- [ ] 创建功能分支
- [ ] 提交 Agent 修改
- [ ] 创建 Draft PR
- [ ] Reviewer Agent 评论 PR
- [ ] Tester Agent 汇总测试结果
- [ ] 用户确认后合并

原则：

> 默认只创建 PR，不自动合并。

## 阶段 8：Web 控制台

目标：把多 Agent 流程可视化。

页面：

- [ ] 项目列表
- [ ] 任务看板
- [ ] 任务详情
- [ ] Agent 运行日志
- [ ] Review 结果
- [ ] 测试结果
- [ ] 用户确认按钮

## 阶段 9：多项目复用

目标：同一个 Orchestrator 可以服务多个项目。

功能：

- [ ] 项目注册
- [ ] 项目配置扫描
- [ ] 多项目任务隔离
- [ ] 项目级权限控制
- [ ] 项目级成本统计

## 阶段 10：高级能力

可选增强：

- [ ] 多模型对比
- [ ] Agent 评分系统
- [ ] 成本预算限制
- [ ] Prompt 版本管理
- [ ] 自动生成周报
- [ ] Slack / 飞书通知
- [ ] 长任务恢复
- [ ] 失败重试策略

## 当前优先级建议

最适合现在做的最小版本：

1. Planner Agent
2. Task 数据结构
3. Markdown 报告生成
4. 项目配置模板
5. GitHub Issue 模板

不要一开始就做自动改代码。先把任务拆解、审查和报告流程跑通。
