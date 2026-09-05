# 上游横向对比与候选选择（2026-08-21）

更新频率的判断分两层：**项目总体活跃度**和**目标文件是否专项维护**。一个每天构建的大仓库，不代表某个冷门服务每天都有有效变化；反之一个只有少量 commit 的专项文件，也可能比大合集更准确。

## 1. 主体骨架

| 服务 | 候选 | 活跃/特征 | 优点 | 缺点 | 当前建议 |
|---|---|---|---|---|---|
| 通用骨架 | SukkaW/Surge | 数千 commits；规则自动构建；明确 non-IP/IP 分层 | Surge 原生、结构清晰、DNS 触发语义考虑完善 | 不是每个具体 App 都有专项表 | **主体保留** |
| 通用域名资产 | v2fly/domain-list-community | 5k+ commits、社区持续 PR；服务级 data 文件 | 服务所有权域名干净、可拆 per-service、MIT | 本身不是“代理策略”，无 IP；需转换并处理 attrs/include | **大量专项服务默认来源** |
| Surge 专项补充 | ConnersHua/RuleGo | 原生 Surge，多项 Extra/Streaming | 文件小、可读、适合 YouTube/WeChat 等 | 覆盖常比 v2fly 紧凑 | **按服务比较** |
| 大而全 | blackmatrix7 | 库大、历史覆盖广 | 很多服务都有现成 Surge 文件 | 用户当前不希望承担大合集/重复依赖 | **只做小文件备选** |
| 衍生配置仓库 | Rabbit-Spec 等 | 有的更新很快 | 可提供配置思路 | 往往再引用 BM/MetaCubeX 等，不是独立事实源 | 审计参考，不作为首选源 |

### 为什么 SukkaW 继续当主体是合适的

Sukka 的核心价值不是“规则最少”，而是它明确把 `domainset/non_ip` 放在 IP 类规则前，并把 Telegram、Streaming、AI、China IP 等拆成可理解的数据来源。你的旧规则已经采用这个方向，问题主要出在**后面又叠加了 BM/RuleGo/自定义 IP，破坏了整体顺序和产生重复**，而不是 Sukka 本身不合适。

## 2. 当前常用服务逐项比较

| 服务 | 方案 A | 方案 B | 结论/选择权 |
|---|---|---|---|
| Ads | AWAvenue | Sukka reject 类 | AWAvenue 专门负责广告；Sukka reject-no-drop/drop 负责网络行为，两者不是互斥，继续分层。 |
| Apple | Elysian 细分 | Sukka Apple 体系 | Elysian 能保留 update/DIRECT、no-CN-CDN/API/CDN/general 的精细策略；Sukka 活跃度更强且依赖更少。当前保留 **Elysian 细分 + Sukka Private Relay/Intelligence**，等你决定要不要简化。 |
| Microsoft | Sukka | v2fly Microsoft | Sukka 有 CDN 与 Microsoft 两层，直接适配 Surge；**Sukka 更适合你的骨架**。v2fly 适合所有权资产但没有策略拆分。 |
| Google | `G1 v2fly` | `G2 BM Google` | v2fly 是活跃的服务所有权域名库，避免你现在 BM + RuleGo Proxy+ 的叠加；**G1 默认**。 |
| AI | `A1 Sukka` | `A2 RuleGo` | Sukka 同时有 AI non-IP/IP 架构且自动维护；RuleGo 文件紧凑、可读。**A1 默认，A2 备选**。 |
| X | `X1 v2fly` | `X2 RuleGo` | v2fly 通常覆盖更广的 Twitter/X 资产；RuleGo 更轻。**X1 默认**。 |
| YouTube | `Y1 RuleGo` | `Y2 v2fly` | RuleGo 更贴近“视频分流”；v2fly 更像 Google/YouTube 所有权全资产，明显更重。**Y1 默认**。 |
| Spotify | `S1 v2fly` | `S2 BM Spotify` | v2fly 文件约 29 个有效域项，还能排除 `@ads`；活跃社区源。**S1 默认**。 |
| Telegram | Sukka | v2fly/其他合集 | Sukka IP 直接来自 Telegram 官方 CIDR 并另有 ASN；**不建议换**。macOS 可选 PROCESS fail-closed。 |
| Streaming | Sukka + RuleGo `!CN` | 单独 v2fly category | 前者更贴近你当前 Surge 策略与地区例外。暂时**保留**。 |
| Nintendo | v2fly | BM Nintendo | v2fly 服务域更广并可过滤 `@cn`；**v2fly 默认**。 |
| Epic | v2fly | BM Epic | 同上；converter 对无法等价转换的 regex 会跳过。**v2fly 默认**。 |
| Steam | v2fly | BM Steam | v2fly Steam 文件包含官方域、CDN 和海外节点，并可排除 `@cn`。**v2fly 默认**。 |
| HoYoverse | LM-Firefly | CINGDAAT | LM 更干净好审计；CINGDAAT 更像补充层。提供 `lm / cingdaat / fusion` 三选一，**LM 默认**。 |
| Wi-Fi Calling | HenryChiao | 自写运营商域名 | 找到的项目里 HenryChiao 更接近专项多地区现成源；继续用，但共享第三方域名如出现误命中要过滤。 |

