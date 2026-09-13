---
name: check-commit
description: 校验 Git 提交信息是否符合 GoldSight 项目提交规范。格式要求：<type>: <description>，type 为 feat/fix/docs/style/refactor/test/chore，description 使用中文且不超过 72 字符。在用户执行 git commit 前、请求校验提交信息、或 /check-commit 时触发。
---

# 提交信息格式检查

## 使用方式

通过 `/check-commit <提交信息>` 调用，或直接传入待校验的提交信息。

## 校验规则

提交信息必须符合以下格式：

```
<type>: <description>
```

### Type 校验

type 必须是以下值之一（小写英文）：

| Type | 用途 |
|------|------|
| `feat` | 新功能 |
| `fix` | 修复缺陷 |
| `docs` | 文档变更 |
| `style` | 代码格式 |
| `refactor` | 代码重构 |
| `test` | 测试相关 |
| `chore` | 构建/工具 |

### Description 校验

1. 不能为空
2. 使用中文描述
3. 不超过 72 个字符
4. 首字母不大写，末尾不加句号

## 校验流程

1. 解析提交信息，提取 type 和 description
2. 检查格式是否为 `<type>: <description>`
3. 验证 type 是否在允许列表中
4. 验证 description 非空且长度 ≤ 72
5. 输出校验结果

## 输出格式

**通过时：**
```
✅ 提交信息合规
   类型: feat
   描述: 添加黄金价格监控模块
```

**不通过时：**
```
❌ 提交信息不合规
   问题: type "update" 不在允许列表中
   允许值: feat / fix / docs / style / refactor / test / chore
   建议: feat: 添加XXX功能
```

## 示例

```
/check-commit feat: 添加用户认证模块
→ ✅ 合规

/check-commit update
→ ❌ 缺少 type 前缀，建议: feat: update

/check-commit feat: 添加了一个非常长的描述信息超过七十二个字符的限制内容
→ ❌ description 超过 72 字符（当前 35 字符）
```
