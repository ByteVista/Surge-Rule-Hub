# Source Catalog

> 本文件记录“为什么拉这个源”，不是说所有源都会进入最终 active。

| 上游 | 主要用途 | 评价/注意事项 |
|---|---|---|
| SukkaW/Surge / ruleset.skk.moe | 主体骨架：reject/CDN/AI/Telegram/stream/download/global/direct/domestic/china | **首选骨架**；Surge 语义与 non-IP/IP 顺序清晰。 |
| v2fly/domain-list-community | Google/X/Spotify/PayPal/Wise/N26/Moomoo roots/IBKR/Binance/Bybit/OKX/Kraken/Nintendo/Epic/Steam | **首选服务所有权数据库**；MIT；需要转换，不等于策略库。 |
| ConnersHua/RuleGo | AI/WeChat/X/YouTube/Streaming !CN | 原生 Surge，文件紧凑；适合和 v2fly/Sukka逐服务比较。 |
| Accademia/Additional_Rule_For_Clash | BankUS、PayPal、Wise、Revolut、Monzo | 金融专项价值高；Clash classical -> Actions 转 Surge。 |
| sarkrui/US_Bank.list | 美国银行/支付品牌补漏 | 最近活动核对到 2026-04-04；**必须清洗**共享 analytics/跨业务域。 |
| CjSalute/fenliu | 金融服务 inventory / 配置思路 | 2026-05-09 时代配置广而全；只镜像审计，不整份用。 |
| Arthur-vx/broker-rules | Moomoo/Futu shared infra、Longbridge/Tiger/Schwab | 文件头 2026-06-19；151 rules，含 63 IP。domain-only 默认，full IP 可选。 |
| GravityPoet IBKR Gist | IBKR API/portal 补充 | 与 v2fly 合并更符合金融覆盖优先。 |
| Elysian-Realme/FuGfConfig | Apple 细分 | commit 数少，但细分符合用户当前 Apple 行为；保留候选。 |
| LM-Firefly/Rules | HoYoverse | 专项规则清晰；当前默认。 |
| CINGDAAT/Rules | HoYoverse supplement | 作为融合备选。 |
| HenryChiao/the_clash_ruleset | US/UK/HK Wi-Fi Calling | 专项位置规则，继续观察共享第三方域误命中。 |
| TG-Twilight/AWAvenue-Ads-Rule | Ads | 广告专项，与 Sukka reject/drop 分工。 |
| blackmatrix7/ios_rule_script | Google/Spotify/Nintendo/Epic/Steam fallback | 只保留服务级小文件作备选；不使用大而全合集。 |
| QuixoticHeart/rule-set | Crypto audit | **`public_output=false`**。上游有明确再发布限制，不能用于 Pages active 产物。 |

## 格式和发布规则

- `public_output=false` 的源即使能下载，也不能成为 active，否则构建直接失败。
- `surge-profile`（如 CjSalute）只镜像，不把整个配置误解析成一个 RULE-SET。
- v2fly `@cn/@ads` 可按 source 的 `exclude_attrs` 过滤；递归 `include:` 会解析。
- 不能可靠转换的 regexp/客户端专属语义宁可跳过，不假装等价。
