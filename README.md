# Surge Rule Hub

公开的 Surge 分流规则仓库。自动同步多个上游，按服务整理并生成配置；配置直接展示在本 README，远程规则从 GitHub Raw 读取，无需 GitHub Pages 或 GitHub Pro。

## 使用方法

1. 复制下方最新推荐配置，或打开 [最终配置原文](https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/dist/Final-Recommended.conf)。
2. 将 `[General]` 中的键合并到本地已有的 `[General]`，用 `[Rule]` 更新分流规则。
3. 保留本地节点、策略组、密码和个人规则；本仓库配置不包含这些内容。策略组名称须与规则中使用的名称一致。

| 文件 | 用途 |
| --- | --- |
| [Final-Recommended.conf](https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/dist/Final-Recommended.conf) | 推荐设置与完整 `[Rule]` 配置 |
| [RuleSnippet.conf](https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/dist/RuleSnippet.conf) | 仅通用 `[Rule]` 片段 |
| [RuleSnippet-Mac.conf](https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/dist/RuleSnippet-Mac.conf) | macOS 可选的 Telegram fail-closed 规则 |
| [General-Recommended.conf](https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/dist/General-Recommended.conf) | DNS / QUIC 建议设置 |
| [General-Strict.conf](https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/dist/General-Strict.conf) | 更严格的全网络接管设置，需按设备与网络测试 |

<!-- SURGE_RULE_BLOCK:START -->
## 最新 Surge 推荐配置（Actions 自动更新）

> 本区域由 GitHub Actions 自动刷新，唯一内容来源是 `dist/Final-Recommended.conf`，包含 `[General]` 和 `[Rule]`。请不要手动编辑本区域。

