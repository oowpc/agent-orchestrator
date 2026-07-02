# 使用说明

当前项目已经具备一个最小命令行 Planner MVP。

## 1. 克隆仓库

```bash
git clone https://github.com/oowpc/agent-orchestrator.git
cd agent-orchestrator
```

## 2. 创建虚拟环境

```bash
python -m venv .venv
```

Windows PowerShell：

```powershell
.venv\Scripts\Activate.ps1
```

Linux / macOS：

```bash
source .venv/bin/activate
```

## 3. 安装依赖

```bash
pip install -r requirements.txt
```

## 4. 先用 mock 模式运行

不配置 API Key 时，系统会自动使用 mock 模式。

```bash
python -m backend.main "给报表 Agent 增加数据质量检查功能" --print
```

输出文件会保存到：

```text
outputs/plans/
```

## 5. 接入真实模型

复制环境变量模板：

```bash
cp .env.example .env
```

然后修改：

```env
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=你的 API Key
LLM_MODEL=你的模型名称
```

如果使用其他 OpenAI-compatible 平台，只需要改：

```env
LLM_BASE_URL=平台的 base url
LLM_API_KEY=平台的 key
LLM_MODEL=模型名
```

## 6. 常用命令

生成任务计划：

```bash
python -m backend.main "我要给项目增加登录功能"
```

指定项目名称：

```bash
python -m backend.main "增加 Excel 上传功能" --project report-agent
```

同时打印报告：

```bash
python -m backend.main "增加数据质量检查" --print
```

## 7. 当前能力边界

当前版本只做：

- 需求分析
- 方案选择
- 风险分析
- 任务拆分
- 验收标准生成
- Markdown 报告生成

当前版本不做：

- 自动改代码
- 自动执行 shell 命令
- 自动创建 PR
- 自动合并分支
- 自动部署

这些能力会在后续阶段逐步加入。

## 8. 下一步开发建议

建议继续实现：

1. SQLite 任务保存
2. Task Manager 状态机
3. Reviewer Agent
4. GitHub Issues 自动创建
5. 目标项目 `.agents/project.yaml` 读取