## 3. 美国银行

### BANK1 — Accademia / BankUS

优点：专项 US Bank 文件，包含 Chase、Wells Fargo、Citi、BofA、US Bank、Capital One、Amex、Discover、Synchrony、PNC、Schwab、Citizens、Ally、5/3、Key、Regions、M&T、Huntington、Santander 等，并含 Plaid/Zelle。项目累计数百 commit。

缺点：作者自己也提醒公共 CDN/子域覆盖不是绝对完整；Clash classical 需要转换。

### BANK2 — sarkrui US_Bank.list（清洗版）

Gist 页面重新核对为 **2026-04-04 最近活动**。它对 Chase/BofA/Citi/PNC 等品牌别名比很多规则细。

缺点：原始文件混有 Segment、Quantum Metric、Optimizely、Adobe/Demdex、Intercom、Equifax、Kraken、Wise、eBay 等共享/跨业务域，不能整份直接套“美国银行”策略。

### BANK3 — Fusion（当前推荐 active）

`BANK1 + BANK2 清洗后品牌根域`。这是我最推荐你先跑的方案：**不是最轻，但更符合你金融“宁可多覆盖、不要漏网”的要求**，同时不会把 sarkrui 里明显共享的 telemetry 一股脑送美国。

## 4. 支付 / Wise

| 代号 | 来源 | 说明 |
|---|---|---|
| PAY1 | sarkrui payment roots | PayPal/Venmo/Stripe/Square/Cash/Zelle/Plaid 等清洗提取。 |
| PAY2 | v2fly PayPal | PayPal 所有权生态很广，适合补 Braintree/Venmo/Xoom 等关联资产。 |
| PAY3 | Accademia VirtualFinance | PayPal/Revolut/Monzo 专项。 |
| **PAY4** | PAY1+PAY2+PAY3 | **当前推荐**；Wise 明确排除。 |
| WISE1 | v2fly | `wise.com + transferwise.com`，非常干净。 |
| WISE2 | Accademia | 独立 Wise 交叉验证。 |
| **WISE3** | union | 两者并集，仍很小，**DIRECT**。 |

CjSalute 的 2026-05-09 时代配置很适合作为“金融服务清单”，但它把多种金融/支付放在统一策略，且很多银行只有一级根域，因此**只镜像用于审计，不直接作为你的 Finance RULE-SET**。

## 5. 券商