> 最后构建：`2026-11-09T22:39:55Z` · 来源 Commit：[`a414ed5`](https://github.com/ByteVista/Surge-Rule-Hub/commit/a414ed5291a01439734a0be892b01ea9928f2b7a) · [Actions Run #42713834173](https://github.com/ByteVista/Surge-Rule-Hub/actions/runs/42713834173)

GitHub 代码块右上角可直接复制；也可打开 [`dist/Final-Recommended.conf`](dist/Final-Recommended.conf) 查看文件。

```ini
# 合并到本地已有 [General]；本文件不包含节点、密码或私人规则。
[General]
dns-server = 223.5.5.5
encrypted-dns-server = https://223.5.5.5/dns-query
encrypted-dns-follow-outbound-mode = false
encrypted-dns-skip-cert-verification = false
hijack-dns = *:53
udp-policy-not-supported-behaviour = REJECT
block-quic = all-proxy
# IPv6 接管选项请根据设备与网络实测保留本地设置。

[Rule]
# Generated order: custom domain rules -> all remote non-IP -> custom IP -> all remote IP/ASN -> tail.
PROTOCOL,STUN,REJECT

# ===== Remote non-IP rules =====
# > Advertising [awa]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/ads.non_ip.list,REJECT,extended-matching
# > Reject No Drop [sukka]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/reject-no-drop.non_ip.list,REJECT-NO-DROP,extended-matching
# > Reject Drop [sukka]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/reject-drop.non_ip.list,REJECT-DROP,extended-matching
# > Speedtest [sukka]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/speedtest.non_ip.list,SpeedTest,extended-matching
# > Discord [v2fly]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/discord.non_ip.list,Proxy,extended-matching
# > HSBC HK [v2fly-hk]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/hsbc-hk.non_ip.list,DIRECT,extended-matching
# > OneDrive [curated-fusion]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/onedrive.non_ip.list,Microsoft,extended-matching
# > Google Drive [curated-fusion]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/google-drive.non_ip.list,Google,extended-matching
# > GitHub [blackmatrix7]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/github.non_ip.list,Proxy,extended-matching
# > Static CDN [sukka]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/cdn.non_ip.list,Proxy,extended-matching
# > iCloud Private Relay [sukka]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/apple-private-relay.non_ip.list,Proxy,extended-matching
# > Apple Intelligence [sukka]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/apple-intelligence.non_ip.list,Proxy,extended-matching
# > Apple Update [elysian]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/apple-update.non_ip.list,DIRECT,extended-matching
# > Apple Non-CN CDN [elysian]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/apple-no-cn-cdn.non_ip.list,Proxy,extended-matching
# > Apple API [elysian]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/apple-api.non_ip.list,Apple,extended-matching
# > Apple CDN [elysian]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/apple-cdn.non_ip.list,Apple,extended-matching
# > Apple General [elysian]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/apple-domain.non_ip.list,Apple,extended-matching
# > Microsoft [sukka]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/microsoft.non_ip.list,Microsoft,extended-matching
# > YouTube [rulego]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/youtube.non_ip.list,Streaming,extended-matching
# > Google [v2fly]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/google.non_ip.list,Google,extended-matching
# > AI [sukka]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/ai.non_ip.list,AI,extended-matching
# > HSBC UK [v2fly-uk]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/hsbc-uk.non_ip.list,United Kingdom,extended-matching
# > Tello Mobile [official-manual]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/tello.non_ip.list,United States,extended-matching
# > US Banks [fusion]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/us-banks.non_ip.list,United States,extended-matching
# > Payments US [fusion]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/payments-us.non_ip.list,United States,extended-matching
# > Wise [fusion]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/wise-direct.non_ip.list,DIRECT,extended-matching
# > N26 [v2fly]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/n26-france.non_ip.list,France,extended-matching
# > iFAST [official-manual]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/ifast-direct.non_ip.list,DIRECT,extended-matching
# > Moomoo US [v2fly-brand]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/moomoo-us.non_ip.list,United States,extended-matching
# > Broker US Safety Net [arthur-domain-clean]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/broker-us.non_ip.list,United States,extended-matching
# > Interactive Brokers US [fusion]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/ibkr-us.non_ip.list,United States,extended-matching
# > Bybit EU [v2fly+sukka]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/bybit-eu.non_ip.list,France,extended-matching
# > Binance US [v2fly+sukka]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/binance-us.non_ip.list,United States,extended-matching
# > OKX US [v2fly+sukka]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/okx-us.non_ip.list,United States,extended-matching
# > Kraken US [v2fly+sukka]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/kraken-us.non_ip.list,United States,extended-matching
# > Coinbase US [sukka-extract]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/coinbase-us.non_ip.list,United States,extended-matching
# > Crypto.com US [sukka-extract]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/crypto-com-us.non_ip.list,United States,extended-matching
# > HoYoverse [lm]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/hoyoverse.non_ip.list,Game,extended-matching
# > Nintendo [v2fly]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/nintendo.non_ip.list,Game,extended-matching
# > Epic [v2fly]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/epic.non_ip.list,Japan,extended-matching
# > Steam [v2fly]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/steam.non_ip.list,Japan,extended-matching
# > Wi-Fi Calling US [henry]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/wifi-calling-us.non_ip.list,United States,extended-matching
# > Wi-Fi Calling UK [henry]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/wifi-calling-uk.non_ip.list,United Kingdom,extended-matching
# > Wi-Fi Calling HK [henry]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/wifi-calling-hk.non_ip.list,Hong Kong,extended-matching
# > Telegram [sukka]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/telegram.non_ip.list,Proxy,extended-matching
# > X / Twitter [v2fly]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/x.non_ip.list,Proxy,extended-matching
# > Spotify [v2fly]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/spotify.non_ip.list,Proxy,extended-matching
# > Streaming CN Exceptions [rulego]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/stream-cn-exceptions.non_ip.list,Streaming,extended-matching
# > International Streaming [sukka]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/streaming.non_ip.list,Streaming,extended-matching
# > Download [sukka]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/download.non_ip.list,Download,extended-matching
# > Global Proxy [sukka]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/global-proxy.non_ip.list,Proxy,extended-matching
# > Domestic [sukka]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/domestic.non_ip.list,DIRECT,extended-matching
# > Direct [sukka]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/direct.non_ip.list,DIRECT,extended-matching
# > China IP [sukka]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/china-ip.non_ip.list,DIRECT,extended-matching
# > WeChat [rulego]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/wechat.non_ip.list,DIRECT,extended-matching

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
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/apple-api.ip.list,Apple,no-resolve
# > Wi-Fi Calling US [henry]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/wifi-calling-us.ip.list,United States,no-resolve
# > Wi-Fi Calling UK [henry]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/wifi-calling-uk.ip.list,United Kingdom,no-resolve
# > Wi-Fi Calling HK [henry]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/wifi-calling-hk.ip.list,Hong Kong,no-resolve
# > Telegram [sukka]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/telegram.ip.list,Proxy,no-resolve
# > Streaming CN Exceptions [rulego]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/stream-cn-exceptions.ip.list,Streaming,no-resolve
# > International Streaming [sukka]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/streaming.ip.list,Streaming,no-resolve
# > Domestic [sukka]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/domestic.ip.list,DIRECT,no-resolve
# > China IP [sukka]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/china-ip.ip.list,DIRECT,no-resolve
# > WeChat [rulego]
RULE-SET,https://raw.githubusercontent.com/ByteVista/Surge-Rule-Hub/main/rules/wechat.ip.list,DIRECT,no-resolve

# ===== Tail =====
RULE-SET,LAN,DIRECT
GEOIP,CN,DIRECT,no-resolve
FINAL,Final,dns-failed
```
<!-- SURGE_RULE_BLOCK:END -->

## 自动更新

GitHub Actions 每周一 08:37（新加坡时间，UTC+8）同步上游，也可在 [Actions](https://github.com/ByteVista/Surge-Rule-Hub/actions/workflows/sync-rules.yml) 手动运行。每次构建依次恢复并校验固定构建器、抓取上游、转换和去重、生成配置、同步 README、校验并提交生成物，不再部署 Pages。

抓取失败时使用上一次成功的 `mirror/`；没有可用镜像或启用服务解析为空时，构建失败并保留原有生成物。所有远程非 IP 规则排在 IP / ASN 规则之前，专项服务排在通用规则之前。

## 来源与目录

- [config/sources.json](config/sources.json)：上游来源；按覆盖范围和匹配精度选择，不固定只用某一家。
- [config/services.json](config/services.json)：候选方案、启用来源、策略与优先级。
- [config/custom_rules.json](config/custom_rules.json)：公开共享的规则设置，个人规则请保留在本地。
- [rules/](rules/)：当前启用规则；[rules/candidates/](rules/candidates/)：各候选方案的转换结果。
- [mirror/](mirror/)：上次成功同步的上游原文；[dist/](dist/)：最终配置和构建报告。
- [UPSTREAM_COMPARISON.md](UPSTREAM_COMPARISON.md)：上游比较。
- [PRIVACY_DNS_WEBRTC.md](PRIVACY_DNS_WEBRTC.md)：DNS / QUIC / WebRTC 设置说明。
- [SOURCE_CATALOG.md](SOURCE_CATALOG.md)：来源与许可说明。

查看或切换来源：

```bash
python3 scripts/select_source.py --list
python3 scripts/select_source.py us-banks accademia
```

切换后提交 `config/services.json`，Actions 会重新生成配置与 README。
