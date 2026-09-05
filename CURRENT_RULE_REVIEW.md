# 当前 `[Rule]` 审计与调整建议

依据用户上传的 157 行规则整理。原则：先保证匹配语义与泄漏控制，再优化依赖数量；金融例外优先于通用规则。

| 当前项 | 结论 | 建议 |
|---|---|---|
| `api3.branch.io -> 美国` | 删除 | Branch 是跨 App attribution 基础设施，强制整域美国容易把无关 App 带走。只有抓包证明某个金融 App 必须依赖它时，才在该服务专项规则里补。 |
| `coinbase.com -> 美国` 单条 | 太薄 | 移到 `coinbase-us` 服务规则，避免只覆盖网页根域而漏 API/CDN。当前没有找到足够可信的长期专项仓库，先保守提取，后续抓包补齐。 |
| Cloudflare/Google DNS IP 写在最前面 | 顺序不佳 | DoH 域名可以在 non-IP 段；`1.1.1.1/8.8.8.8` 这类 IP 必须放到统一 IP phase，避免提前触发/打断域名分流。 |
| `redpocket.com` 两次 | 重复 | 仅保留一次。 |
| `wise.com,DIRECT` | 覆盖不足 | 改成独立 `wise-direct`，至少同时覆盖 `wise.com` 与历史 `transferwise.com`；保持 DIRECT。 |
| 全局 `UDP/443 -> REJECT-NO-DROP` | 过于粗暴 | 优先改 `[General] block-quic = all-proxy`：代理流量不走 QUIC，但 DIRECT 仍可用 QUIC。比“一刀切所有 UDP/443”副作用小。 |
| `DOMAIN-KEYWORD,jsdelivr.net` | 粒度不合理 | 若目的就是 jsDelivr，使用 `DOMAIN-SUFFIX,jsdelivr.net`；keyword 会扩大匹配语义。 |
| `vercel.app -> Proxy` | 太宽 | 建议换成你的 Sub-Store 具体 hostname；`vercel.app` 是共享平台。仓库模板暂不保留这一条，避免误分流。 |
| Apple `api-ip.list` 与域名规则混在前段 | 结构问题 | 保留 Elysian 细分思路，但构建器自动把它拆到全局 IP phase。 |
| Google = BM + RuleGo Proxy+ | 重叠较多 | 建议改为 v2fly Google 单服务域名库；BM 留作备选，不再叠一个更宽的 `Proxy+` 到 Google。 |
| HoYoverse 三套叠加 | 重叠 | 默认 LM-Firefly 专项；CINGDAAT 与融合版作为候选，由你决定是否为覆盖率付出重复。 |
| PayPal 单独 BM | 不符合新需求 | 并入 Payments-US；Wise 继续单独 DIRECT。 |
| Nintendo/Epic/Steam 全 BM | 可替换 | 默认改 v2fly per-service，排除 `@cn`，BM 只保留候选。 |
| Telegram non-IP/IP/ASN | 保留 Sukka | Telegram 官方 CIDR 由 Sukka 自动生成，结构清楚。 |
| `PROCESS-NAME,Telegram,REJECT-DROP` | **不是错误** | 这是 Sukka 的 macOS fail-closed 隐私思路：前面只允许 Telegram 官方规则，随后拒绝 Telegram 进程其他连接。它是平台/偏好相关项，因此通用片段默认不带；另生成 `RuleSnippet-Mac.conf`。 |
| Streaming `RuleGo !CN + Sukka stream` | 可以保留 | `!CN` 先处理中国流媒体例外，Sukka 负责更广泛流媒体；后续可按实际命中率再去重。 |
| Sukka global/direct/domestic/china | 继续作为骨架 | 这是目前最适合保留的主体层。 |
| WeChat 域名在 China IP 之后 | 结构错误 | 所有 domain/non-IP 必须先于所有 IP/ASN。构建器会自动修正。 |
| `FINAL,Final,dns-failed` | 保留 | 与 DNS 失败兜底设计兼容。 |

## 推荐顺序

1. 你自己的**精确 domain 例外**；
2. 拒绝/广告与服务专项 non-IP；
3. 金融地域例外 non-IP（France / DIRECT / US）；
4. 通用 non-IP（Streaming / Global / Domestic / Direct 等）；
5. 你自己的精确 IP；
6. 服务专项 IP/ASN；
7. China/domestic IP；
8. `LAN,DIRECT`、`GEOIP,CN,DIRECT`、`FINAL,Final,dns-failed`。

构建器强制“所有 non-IP 在所有 IP 之前”。这样 hostname 请求更有机会在本地 DNS 解析之前就完成策略判定，也避免 WeChat/金融域名被早期 IP 分类截走。
