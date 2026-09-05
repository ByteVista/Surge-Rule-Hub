# DNS / QUIC / WebRTC 泄漏治理

这部分必须和 Surge 的 Enhanced Mode/VIF、DNS 设置、代理是否支持 UDP 一起看。单独把 `1.1.1.1` 或 `8.8.8.8` 送代理，不能代表“没有 DNS 泄漏”。

## 建议默认配置

把 `dist/General-Recommended.conf` 的三项合并进现有 `[General]`：

```ini
hijack-dns = *:53
udp-policy-not-supported-behaviour = REJECT
block-quic = all-proxy
```

作用分别是：

- 劫持普通 53 端口 DNS，减少 App 自己绕过 Surge DNS 的机会；
- 当命中的代理策略不支持 UDP 时直接拒绝，而不是让 UDP 悄悄回落 DIRECT；
- 仅对走代理的连接阻止 QUIC，让 HTTP/3 回落 TCP；DIRECT 流量不必全部牺牲 QUIC。

## Strict 版

`General-Strict.conf` 额外加入：

```ini
include-all-networks = true
```

这会进一步扩大 Surge 接管范围，适合你在金融 App 登录/验证期间做严格测试；但可能影响 AirDrop、Xcode 设备发现、USB/局域网工作流，因此不建议不加测试地长期全局打开。

## DNS 规则的正确位置

- `DOMAIN,dns.google,Proxy` / `DOMAIN,cloudflare-dns.com,Proxy` 属于 non-IP；
- `1.1.1.1/1.0.0.1/8.8.8.8/8.8.4.4` 属于 IP phase；
- IP 规则加 `no-resolve`，避免“为了判断 DNS 服务器的 IP 规则又触发 DNS”。

浏览器/应用自己的 DoH/DoT 是另一层协议。`hijack-dns = *:53` 只能处理普通 DNS；如果 Chromium/Firefox 自己启用了 Secure DNS，建议在“严格金融环境”里关闭浏览器 Secure DNS，统一交给 Surge 的 DNS 体系。

## WebRTC

不要用“全局封锁 STUN / 全部 UDP”作为默认 WebRTC 防泄漏方案，会直接破坏音视频、FaceTime/会议软件甚至部分游戏。

更合理的目标是：**浏览器发出的 STUN/UDP 也必须经过 Surge 捕获，且命中一个不支持 UDP 的代理时不能回落 DIRECT**。因此 `udp-policy-not-supported-behaviour = REJECT` 比“让它直连试试”安全得多；需要极限测试时再配合 `include-all-networks = true`。

测试时至少分别检查：

1. 普通网页出口 IP；
2. DNS resolver 所在国家/ASN；
3. WebRTC candidate 是否暴露真实公网 IP；
4. IPv6 是否出现不受控直连；
5. 金融 App 在 Wi-Fi / 蜂窝切换后是否维持同一目标地区出口。

如果你使用 IPv6，还需要确保 Surge VIF/你的节点链路对 IPv6 的处理与预期一致；否则“IPv4 走美国、IPv6 直连本地”会成为最隐蔽的泄漏之一。

## 金融风控比“节点速度”更重要的几个点

- 同一服务尽量固定一个国家、一个稳定出口，不要对登录/API/行情做随机负载均衡。
- 不要让 DNS 走一个国家而 HTTP 出口走另一个国家；至少保证稳定、可解释。
- 不要把共享 analytics/CDN 域名随意强制成美国金融策略；它可能同时服务其他 App，反而形成异常流量画像。
- 对 Bybit EU / N26 / Wise / iFAST 这类例外规则必须放在更广的 US Finance/Global 规则之前。
