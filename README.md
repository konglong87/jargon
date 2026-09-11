# Jargon

**把用户的模糊需求，翻译成行业专业术语。**

你知道自己想要什么，但不知道怎么说得专业？Jargon 会识别需求所属领域，按需加载术语，把“有质感”“稳定”“高级”“专业一点”等模糊表达扩展成更具体、更可执行的提示词。

## 它能做什么

```text
“做一个有质感的网站”
→ 信息密度、字体层级、高对比度、留白节奏、组件一致性

“做一个稳定的大型后端”
→ 高可用、高并发、流量模型、水平扩展、幂等、熔断、可观测性
```

Jargon 不替你决定产品方向。它先把专业选项翻译成容易理解的语言，再让你选择真正重要的取舍。

## 快速安装

推荐使用 `npx`。它适用于 Claude Code、Cursor、Codex、OpenCode 等多种 Agent 工具，不需要手动复制文件。

### 安装全部内容

```bash
npx skills add https://github.com/konglong87/jargon
```

### 查看可用技能

```bash
npx skills add https://github.com/konglong87/jargon --list
```

### 全局安装

```bash
npx skills add https://github.com/konglong87/jargon -g
```

### 指定平台安装

```bash
npx skills add https://github.com/konglong87/jargon \
  --skill jargon \
  --agent claude-code cursor codex
```

> 需要 Node.js 和 npm。若你的 Agent 安装器参数略有不同，请以 `npx skills add --help` 的当前提示为准。

## Claude Code

```bash
npx skills add https://github.com/konglong87/jargon \
  --skill jargon \
  --agent claude-code
```

安装后，在 Claude Code 中直接描述需求，例如：

```text
做一个有质感的中文电商首页
```

Jargon 会先识别模糊词，再给出可选择的专业方向。确认后才生成最终执行提示词。

## Cursor

```bash
npx skills add https://github.com/konglong87/jargon \
  --skill jargon \
  --agent cursor
```

安装后，在 Cursor Chat 中直接描述需求即可。Jargon 会根据当前请求加载相关领域术语，不会一次性加载全部知识。

## Codex / OpenCode

```bash
npx skills add https://github.com/konglong87/jargon \
  --skill jargon \
  --agent codex opencode
```

如果目标工具没有自动识别 Skill，也可以手动加载 [`skills/jargon/SKILL.md`](skills/jargon/SKILL.md)。

## 使用方式

```text
用户白话
→ 识别领域
→ 匹配意图
→ 按需加载术语包
→ 语义匹配模糊表达
→ 输出专业候选和取舍
→ 用户确认
→ 生成增强提示词
```

例如：

```text
用户：我想做一个稳定的大型后端。

Jargon：
- “稳定”可以拆成高可用、容错、故障转移和可观测性。
- “大型”通常需要明确并发量、峰值流量和水平扩展策略。
- 还需要确认：是否要求幂等、限流、熔断和降级？
```

## 核心特点

- **按需加载**：只读取当前领域和意图相关的术语包。
- **语义匹配**：理解同义表达，例如“别轻易挂”“扛得住流量”“看起来高级”。
- **白话解释**：专业术语会同时给出普通用户能理解的说明。
- **明确取舍**：每个方向说明能得到什么、要牺牲什么。
- **确认后扩写**：用户确认之前，不把猜测当成最终要求。
- **搜索兜底**：没有覆盖时，可在用户允许后使用网络搜索；搜索结果只作为临时参考，不自动写入术语库。

## 项目结构

```text
index/
├── root.json       # 18 个根领域索引
└── packages.json   # 领域、意图和术语包索引

terms/              # 按领域拆分的术语列表
skills/jargon/
└── SKILL.md        # Agent 使用规则
```

术语包状态：

- `published`：可以被运行时直接加载。
- `draft`：维护中的草案，不应作为确定专业事实注入提示词。

## 手动安装

```bash
git clone https://github.com/konglong87/jargon.git
```

然后将 [`skills/jargon/SKILL.md`](skills/jargon/SKILL.md) 加载到你的 Agent 配置中，并让它读取仓库里的 `index/root.json`、`index/packages.json` 和对应的 `terms/*.json`。

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

不要提交密钥、令牌、个人路径或真实用户隐私。高风险领域的术语应绑定适用范围，并明确不能替代专业意见。

## License

[MIT](LICENSE)
