# 首次 Actions 前的说明

这个 ZIP 是“仓库模板 + 选择矩阵 + 构建器”，不是把 70 多个上游内容永久固化在压缩包里。

本地生成环境无法直接运行批量网络抓取，所以 ZIP 中 `rules/`/`docs/rules/` 的远程来源部分可能只有头注释或为 0 条；**这不是最终规则内容**。上传 GitHub 后第一次运行 `Sync and Build Surge Rules` 会：

1. 拉取所有 active 上游；
2. 写入 `mirror/`；
3. 生成 candidates 和 active rules；
4. 重新生成真正的 `RuleSnippet.conf` / `RuleSnippet-Mac.conf`；
5. 校验后才部署 Pages。

第一次 Actions 如果某个 active 金融上游拉取失败且没有 last-known-good mirror，Workflow 会失败，不会把残缺规则发布成“成功”。这是故意的 fail-safe。
