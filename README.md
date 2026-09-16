<div align="center">

# Jargon

### Jargon，你说感觉，Jargon 帮你专业术语补全。

<p>
  <img src="https://img.shields.io/badge/18%20%E4%B8%AA%E9%A2%86%E5%9F%9F-indexed-6d5dfc" alt="19 个领域">
  <img src="https://img.shields.io/badge/19%20%E4%B8%AA%E9%A2%86%E5%9F%9F-indexed-20a464" alt="19 个领域">
  <img src="https://img.shields.io/badge/npx-first-f59e0b" alt="npx first">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-111827" alt="MIT License"></a>
</p>

<p>
  <a href="#快速开始">快速开始</a> ·
  <a href="#工作原理">工作原理</a> ·
  <a href="#支持平台">支持平台</a> ·
  <a href="#添加新领域">添加新领域</a>
</p>

</div>

## 它能做什么

你知道自己想要什么，但不知道怎么说得专业？Jargon 会识别需求所属领域，按需加载术语，把“有质感”“稳定”“高级”“专业一点”等模糊表达扩展成更具体、更可执行的提示词。

Jargon 不替你决定方向。它把专业选项翻译成容易理解的语言，再让你选择真正重要的取舍。

| 你说 | Jargon 帮你补全 |
|---|---|
| 做一个有质感的网站 | 信息密度、字体层级、高对比度、留白节奏、组件一致性 |
| 做一个稳定的大型后端 | 高可用、高并发、流量模型、水平扩展、幂等、熔断、可观测性 |
| 做一个电影感的视频 | 景别、光线、构图、色调、运动、画幅比例、声音 |

## 🚀 快速开始

推荐使用 `npx`。它适用于 Claude Code、Cursor、Codex、OpenCode 等多种 Agent 工具，不需要手动复制文件。

```bash
npx skills add https://github.com/konglong87/jargon
```

安装后，直接对 Agent 说：

```text
做一个有质感的中文电商首页
```

Jargon 会识别模糊词、加载相关术语、给出可选方向，并在你确认后生成增强提示词。

<details>
<summary>更多 npx 安装选项</summary>

```bash
# 查看可用技能
npx skills add https://github.com/konglong87/jargon --list

# 全局安装
npx skills add https://github.com/konglong87/jargon -g

# 指定平台安装
npx skills add https://github.com/konglong87/jargon \
  --skill jargon \
  --agent claude-code cursor codex
```

需要 Node.js 和 npm。若安装器参数发生变化，请以 `npx skills add --help` 的当前提示为准。

</details>

## 支持平台

| 平台 | 安装命令 |
|---|---|
| Claude Code | `npx skills add https://github.com/konglong87/jargon --skill jargon --agent claude-code` |
| Cursor | `npx skills add https://github.com/konglong87/jargon --skill jargon --agent cursor` |
| Codex | `npx skills add https://github.com/konglong87/jargon --skill jargon --agent codex` |
| OpenCode | `npx skills add https://github.com/konglong87/jargon --skill jargon --agent opencode` |

如果目标工具没有自动识别 Skill，也可以手动加载 [`skills/jargon/SKILL.md`](skills/jargon/SKILL.md)。

## 工作原理

```mermaid
flowchart LR
    A[用户模糊需求] --> B[根领域索引]
    B --> C[意图索引]
    C --> D[按需加载术语包]
    D --> E[LLM 语义匹配]
    E --> F[专业候选与取舍]
    F --> G[增强提示词]
```

每次只加载当前请求相关的领域和意图，不会把全部术语一次性塞进上下文。

1. 识别用户所属领域。
2. 匹配用户要做的事情，也就是意图。
3. 加载对应术语列表。
4. 识别模糊词、同义表达和相关维度。
5. 输出 3～6 个专业方向，并说明收益和代价。
6. 只询问会改变方案的问题。
7. 用户确认后生成最终增强提示词。

没有匹配到术语包时，只有在用户允许后才进行网络搜索。搜索结果只作为本次临时参考，不自动写回术语库。

## 当前覆盖范围

| 内容 | 状态 |
|---|---|
| 多级根领域索引 | ✅ |
| 按需加载术语包 | ✅ |
| UI/UX 术语包 | ✅ |
| 后端术语包 | ✅ |
| AIGC 术语包 | ✅ |
| 其他领域术语入口 | ✅ |
| npx CLI | 🚧 规划中 |

当前索引包含 19 个领域。UI/UX、后端和 AIGC 术语包内容更完整；其他领域持续扩充中。

## 项目结构

```text
index/
├── root.json       # 19 个根领域索引
└── packages.json   # 领域、意图和术语包索引

terms/              # 按领域拆分的术语列表
skills/jargon/
└── SKILL.md        # Agent 使用规则
```

术语包状态：

- `published`：可以被运行时直接加载。
- `draft`：维护中的草案，不应作为确定专业事实注入提示词。

## 添加新领域

新增领域只需要三步：

1. 在 `index/root.json` 增加领域入口。
2. 在 `index/packages.json` 增加领域和术语包映射。
3. 在 `terms/` 增加术语列表。

每个术语建议包含：

```json
{
  "term": "高可用",
  "plain_language": "部分机器出故障时，服务仍能继续提供",
  "benefit": "降低单点故障影响",
  "cost": "增加部署和运维复杂度"
}
```

不要提交密钥、令牌、个人路径或真实用户隐私。法律、医学、金融等高风险领域需要明确适用范围，不能替代专业意见。

## 手动安装

```bash
git clone https://github.com/konglong87/jargon.git
```

然后将 [`skills/jargon/SKILL.md`](skills/jargon/SKILL.md) 加载到你的 Agent 配置中，并让它读取 `index/root.json`、`index/packages.json` 和对应的 `terms/*.json`。

## License

[MIT](LICENSE)
