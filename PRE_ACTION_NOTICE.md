# 首次 Actions 前的说明（V6）

这个 ZIP 是“仓库模板 + 选择矩阵 + 构建器”，不会把本地无法联网生成的空规则伪装成正式产物。

因此 V6 初始包中：

- 不再预置一整套 `rules/*.list` 空文件；
- 不再预置假的 `dist/RuleSnippet.conf`；
- `README.md` 与 `docs/index.html` 只显示“等待第一次成功 Actions 构建”；
- 真正规则必须由 GitHub Actions 联网拉取上游后生成。

第一次运行 `Sync and Build Surge Rules` 会：

1. 拉取所有 active 上游（瞬时失败自动重试）；
2. 对 V2Fly `include:` 依赖继续拉取，缺失时直接失败，不静默降级；
3. 检查每个 active 上游至少能解析出 1 条受支持的 Surge 规则；
4. 在源健康检查全部通过后，清空旧的 `rules/`、`dist/`、`docs/` 生成物；
5. 重新生成 candidates、active rules、`RuleSnippet.conf`、README 和 Pages；
6. 检查 48 个 active 服务全部非空；
7. 校验通过后才 commit 并部署 Pages。

所以 V6 中，**成功（绿色）的 Actions 不可能再发布“只有 iFAST，其他全部 empty”的页面**。如果任何远程源或转换出现问题，Workflow 会红灯，并在日志中指出具体 source/service。
