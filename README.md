[README.md](https://github.com/user-attachments/files/31863994/README.md)
# Surge Rule Hub（个人分流规则仓库模板）

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
5. Actions 成功后，打开 Pages 首页确认规则条数不为 0，再使用页面上的 `RuleSnippet.conf`。
6. 将 `dist/General-Recommended.conf` 中的键**合并到已有 `[General]`**，不要创建第二个 `[General]`。

### GitHub Pages 与“私有仓库”的重要区别

GitHub Pages 站点用于给 Surge 拉取远程规则，因此通常必须公开可访问。私有仓库是否能启用 Pages 取决于你的 GitHub 套餐；而且普通 Pages 即使来源仓库是 Private，站点也通常不是“仅自己可访问”。真正的 Private Pages 访问控制主要属于组织/Enterprise 场景。

因此最实用的结构是：**源码/配置仓库 Private + Pages 产物公开**。如果你不希望任何生成规则公开，不要用 Pages；改用你自己的静态托管/CDN，或使用一个支持令牌但 Surge 能稳定访问的分发方式。

## 如何选择每个服务的上游

仓库不会把我的推荐强制锁死。查看所有可选项：

```bash
python3 scripts/select.py --list
```

例如把美国银行切到纯 Accademia：

```bash
python3 scripts/select.py us-banks accademia
```

把 Moomoo 切到“v2fly + Arthur 共享 Futu/Moomoo 域名（不含大段 IP）”覆盖版：

```bash
python3 scripts/select.py moomoo-us coverage-fusion
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
6. 校验相位错误；
7. 提交 mirror/rules/dist/docs，并同步刷新 README 中的最新 Surge `[Rule]` 配置；
8. 部署 Pages。

第一次运行没有 last-known-good mirror，如果 active 上游拉取失败会直接失败，而不是生成残缺金融规则。

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

Do not edit the embedded rule block in `docs/index.html` manually; it is overwritten by `scripts/build.py` on every build.

<!-- SURGE_RULE_BLOCK:START -->
## 最新 Surge `[Rule]` 配置（Actions 自动更新）

> 本区域由 GitHub Actions 自动刷新，唯一内容来源是 `dist/RuleSnippet.conf`。请不要手动编辑本区域。

> 最后构建：`2026-09-05T12:48:49Z` · 来源 Commit：[`23207f9`](https://github.com/CINGDAAT/Surge-Rule-Hub/commit/23207f9b1e6da19078778f1dd4f6c0e53da34f45) · [Actions Run #33967096085](https://github.com/CINGDAAT/Surge-Rule-Hub/actions/runs/33967096085)

GitHub 代码块右上角可直接复制；也可打开 [`docs/RuleSnippet.conf`](docs/RuleSnippet.conf) 查看纯文本。

```ini
[Rule]
# PRE-ACTION LOCAL BUILD: remote mirrors are not populated in this ZIP. Run GitHub Actions before using this file.
# Generated order: custom domain rules -> all remote non-IP -> custom IP -> all remote IP/ASN -> tail.
DOMAIN-SUFFIX,skk.moe,🇺🇸Relay
DOMAIN-SUFFIX,iplark.com,🇺🇸Relay
DOMAIN-SUFFIX,ipcheck.ing,🇺🇸Relay
DOMAIN,dns.google,Proxy
DOMAIN,cloudflare-dns.com,Proxy
DOMAIN-SUFFIX,usaddres.com,DIRECT
DOMAIN-SUFFIX,daat.eu.org,DIRECT
DOMAIN-SUFFIX,voxi.co.uk,United Kingdom
DOMAIN-SUFFIX,redpocket.com,United States
DOMAIN-SUFFIX,anytimemailbox.com,United States
DOMAIN-SUFFIX,irs.gov,United States
DOMAIN,api.lemonsqueezy.com,REJECT
DOMAIN-SUFFIX,gametrade.jp,Japan
DOMAIN,prepaid.hkcsl.com,DIRECT
DOMAIN-SUFFIX,bochk.com,DIRECT
DOMAIN-SUFFIX,gjfzpt.cn,REJECT
DOMAIN-SUFFIX,jsdelivr.net,Proxy
DEST-PORT,123,DIRECT

# ===== Remote non-IP rules =====
# > iFAST [official-manual]
RULE-SET,https://<GITHUB_USER>.github.io/<REPO>/rules/ifast-direct.non_ip.list,DIRECT,extended-matching

# ===== Local/custom IP rules =====
IP-CIDR,161.33.3.233/32,DIRECT,no-resolve
IP-CIDR,8.216.83.167/32,Game,no-resolve
IP-CIDR,1.1.1.1/32,Proxy,no-resolve
IP-CIDR,1.0.0.1/32,Proxy,no-resolve
IP-CIDR,8.8.8.8/32,Proxy,no-resolve
IP-CIDR,8.8.4.4/32,Proxy,no-resolve
IP-ASN,132203,DIRECT
IP-ASN,56040,DIRECT
IP-ASN,45090,DIRECT

# ===== Remote IP / ASN rules =====

# ===== Tail =====
RULE-SET,LAN,DIRECT
GEOIP,CN,DIRECT
FINAL,Final,dns-failed
```
<!-- SURGE_RULE_BLOCK:END -->
