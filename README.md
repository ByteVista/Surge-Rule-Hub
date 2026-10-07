# Surge Rule Hub（个人分流规则仓库模板）


> **Pipeline package:** V9 canonical-build guard. README sync runs only after `dist/RuleSnippet.conf` has been generated and validated.

> 研究/整理日期：2026-08-21。目标不是“规则越少越好”，而是 **基础层控制负载，金融层优先完整覆盖、固定出口和可审计性**。

这个仓库用于把多个上游规则自动镜像到你自己的仓库，统一转换为 Surge 可用格式，按服务合并/拆分，自动将 **所有 non-IP 规则放在所有 IP/ASN 规则之前**，最后通过 GitHub Pages 发布并生成可直接粘贴的 `[Rule]` 片段。

## 先看结论

- 主体骨架继续使用 **SukkaW/Surge** 是合适的：适合 Reject/CDN/Microsoft/Telegram/Streaming/Download/Global/Direct/Domestic/China IP 等通用骨架。
- 不建议把 blackmatrix7 的“大而全”合集继续当主体；只保留成少数服务的备选小列表。
- 金融采用“**专项源 + 多源融合 + 固定地域策略**”：美国银行、支付、券商、交易所优先覆盖，不为了几十条规则的差异牺牲登录/API/行情域名。
- Wise 始终单独 `DIRECT`；N26 -> `France`；Bybit EU -> `France`；iFAST -> `DIRECT`；其余本仓库金融默认 -> `United States`。
- Moomoo 只保留 US 需求；不再把 Futu HK 当独立服务使用。
- 非 Surge 上游可以使用：Clash classical、V2Fly geosite 文本、Quantumult X/Loon 常见 `HOST/HOST-SUFFIX/IP6-CIDR` 语法会统一转换。
- GitHub Pages 的规则链接本质上需要让 Surge 无认证读取。**私有仓库 != 私有 Pages 内容**。请先看下面的 Pages 说明。

## 目录

- `config/sources.json`：所有上游来源。
- `config/services.json`：每个服务的候选方案、最终 active 选择、策略和排序。
- `config/custom_rules.json`：你原配置中需要保留的本地规则。
- `mirror/`：Actions 拉取的上游原文（last-known-good）。
- `rules/candidates/<service>/`：每个候选方案转换后的 Surge 规则，方便逐项对比。
- `rules/<service>.non_ip.list` / `.ip.list`：当前 active 方案。
- `dist/RuleSnippet.conf`：通用 `[Rule]` 片段。
- `dist/RuleSnippet-Mac.conf`：macOS 可选的 Telegram fail-closed 版。
- `dist/General-Recommended.conf`：建议合并进你现有 `[General]` 的 DNS/QUIC 设置。
- `dist/General-Strict.conf`：更严格的全网络接管版本。
- `UPSTREAM_COMPARISON.md`：各服务候选上游横向比较。
- `CURRENT_RULE_REVIEW.md`：你现有 157 行规则的逐项优化建议。
- `PRIVACY_DNS_WEBRTC.md`：DNS / QUIC / WebRTC 泄漏治理。
- `SOURCE_CATALOG.md`：上游清单、用途与许可/发布限制。

## 上传与启用

1. 在 GitHub 新建仓库（建议 Private），把本 ZIP 解压后的**仓库内容**上传到仓库根目录。**必须确认 `.github/workflows/sync-rules.yml` 也已上传；macOS Finder 默认会隐藏 `.github`。**
   - 最稳妥的方法是使用 `git add -A` / `git push` 上传。
   - 如果只用 GitHub 网页上传，请先看 `SETUP_ACTIONS.md`；根目录另附 `SYNC_RULES_WORKFLOW.yml` 作为可见备份。
2. 打开 `Settings -> Actions -> General`，确保 Actions 可运行且 Workflow 有写权限。
3. 如果你的 GitHub 套餐允许私有仓库使用 Pages：在 `Settings -> Pages` 选择 **GitHub Actions** 作为 Source。
4. 进入 `Actions -> Sync and Build Surge Rules -> Run workflow`，第一次务必手动跑一次。
5. **只有 Actions 全部绿色成功后**再使用 Pages/README 中的规则。V6 起，只要任一 active 上游抓取失败、解析为 0，或任一启用服务最终为 0 条，构建会直接失败，绝不会发布 empty 规则。
6. 将 `dist/General-Recommended.conf` 中的键**合并到已有 `[General]`**，不要创建第二个 `[General]`。

