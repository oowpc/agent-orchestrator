# Coding Rules

本文件用于目标项目仓库，说明 Agent 修改代码时必须遵守的规则。

## 基本原则

1. 每次只解决一个明确任务。
2. 不要顺手改无关代码。
3. 不要大规模重构，除非任务明确要求。
4. 不要删除文件，除非用户明确确认。
5. 不要提交密钥、token、`.env`、私钥文件。
6. 修改公共接口时必须同步更新文档和测试。

## 分支原则

- 默认从 `main` 创建功能分支。
- 分支名建议：
  - `agent/T001-short-title`
  - `fix/T002-short-title`
  - `docs/T003-short-title`
- 默认创建 Pull Request，不直接提交主分支。

## 提交信息规范

建议格式：

```text
feat: add data quality checks
fix: handle empty uploaded file
docs: update setup guide
test: add upload validation tests
chore: update project config
```

## 测试要求

代码变更必须说明：

- 运行了哪些测试
- 测试是否通过
- 没有运行测试的原因

## 输出要求

Agent 完成任务后必须输出：

```markdown
## 完成内容

## 修改文件

## 测试结果

## 风险与限制

## 建议下一步
```
