# Test Rules

本文件用于目标项目仓库，说明 Tester Agent 和 Worker Agent 如何处理测试。

## 测试优先级

优先覆盖：

1. 核心业务逻辑
2. 边界输入
3. 错误输入
4. 回归场景
5. 安全相关场景

## 常见测试类型

- 单元测试
- 接口测试
- 集成测试
- 回归测试
- 大文件测试
- 脏数据测试
- 权限测试

## 测试命令

测试命令以 `.agents/project.yaml` 中的 `commands` 为准。

示例：

```yaml
commands:
  test:
    - pytest
  lint:
    - ruff check .
  frontend_test:
    - npm test
```

## Docker 沙箱原则

后续自动执行测试时，应遵守：

- 默认关闭网络
- 限制 CPU 和内存
- 限制运行时间
- 不挂载密钥目录
- 不读取 `.env`
- 在临时副本中执行

## 测试报告格式

```markdown
## 测试命令

## 测试结果

## 失败日志摘要

## 可能原因

## 修复建议
```
