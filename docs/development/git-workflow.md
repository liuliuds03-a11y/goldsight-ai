# GoldSight AI V3.0 - Git 工作流

## 1. 分支策略

项目采用 **main + develop + feature/\*** 分支模型。

| 分支 | 用途 | 保护级别 |
|------|------|---------|
| `main` | 生产稳定版本 | 仅通过 PR 合并 |
| `develop` | 开发集成分支 | 仅通过 PR 合并 |
| `feature/*` | 功能开发 | 自由开发，合并后删除 |
| `hotfix/*` | 紧急修复 | 从 main 创建，修复后合并回 main + develop |

详细规则见 [branch-strategy.md](./branch-strategy.md)。

## 2. 提交规范

所有提交信息必须遵循格式：

```
<type>: <description>
```

可用 type：`feat` / `fix` / `docs` / `style` / `refactor` / `test` / `chore`

详细规则见 [commit-convention.md](./commit-convention.md)。

## 3. 开发工作流

### 3.1 功能开发流程

```
1. 从 develop 创建功能分支
   git checkout develop
   git checkout -b feature/<模块>-<简述>

2. 在功能分支上开发并提交
   git add .
   git commit -m "feat: 添加XXX功能"

3. 同步 develop 最新变更（开发过程中）
   git fetch origin
   git rebase origin/develop

4. 推送功能分支并创建 PR
   git push origin feature/<模块>-<简述>
   → 在 GitHub/GitLab 创建 PR → develop

5. PR 审查通过后合并，删除功能分支
```

### 3.2 版本发布流程

```
1. 确保 develop 分支所有测试通过
2. 从 develop 合并到 main
   git checkout main
   git merge --no-ff develop
3. 打版本标签
   git tag -a v1.0.0 -m "release: v1.0.0 - 初始版本"
4. 推送 main 和标签
   git push origin main
   git push origin v1.0.0
5. 同步回 develop（保持版本同步）
   git checkout develop
   git merge main
```

### 3.3 紧急修复流程

```
1. 从 main 创建 hotfix 分支
   git checkout main
   git checkout -b hotfix/<问题简述>

2. 修复问题并提交
   git commit -m "fix: 修复XXX问题"

3. 合并到 main
   git checkout main
   git merge --no-ff hotfix/<问题简述>

4. 打标签
   git tag -a v1.0.1 -m "fix: v1.0.1 紧急修复"

5. 同步到 develop
   git checkout develop
   git merge main

6. 删除 hotfix 分支
   git branch -d hotfix/<问题简述>
```

## 4. 合并流程

### 4.1 Pull Request 要求

- **标题**：遵循提交规范格式
- **描述**：说明变更内容、影响范围和测试情况
- **审查**：至少一名相关 Agent 审查通过
- **CI**：lint 和测试全部通过
- **验收**：PM Agent 确认功能符合需求

### 4.2 合并策略

- **feature → develop**：使用 `--no-ff` 保留合并记录
- **develop → main**：使用 `--no-ff` 保留合并记录
- **hotfix → main/develop**：使用 `--no-ff` 保留合并记录

```bash
git merge --no-ff feature/<模块>-<简述>
```

## 5. 冲突解决指南

### 5.1 预防冲突

- **频繁同步**：开发过程中定期 rebase develop
- **小步提交**：每个功能点单独提交，减少冲突范围
- **模块分工**：各 Agent 负责独立模块，减少文件级冲突

### 5.2 解决冲突步骤

```bash
# 1. 拉取最新代码，发现冲突
git fetch origin
git rebase origin/develop

# 2. 查看冲突文件
git status

# 3. 手动编辑冲突文件
#    冲突标记：<<<<<<< / ======= / >>>>>>>
#    保留双方有效代码，删除冲突标记

# 4. 标记冲突已解决
git add <冲突文件>

# 5. 继续 rebase
git rebase --continue

# 如果冲突过于复杂，可以中止 rebase 重新规划
git rebase --abort
```

### 5.3 冲突解决原则

1. **理解双方意图**：不要简单删除对方代码
2. **保持功能完整**：确保双方功能都能正常工作
3. **测试验证**：解决冲突后必须运行测试
4. **沟通确认**：不确定时与相关 Agent 沟通

## 6. 禁止操作

以下操作在任何情况下都**不允许**执行：

- ❌ `git push --force`（强制推送）
- ❌ `git reset --hard`（硬重置丢弃提交）
- ❌ 直接推送到 `main` 或 `develop`
- ❌ 删除远程分支（除已合并的 feature 分支）
- ❌ 修改已推送的提交历史