| 服务 | 候选 | 评价 | 建议 |
|---|---|---|---|
| Moomoo US | `MOO1 v2fly-brand` | 目前 v2fly `futu` 数据里可独立识别的 Moomoo 根域是 `moomoo.com / moomooequity.com / moomootrustee.com`；最干净，但共享 Futu API 可能漏。 | **默认** |
| Moomoo US | `MOO2 arthur-domain-shared` | 从 Arthur 提取 Moomoo/Futu 共享基础设施但去掉全部 IP；覆盖更强，误伤比 full 版低。 | **金融覆盖优先时更推荐你选它或 fusion** |
| Moomoo US | `MOO3 coverage-fusion` | MOO1 + MOO2。 | 我个人更倾向于你最终选 **MOO3**，但先由你确认。 |
| Broker safety | Arthur domain-only | Arthur 文件头标注更新至 **2026-06-19**，151 条含 63 IP；覆盖 Moomoo/Futu/Longbridge/Tiger/Schwab。默认只启用域名版。 | **默认安全网** |
| Broker safety | Arthur complete | 加 63 条 IP，覆盖更强，但部分为较大云网段，可能把同网段其他业务误送美国。 | 可选增强，不默认 |
| IBKR | v2fly | `ibkr.* / ibllc.com / interactivebrokers.*` 等 20+ 项；社区源活跃。 | A |
| IBKR | GravityPoet Gist | 2026-01-21 仍有活动，显式含 `api.ibkr.com` 等接口。 | B |
| **IBKR** | fusion | A+B。金融规则体量仍小，收益大。 | **默认/推荐** |
| Robinhood | 暂无强专项上游 | 搜到的更多是 API 客户端/个人配置，不足以作为高置信度路由上游。 | 暂不伪造；后续做官方域+抓包审计 |
| Webull | 同上 | 有 API repo 能验证部分生产 host，但没有我愿意称为“长期高质量分流源”的专项表。 | 同上 |
| Fidelity | 个人自维护规则可找到 | 但维护来源/覆盖证明不足。 | 仅作为候选素材，不默认 |
| E*TRADE / SoFi | 暂无强专项上游 | 同理。 | 等下一轮逐服务抓包/官方域验证 |

> 你说“券商都尽量美国版”后，保留一个 US Broker safety-net 是合理的；但对高风控 App，我仍建议 Moomoo/IBKR/Robinhood/Webull 等逐个独立文件优先匹配，再让 Broker-US 兜底。

## 6. 交易所 / 虚拟货币

QuixoticHeart/rule-set 的 crypto 数据很全、且自动构建频繁，但其 README 有“禁止转载/发布至中国大陆地区”等明确再发布限制。你的 Pages 会把生成规则再次公开，因此它在本仓库被标记 `public_output=false`，**只能审计，绝不作为公开 active 来源**。

| 服务 | 候选 | 覆盖判断 | 默认 |
|---|---|---|---|
| Bybit EU -> France | v2fly | 约十多个 Bybit 相关根域（bybit/byapis/byapps/bytick 等） | A |
|  | Sukka global 提取 | 可补 Sukka 已维护到的根域 | B |
|  | A+B | 不依赖受限来源 | **默认** |
| Binance US -> US | v2fly | 数十个 Binance 资产，含 `binance.us` / API/static | A |
|  | Sukka 提取 | 交叉补充 | B |
|  | A+B | **默认** |
| OKX -> US | v2fly | OKX/OKEx/OKLink/XLayer 等 | A |
|  | Sukka 提取 | 交叉补充 | B |
|  | A+B | **默认** |
| Kraken -> US | v2fly | 当前独立数据较小，只有少数根域 | A（单独太薄） |
|  | Sukka 提取 | 补一层 | B |
|  | A+B | **默认，但仍建议后续抓包** |
| Coinbase -> US | Sukka 提取 | 比你原来的手写一条更可维护，但仍可能薄 | **临时默认** |
| Crypto.com -> US | Sukka 提取 | 同上 | **临时默认** |

## 7. 你最终可以这样回我选择

例如：

```text
BANK3, PAY4, WISE3,
MOO3 + BROKER-domain, IBKR-fusion,
Bybit=v2+sukka, Binance=v2+sukka, OKX=v2+sukka, Kraken=v2+sukka,
Google=v2fly, AI=Sukka, X=v2fly, YouTube=RuleGo, Spotify=v2fly,
HoYo=LM, Apple=Elysian细分+Sukka特殊项
```

这次 ZIP 的 active 只是为了让仓库可运行，并不视为你已经做出最终选择。