### GitHub Pages 与“私有仓库”的重要区别

GitHub Pages 站点用于给 Surge 拉取远程规则，因此通常必须公开可访问。私有仓库是否能启用 Pages 取决于你的 GitHub 套餐；而且普通 Pages 即使来源仓库是 Private，站点也通常不是“仅自己可访问”。真正的 Private Pages 访问控制主要属于组织/Enterprise 场景。

因此最实用的结构是：**源码/配置仓库 Private + Pages 产物公开**。如果你不希望任何生成规则公开，不要用 Pages；改用你自己的静态托管/CDN，或使用一个支持令牌但 Surge 能稳定访问的分发方式。

## 如何选择每个服务的上游

仓库不会把我的推荐强制锁死。查看所有可选项：

```bash
python3 scripts/select_source.py --list
```

例如把美国银行切到纯 Accademia：

```bash
python3 scripts/select_source.py us-banks accademia
```

把 Moomoo 切到“v2fly + Arthur 共享 Futu/Moomoo 域名（不含大段 IP）”覆盖版：

```bash
python3 scripts/select_source.py moomoo-us coverage-fusion
```

切换后提交 `config/services.json`，下一次 Actions 会自动重建。完整候选理由见 `UPSTREAM_COMPARISON.md`。

## 自动转换规则

当前转换器支持：

- Surge `DOMAIN / DOMAIN-SUFFIX / DOMAIN-KEYWORD / IP-CIDR / IP-CIDR6 / IP-ASN / GEOIP ...`
- Clash classical `payload:`
- V2Fly/domain-list-community：普通域名、`domain:`、`full:`、`keyword:`、递归 `include:`
- Domain-set：`.example.com`、`+.example.com` 等
- Quantumult X / Loon 常见别名：`HOST -> DOMAIN`、`HOST-SUFFIX -> DOMAIN-SUFFIX`、`HOST-KEYWORD -> DOMAIN-KEYWORD`、`IP6-CIDR -> IP-CIDR6`

不同内核语义不能可靠等价转换的内容（例如部分 GEOSITE、客户端专属 regex/process/script）不会硬转；会跳过或要求人工审计，避免“转换成功但语义错”。

## Actions 策略

默认每 6 小时同步一次。同步逻辑：

1. 拉取所有配置的上游；
2. 失败时优先使用仓库里上一次成功的 `mirror/`；
3. 转换、过滤、合并、去重；
4. 自动拆 `non_ip` 和 `ip`；
5. 只把**实际非空**的远程规则写进 `[Rule]`，避免空 RULE-SET 带来的多余请求；
6. 校验相位错误，并强制检查所有 active source / service 均非空；
7. 提交 mirror/rules/dist/docs，并同步刷新 README 中的最新 Surge `[Rule]` 配置；
8. 部署 Pages。

第一次运行没有 last-known-good mirror，如果 active 上游拉取失败会直接失败，而不是生成残缺金融规则。

**V6 额外保护：**远端返回了 HTML/错误页、格式变化导致解析为 0、或过滤后某个 active 服务变成 0 条，同样直接失败；成功状态意味着所有 48 个启用服务至少有一条有效规则。

## 当前预选（不是最终定案）

为了让 Actions 第一次能完整跑通，仓库带了一组“建议 active”，但你仍可逐项改：

- US Banks：`fusion` = Accademia BankUS + 清洗后的 sarkrui。
- Payments US：`fusion` = 清洗 sarkrui + v2fly PayPal + Accademia PayPal/Revolut/Monzo。
- Wise：`fusion`，DIRECT。
- N26：v2fly，France。
- iFAST：官方域名人工维护，DIRECT（因为没有找到足够可靠的长期专项规则仓库）。
- Moomoo US：先 `v2fly-brand`；更重的共享基础设施版由你选择。
- US Broker safety-net：Arthur domain-only；不默认启用它的 63 条大范围 IP。
- IBKR：v2fly + 专项 Gist 融合。
- Bybit EU：v2fly + Sukka 提取，France。
- Binance/OKX/Kraken：v2fly + Sukka 提取，美国。
- Coinbase/Crypto.com：目前只能用较保守的 Sukka 提取；后续最好结合抓包再补，不伪造“高质量专项源”。

## 为什么不是把所有服务合成一条 Finance.list

你的金融地域策略并不一致。N26/Bybit/Wise/iFAST 与美国金融的出口不同，因此必须至少先按**地域和例外**拆开。美国银行与美国支付可以合集；高风险券商/交易所则更适合保留单独文件，便于看到哪个服务新增了域名、哪个上游改变了 IP 段，也便于风控排障。


## GitHub Pages: latest Surge [Rule] block

Every successful Actions build regenerates `docs/index.html` from the same in-memory `RuleSnippet.conf` output. The Pages home page therefore shows the complete latest `[Rule]` block with a one-click copy button, build timestamp, source commit / Actions run metadata when available, plus raw links to `RuleSnippet.conf` and `rule-snippet.txt`.

Do not edit the embedded rule block in `docs/index.html` manually; it is overwritten by `scripts/canonical_build.py` on every build.

<!-- SURGE_RULE_BLOCK:START -->
## 最新 Surge `[Rule]` 配置（Actions 自动更新）

> 本区域由 GitHub Actions 自动刷新，唯一内容来源是 `dist/RuleSnippet.conf`。请不要手动编辑本区域。

> 最后构建：`2026-10-07T13:50:12Z` · 来源 Commit：[`f770862`](https://github.com/ByteVista/Surge-Rule-Hub/commit/f770862a59b8854c788a34a77de0e9219a049504) · [Actions Run #37631638113](https://github.com/ByteVista/Surge-Rule-Hub/actions/runs/37631638113)

GitHub 代码块右上角可直接复制；也可打开 [`docs/RuleSnippet.conf`](docs/RuleSnippet.conf) 查看纯文本。

```ini
[Rule]
# Generated order: custom domain rules -> all remote non-IP -> custom IP -> all remote IP/ASN -> tail.
PROTOCOL,STUN,REJECT

# ===== Remote non-IP rules =====
# > Advertising [awa]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/ads.non_ip.list,REJECT,extended-matching
# > Reject No Drop [sukka]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/reject-no-drop.non_ip.list,REJECT-NO-DROP,extended-matching
# > Reject Drop [sukka]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/reject-drop.non_ip.list,REJECT-DROP,extended-matching
# > Speedtest [sukka]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/speedtest.non_ip.list,SpeedTest,extended-matching
# > OneDrive [curated-fusion]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/onedrive.non_ip.list,Microsoft,extended-matching
# > Google Drive [curated-fusion]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/google-drive.non_ip.list,Google,extended-matching
# > GitHub [blackmatrix7]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/github.non_ip.list,Proxy,extended-matching
# > Static CDN [sukka]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/cdn.non_ip.list,Proxy,extended-matching
# > iCloud Private Relay [sukka]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/apple-private-relay.non_ip.list,Proxy,extended-matching
# > Apple Intelligence [sukka]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/apple-intelligence.non_ip.list,Proxy,extended-matching
# > Apple Update [elysian]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/apple-update.non_ip.list,DIRECT,extended-matching
# > Apple Non-CN CDN [elysian]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/apple-no-cn-cdn.non_ip.list,Proxy,extended-matching
# > Apple API [elysian]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/apple-api.non_ip.list,Apple,extended-matching
# > Apple CDN [elysian]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/apple-cdn.non_ip.list,Apple,extended-matching
# > Apple General [elysian]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/apple-domain.non_ip.list,Apple,extended-matching
# > Microsoft [sukka]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/microsoft.non_ip.list,Microsoft,extended-matching
# > YouTube [rulego]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/youtube.non_ip.list,Streaming,extended-matching
# > Google [v2fly]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/google.non_ip.list,Google,extended-matching
# > AI [sukka]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/ai.non_ip.list,AI,extended-matching
# > HSBC UK [v2fly-uk]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/hsbc-uk.non_ip.list,United Kingdom,extended-matching
# > Tello Mobile [official-manual]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/tello.non_ip.list,United States,extended-matching
# > US Banks [fusion]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/us-banks.non_ip.list,United States,extended-matching
# > Payments US [fusion]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/payments-us.non_ip.list,United States,extended-matching
# > Wise [fusion]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/wise-direct.non_ip.list,DIRECT,extended-matching
# > N26 [v2fly]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/n26-france.non_ip.list,France,extended-matching
# > iFAST [official-manual]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/ifast-direct.non_ip.list,DIRECT,extended-matching
# > Moomoo US [v2fly-brand]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/moomoo-us.non_ip.list,United States,extended-matching
# > Broker US Safety Net [arthur-domain-clean]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/broker-us.non_ip.list,United States,extended-matching
# > Interactive Brokers US [fusion]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/ibkr-us.non_ip.list,United States,extended-matching
# > Bybit EU [v2fly+sukka]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/bybit-eu.non_ip.list,France,extended-matching
# > Binance US [v2fly+sukka]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/binance-us.non_ip.list,United States,extended-matching
# > OKX US [v2fly+sukka]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/okx-us.non_ip.list,United States,extended-matching
# > Kraken US [v2fly+sukka]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/kraken-us.non_ip.list,United States,extended-matching
# > Coinbase US [sukka-extract]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/coinbase-us.non_ip.list,United States,extended-matching
# > Crypto.com US [sukka-extract]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/crypto-com-us.non_ip.list,United States,extended-matching
# > HoYoverse [lm]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/hoyoverse.non_ip.list,Game,extended-matching
# > Nintendo [v2fly]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/nintendo.non_ip.list,Game,extended-matching
# > Epic [v2fly]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/epic.non_ip.list,Japan,extended-matching
# > Steam [v2fly]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/steam.non_ip.list,Japan,extended-matching
# > Wi-Fi Calling US [henry]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/wifi-calling-us.non_ip.list,United States,extended-matching
# > Wi-Fi Calling UK [henry]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/wifi-calling-uk.non_ip.list,United Kingdom,extended-matching
# > Wi-Fi Calling HK [henry]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/wifi-calling-hk.non_ip.list,Hong Kong,extended-matching
# > Telegram [sukka]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/telegram.non_ip.list,Proxy,extended-matching
# > X / Twitter [v2fly]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/x.non_ip.list,Proxy,extended-matching
# > Spotify [v2fly]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/spotify.non_ip.list,Proxy,extended-matching
# > Streaming CN Exceptions [rulego]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/stream-cn-exceptions.non_ip.list,Streaming,extended-matching
# > International Streaming [sukka]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/streaming.non_ip.list,Streaming,extended-matching
# > Download [sukka]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/download.non_ip.list,Download,extended-matching
# > Global Proxy [sukka]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/global-proxy.non_ip.list,Proxy,extended-matching
# > Domestic [sukka]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/domestic.non_ip.list,DIRECT,extended-matching
# > Direct [sukka]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/direct.non_ip.list,DIRECT,extended-matching
# > China IP [sukka]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/china-ip.non_ip.list,DIRECT,extended-matching
# > WeChat [rulego]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/wechat.non_ip.list,DIRECT,extended-matching

# ===== Local/custom IP rules =====
IP-CIDR,161.33.3.233/32,DIRECT,no-resolve
IP-CIDR,8.216.83.167/32,Game,no-resolve
IP-CIDR,1.1.1.1/32,Proxy,no-resolve
IP-CIDR,1.0.0.1/32,Proxy,no-resolve
IP-CIDR,8.8.8.8/32,Proxy,no-resolve
IP-CIDR,8.8.4.4/32,Proxy,no-resolve
IP-ASN,132203,DIRECT,no-resolve
IP-ASN,56040,DIRECT,no-resolve
IP-ASN,45090,DIRECT,no-resolve

# ===== Remote IP / ASN rules =====
# > Apple API [elysian]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/apple-api.ip.list,Apple,no-resolve
# > Wi-Fi Calling US [henry]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/wifi-calling-us.ip.list,United States,no-resolve
# > Wi-Fi Calling UK [henry]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/wifi-calling-uk.ip.list,United Kingdom,no-resolve
# > Wi-Fi Calling HK [henry]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/wifi-calling-hk.ip.list,Hong Kong,no-resolve
# > Telegram [sukka]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/telegram.ip.list,Proxy,no-resolve
# > Streaming CN Exceptions [rulego]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/stream-cn-exceptions.ip.list,Streaming,no-resolve
# > International Streaming [sukka]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/streaming.ip.list,Streaming,no-resolve
# > Domestic [sukka]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/domestic.ip.list,DIRECT,no-resolve
# > China IP [sukka]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/china-ip.ip.list,DIRECT,no-resolve
# > WeChat [rulego]
RULE-SET,https://ByteVista.github.io/Surge-Rule-Hub/rules/wechat.ip.list,DIRECT,no-resolve

# ===== Tail =====
RULE-SET,LAN,DIRECT
GEOIP,CN,DIRECT,no-resolve
FINAL,Final,dns-failed
```
<!-- SURGE_RULE_BLOCK:END -->
