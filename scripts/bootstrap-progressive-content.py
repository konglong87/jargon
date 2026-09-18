#!/usr/bin/env python3
"""Create Jargon progressive indexes and granular knowledge packages."""
from __future__ import annotations
import json
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARSER = argparse.ArgumentParser(description="Bootstrap or refresh Jargon progressive indexes")
PARSER.add_argument(
    "--force",
    action="store_true",
    help="regenerate existing leaf JSON from the embedded bootstrap catalog",
)
ARGS = PARSER.parse_args()

def dump(path: str, data: dict) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)

def adopt_existing_leaf(spec: dict) -> None:
    """Treat an existing leaf JSON as authored content unless --force is used."""
    target = ROOT / spec["path"]
    if not target.is_file() or ARGS.force is True:
        dump(spec["path"], {
            "schema_version": "1.0.0",
            **{key: value for key, value in spec.items() if key not in {"path", "entries"}},
            "entries": spec["entries"],
        })
        return
    existing = read_json(target)
    required = ("leaf_id", "domain_id", "subdomain_id", "title", "knowledge_type", "status", "intent_ids", "entries")
    missing = [key for key in required if key not in existing]
    if missing:
        raise ValueError(f"leaf {spec['path']} is missing required fields: {', '.join(missing)}")
    existing["path"] = spec["path"]
    existing.setdefault("scope", "general")
    existing.setdefault("do_not_generalize", False)
    spec.clear()
    spec.update(existing)

def discover_authored_leaves() -> None:
    """Include manually added granular leaves in the next generated index."""
    for path in sorted((ROOT / "terms").rglob("*.json")):
        relative = path.relative_to(ROOT).as_posix()
        if len(path.relative_to(ROOT / "terms").parts) == 1:
            continue
        data = read_json(path)
        leaf_id = data.get("leaf_id")
        if not leaf_id or leaf_id in leaf_defs:
            continue
        required = ("domain_id", "subdomain_id", "title", "knowledge_type", "status", "intent_ids", "entries")
        if all(key in data for key in required):
            data.setdefault("scope", "general")
            data.setdefault("do_not_generalize", False)
            leaf_defs[leaf_id] = {"path": relative, **data}

# Keep root/package indexes backward compatible while publishing the progressive loader policy.
root = json.loads((ROOT / "index/root.json").read_text(encoding="utf-8"))
root["schema_version"] = "2.0.0"
root["loading_policy"] = {
    "strategy": "progressive",
    "levels": ["root", "subdomain", "intent", "leaf", "entry"],
    "max_subdomains": 3,
    "max_intents": 3,
    "max_intents_scope": "per_subdomain",
    "max_leaf_packages": 8,
    "max_entries_per_leaf": 30,
    "search_fallback": "ask-before-network",
}
domain_specs = {
    "digital-product-uiux": [
        ("visual-layout", "视觉布局", "卡片、留白、非对称和出血布局"),
        ("design-tokens", "设计令牌", "颜色、字体、圆角、阴影和间距"),
        ("interaction-motion", "交互动效", "时间、速度、连续性和反馈"),
        ("gesture-interaction", "手势交互", "跟随、阈值、吸附和手势采样"),
        ("information-architecture", "信息架构", "导航、层级、密度和内容组织"),
        ("accessibility", "可访问性", "键盘、读屏、减少动态和状态表达"),
        ("dashboard-design", "Dashboard 设计", "数据后台的视觉方向和布局"),
        ("component-design", "组件设计", "可复用组件和 AI 组件描述"),
        ("3d-web-interface", "3D Web 界面", "实时 3D 和 GPU 视觉界面"),
    ],
    "ai-aigc-meta-skills": [
        ("image-prompt", "图像提示词", "主体、材质、光线和构图"),
        ("video-prompt", "视频提示词", "镜头、运动、声音和节奏"),
        ("character-ip", "角色 IP", "角色一致性、三视图和衍生物"),
        ("material-style", "材质与风格", "毛绒、PVC、纸张和渲染质感"),
        ("camera-language", "镜头语言", "景别、焦段、机位和运镜"),
        ("composition", "构图", "主体位置、留白和视觉动线"),
        ("motion-control", "运动控制", "动作、跟随、速度和镜头运动"),
        ("negative-prompt", "负面约束", "变形、漂移、重复和违规输出"),
        ("tool-adapter", "工具适配", "通用、Midjourney 和 Stable Diffusion 参数"),
    ],
    "software-engineering-architecture": [
        ("backend-architecture", "后端架构", "服务边界、状态和数据流"),
        ("high-availability", "高可用", "冗余、故障域、RTO 和 RPO"),
        ("high-concurrency", "高并发", "流量模型、延迟和资源隔离"),
        ("scalability", "高扩展", "水平扩展、分片、缓存和异步化"),
        ("observability", "可观测性", "SLI、SLO、日志、指标和追踪"),
        ("idempotency", "幂等", "操作身份、重试和重复请求"),
        ("frontend-platform", "前端平台", "组件、构建、运行时和交付"),
        ("desktop-web-mobile", "桌面 Web 移动端", "跨平台渲染与能力边界"),
    ],
    "workplace-communication": [
        ("vague-expression", "模糊表达", "把职场黑话翻译成可执行需求"),
        ("project-collaboration", "项目协作", "角色、依赖、风险和决策"),
        ("goal-alignment", "目标对齐", "目标、指标、范围和优先级"),
        ("execution-language", "执行语言", "下一步、负责人、截止时间和验收"),
        ("management-terms", "管理术语", "组织、机制、复盘和资源配置"),
    ],
}
# Small generic subdomain skeletons keep all roots progressively addressable without pretending coverage.
for domain in root["domains"]:
    domain_id = domain["domain_id"]
    domain_specs.setdefault(domain_id, [("core", "核心入口", "该领域的渐进式术语入口，内容持续扩充")])
for domain in root["domains"]:
    domain_id = domain["domain_id"]
    domain["subdomain_index"] = f"index/domains/{domain_id}.json"
    domain["loading_hint"] = "先匹配子域，再读取最小叶子包"
dump("index/root.json", root)

# Intent groups are deliberately small: they are a routing layer, not a knowledge dump.
intent_defaults = {
    "visual-layout": [("design-layout", "设计", "页面布局"), ("audit-layout", "评审", "布局问题")],
    "information-architecture": [("design-information", "设计", "信息架构"), ("audit-information", "评审", "信息层级")],
    "design-tokens": [("define-tokens", "定义", "设计令牌"), ("audit-tokens", "审计", "令牌一致性")],
    "interaction-motion": [("design-interaction", "设计", "交互动效"), ("implement-animation", "实现", "动画反馈"), ("audit-motion", "评审", "动效质量")],
    "gesture-interaction": [("design-gesture", "设计", "手势交互"), ("implement-gesture", "实现", "手势组件"), ("audit-gesture", "评审", "手感问题")],
    "dashboard-design": [("design-dashboard", "设计", "数据后台"), ("audit-dashboard", "评审", "后台审美")],
    "component-design": [("generate-component", "生成", "UI 组件"), ("spec-component", "规范", "组件需求")],
    "3d-web-interface": [("compare-platform", "比较", "平台能力"), ("choose-renderer", "选择", "渲染后端")],
    "accessibility": [("audit-accessibility", "审计", "可访问性"), ("implement-accessibility", "实现", "无障碍能力")],
    "character-ip": [("generate-character", "生成", "角色 IP"), ("extend-character", "延展", "角色周边")],
    "image-prompt": [("write-image-prompt", "编写", "图像提示词"), ("audit-image-prompt", "检查", "图像提示词")],
    "video-prompt": [("write-video-prompt", "编写", "视频提示词"), ("audit-video-prompt", "检查", "视频提示词")],
    "material-style": [("write-image-prompt", "编写", "材质提示词")],
    "camera-language": [("write-image-prompt", "编写", "镜头语言"), ("write-video-prompt", "编写", "镜头语言")],
    "composition": [("write-image-prompt", "编写", "构图语言"), ("audit-image-prompt", "检查", "构图语言")],
    "motion-control": [("write-video-prompt", "编写", "运动控制")],
    "negative-prompt": [("write-image-prompt", "编写", "负面约束"), ("audit-image-prompt", "检查", "负面约束")],
    "tool-adapter": [("write-image-prompt", "编写", "工具适配"), ("write-video-prompt", "编写", "工具适配")],
    "backend-architecture": [("design-backend", "设计", "后端架构"), ("review-backend", "评审", "后端方案")],
    "high-availability": [("design-ha", "设计", "高可用"), ("audit-ha", "演练", "故障恢复")],
    "high-concurrency": [("model-capacity", "建模", "并发容量"), ("tune-performance", "优化", "性能")],
    "scalability": [("design-scale", "设计", "扩展策略"), ("plan-migration", "规划", "容量迁移")],
    "observability": [("define-slo", "定义", "SLO"), ("debug-production", "排障", "线上故障")],
    "idempotency": [("design-idempotency", "设计", "幂等契约"), ("diagnose-duplicate", "排查", "重复写入")],
    "frontend-platform": [("design-frontend", "设计", "前端平台"), ("audit-frontend", "评审", "前端平台")],
    "desktop-web-mobile": [("compare-platform", "比较", "平台能力"), ("choose-renderer", "选择", "渲染后端")],
    "vague-expression": [("clarify-vague", "澄清", "模糊表达"), ("rewrite-actionable", "改写", "可执行表达")],
    "project-collaboration": [("align-collaboration", "对齐", "项目协作"), ("resolve-dependency", "解决", "协作依赖")],
    "goal-alignment": [("define-goal", "定义", "目标"), ("review-priority", "评审", "优先级")],
    "execution-language": [("write-action", "编写", "执行项"), ("review-status", "复盘", "状态汇报")],
    "management-terms": [("explain-term", "解释", "管理术语"), ("translate-jargon", "翻译", "组织黑话")],
}

# Granular knowledge content. Every leaf is independently loadable.
leaf_defs = {}
def add_leaf(path, leaf_id, domain_id, subdomain_id, title, knowledge_type, entries, intent_ids=None, scope="general", extra=None):
    leaf_defs[leaf_id] = {
        "path": path,
        "leaf_id": leaf_id,
        "domain_id": domain_id,
        "subdomain_id": subdomain_id,
        "title": title,
        "knowledge_type": knowledge_type,
        "scope": scope,
        "status": "published",
        "intent_ids": intent_ids or [],
        "entries": entries,
        **(extra or {}),
    }

# Shared helpers.
def entry(eid, name, plain, when, params=None, related=None, constraints=None, aliases=None):
    return {
        "id": eid, "name": name, "plain_language": plain, "when_to_use": when,
        "parameters": params or [], "related": related or [], "constraints": constraints or [], "aliases": aliases or []
    }

interaction_dir = "terms/interaction"
add_leaf(f"{interaction_dir}/undo-window.json", "undo-window", "digital-product-uiux", "interaction-motion", "撤销时间窗口", "technique", [
    entry("undo-window", "可逆操作时间窗口", "删除后保留一段明确的可撤销时间，让用户有机会反悔。", "删除、归档、批量移除等可逆操作", ["窗口默认 5s；高风险操作 8–10s", "过期后按钮禁用并完成最终删除"], ["progress-feedback", "reverse-animation"], ["不要让过期后仍看起来可点击"]),
    entry("progress-feedback", "线性进度反馈", "进度条或进度环的完成时间与撤销窗口完全一致。", "需要让剩余时间可见", ["动画使用 linear", "数字可每秒更新，进度动画保持连续"], ["undo-window"], ["不能用缓动制造错误的剩余时间感"]),
    entry("pause-on-focus", "聚焦暂停窗口", "用户悬停或键盘聚焦撤销控件时暂停倒计时。", "误操作成本高且需要可访问性增强的场景", ["暂停状态必须可见", "失焦后继续倒计时"], ["accessibility"], ["不能无限暂停导致资源长期占用"]),
], ["design-interaction", "audit-motion"], extra={"loading_note": "撤销功能只需加载本叶子和反向动画，不加载全部动效"})
add_leaf(f"{interaction_dir}/reverse-animation.json", "reverse-animation", "digital-product-uiux", "interaction-motion", "撤销反向动画", "technique", [
    entry("reverse-path", "沿原路径反向归位", "撤销时沿删除动画的反方向回到原位置，而不是重新淡入。", "列表删除后恢复原项", ["删除缩小+位移+淡出，撤销放大+反向位移+淡入", "删除 200–300ms，撤销 180–240ms"], ["flip-reentry", "velocity-inheritance"], ["必须保留原索引、尺寸和位置上下文"]),
    entry("reentry-highlight", "归位确认高亮", "元素回到原位后增加短暂高亮或脉冲，确认它确实回来了。", "撤销后的状态需要被快速识别", ["高亮 500–700ms", "不改变布局"], ["reverse-path"], ["不要用强烈闪烁造成干扰"]),
    entry("reduced-motion", "减少动态降级", "减少动态时保留进度、状态和结果，不强制播放位移动画。", "用户开启 prefers-reduced-motion", ["保留明确状态变化", "取消复杂路径和粒子"], ["accessibility"], ["不可因为降级而丢失撤销入口"]),
], ["implement-animation", "audit-motion"])
add_leaf(f"{interaction_dir}/flip-reentry.json", "flip-reentry", "digital-product-uiux", "interaction-motion", "FLIP 反向归位", "technique", [
    entry("flip", "First Last Invert Play", "记录删除前后布局，撤销时把真实节点插回原索引，再播放反向变换。", "列表重排、共享元素和复杂布局撤销", ["First 记录原位置尺寸", "Last 记录重排后位置", "Invert 计算差值", "Play 播放反向变换"], ["reverse-path", "shared-element-transition"], ["节点已移除时保留 ghost/clone 或占位符"]),
    entry("placeholder", "占位与真实节点回插", "节点暂时移除后保留占位，撤销时按原索引插回真实节点。", "DOM 节点生命周期较短的列表", ["恢复原索引", "其他项让位动画"], ["flip"], ["不能把 ghost 当作最终业务节点"]),
], ["implement-animation"])
add_leaf(f"{interaction_dir}/accessibility.json", "motion-accessibility", "digital-product-uiux", "accessibility", "动效可访问性", "guideline", [
    entry("undo-aria", "撤销按钮可读标签", "按钮要读出操作和剩余时间，例如撤销删除，剩余 5 秒。", "撤销条、倒计时按钮", ["aria-label 动态更新", "键盘可聚焦和触发"], ["undo-window"], ["不要每秒通过 aria-live 播报倒计时"]),
    entry("undo-live", "轻量状态播报", "用 aria-live=polite 提示已删除、可撤销等关键状态。", "操作结果需要被读屏用户感知", ["只播报状态变化", "焦点不被撤销条抢走"], ["undo-aria"], ["不重复播报相同状态"]),
], ["audit-accessibility", "implement-accessibility"])

shared_entries = {
    "follow": [entry("follow", "跟随", "元素连续继承输入位置或速度，不瞬间跳到新状态。", "拖拽、滚动、转场和惯性动作", ["位置或速度 1:1 跟随", "必要时使用 lerp 或 spring 收敛"], ["threshold", "velocity-inheritance"], ["高频输入不能依赖昂贵布局重排"])],
    "threshold": [entry("threshold", "阈值", "达到位移、速度或双条件后才触发状态切换。", "半屏弹层、长按拖拽、粘连断开", ["明确位移阈值", "明确速度阈值", "可加入迟滞避免抖动"], ["snap", "follow"], ["不轻易触发，也不突然失效"])],
    "snap": [entry("snap", "吸附", "松手后把连续输入收敛到明确落点。", "滚轮、底部抽屉、滑块和拖拽", ["根据位置和速度选择锚点", "终点接管要平滑"], ["threshold", "velocity-inheritance"], ["不要硬跳到终点"])],
    "velocity-inheritance": [entry("velocity-inheritance", "速度继承", "松手后继续沿当前速度运动，再减速并吸附。", "惯性滚动、抽屉和抛物线飞入", ["保存释放瞬间速度", "设置 friction 和最大位移"], ["follow", "snap"], ["速度必须有上限，避免失控"])],
    "interruption": [entry("interruption", "可中断与恢复", "动画中途再次输入时接管当前状态，而不是等待旧动画结束。", "可拖拽、可快速连点或可反悔的组件", ["读取当前 transform", "取消旧动画并从当前状态继续"], ["follow", "reverse-animation"], ["不能产生双重回调或状态竞态"])],
}
for leaf_id, entries in shared_entries.items():
    add_leaf(f"{interaction_dir}/{leaf_id}.json", leaf_id, "digital-product-uiux", "gesture-interaction", entries[0]["name"], "principle", entries, ["design-gesture", "implement-gesture", "audit-gesture"])

interaction_12 = {
    "spring-press": ("Spring 按压回弹", "按下缩到 0.96–0.98，松手用弹簧回到 1 并允许 1.02–1.04 的轻微过冲。", ["scale 0.96–0.98", "overshoot 2%–4%", "可叠加内阴影或明度变化"]),
    "squash-toggle": ("Squash 弹性开关", "开关起步横向拉伸、纵向压缩，再回到正常比例。", ["scaleX 1.08", "scaleY 0.94", "180–240ms", "transform-origin 与方向一致"]),
    "ripple-button": ("Ripple 水波按钮", "从真实触点向最远角扩散水波，不把点击中心固定在控件中心。", ["400–600ms", "半径覆盖最远角", "移动端用 worklet/WXS 获取坐标"]),
    "burst-feedback": ("Burst 点击爆散", "关键点击用 6–12 个短寿命粒子表达完成或奖励。", ["寿命 300–500ms", "随机角度", "轻微重力", "只用于关键动作"]),
    "draw-success": ("Draw 成功勾选", "先画圆再画勾，用 SVG 描边过程表达成功。", ["stroke-dasharray", "stroke-dashoffset", "400–700ms"]),
    "liquid-slider": ("Liquid 液态滑块", "轨道、滑钮和数值使用同一弹簧同步变化。", ["同一 spring", "零延迟跟手", "轨道与数值同步"]),
    "count-animation": ("Count 数字滚动", "数字按位滚动并在最后一段明显减速。", ["tabular-nums", "cubic-bezier(0.16,1,0.3,1)", "固定宽度"]),
    "skeleton-shimmer": ("Shimmer 骨架落位", "骨架尺寸与真实内容一致，内容到达后平滑替换。", ["1.2–1.6s 循环", "高度、行高、间距一致"]),
    "card-flip": ("3D 卡片翻面", "正反面围绕同一中心翻转，保持透视和背面隐藏。", ["perspective 800–1200", "backface-visibility hidden", "iOS 加 webkit 前缀"]),
    "morph-icon": ("Morph 汉堡变叉", "使用同路径或线段位移旋转完成图标变形。", ["200–300ms", "同点数或明确线段映射"]),
    "stack-card": ("Stack 卡片抽走", "抽走前卡时露出后卡的缩放和位移层级。", ["scale 0.94/0.88", "translateY 8/16", "后卡必须露边"]),
    "bottom-sheet": ("阻尼弹性底部抽屉", "支持下拉、橡皮筋和多个锚点吸附。", ["closed/peek/half/full", "按位移+速度选锚点", "处理滚动穿透"]),
}
for leaf_id, (name, plain, params) in interaction_12.items():
    subdomain_id = "interaction-motion" if leaf_id != "bottom-sheet" else "gesture-interaction"
    intent_ids = ["design-interaction", "implement-animation"] if subdomain_id == "interaction-motion" else ["design-gesture", "implement-gesture"]
    add_leaf(f"{interaction_dir}/{leaf_id}.json", leaf_id, "digital-product-uiux", subdomain_id, name, "pattern", [entry(leaf_id, name, plain, "需要高级反馈但仍要保持可理解的操作结果", params, ["follow", "threshold", "snap", "interruption"])], intent_ids)

# Dashboard terms and reusable style template.
dashboard_entries = {
    "warm-minimal": ("暖调留白型", "奶油底色、单一黄色强调、细边框和弱阴影，保留呼吸感。", ["#F7F3EA", "一个主强调色", "圆角克制", "弱阴影"]),
    "high-contrast": ("强对比视觉型", "一张主卡占据视觉中心，用高饱和对比和大数字建立层级。", ["主卡占视觉中心", "硬阴影", "大数字", "非对称"]),
    "minimal-data": ("极简数据型", "以灰阶和一个强调色组织数据，去网格线和多余标签。", ["灰阶为主", "胶囊柱状图", "标签精简"]),
    "immersive-atmosphere": ("氛围沉浸型", "深色底、雾面渐变、玻璃卡片和轻微动态光斑。", ["GPU 负载预算", "移动端降级", "模糊光斑"]),
    "image-led-content": ("图卡内容型", "让真实图片成为主角，文字叠加且只保留一个强调色。", ["大图卡片", "文字叠加", "单一 CTA 色"]),
    "layout-patterns": ("高级布局模式", "用错位、大图、非对称、层叠、留白和破格出血建立布局性格。", ["错位按 8/12/16px 节奏", "7:3 或 8:2 比例", "只破一处网格", "安全区内留信息"]),
}
for leaf_id, (name, plain, params) in dashboard_entries.items():
    add_leaf(f"terms/dashboard/{leaf_id}.json", leaf_id, "digital-product-uiux", "dashboard-design", name, "pattern", [entry(leaf_id, name, plain, "Dashboard 需要有明确审美方向且避免模板化", params, ["design-tokens", "layout-patterns"], ["不要所有卡片一样大", "不要默认蓝紫渐变", "不要模板化侧边栏+四张 KPI 卡"])], ["design-dashboard", "audit-dashboard"])

dump("templates/dashboard/dashboard-style-system.json", {
    "schema_version": "1.0.0", "template_id": "dashboard-style-system", "name": "Dashboard 审美 Skill", "type": "template",
    "inputs": ["product_or_scene", "style_direction", "content_priority"],
    "style_directions": [{"id": k, "name": v[0], "rule": v[1], "tokens": v[2]} for k, v in dashboard_entries.items()],
    "output_contract": ["页面结构", "色彩规范", "组件规范", "可直接给 AI 的提示词"],
    "forbidden_defaults": ["默认蓝紫渐变", "所有卡片一样大", "满屏圆角矩形", "过多颜色和图标", "模板化侧边栏+顶栏+四张 KPI 卡"]
})

# Eight AI-feedable component descriptions.
components = {
    "tilt-light-panel": ("3D 倾斜光影面板", "监听 pointermove/touchmove 计算 rotateX/rotateY，最大倾斜 8–12°，叠加随指针移动的径向高光，松手用 Spring 回正。", ["pointer tracking", "perspective", "preserve-3d", "radial-gradient", "spring damping"]),
    "fluid-capsule-morph": ("流体胶囊形变", "胶囊按钮通过 FLIP/shared layout 形变为弹窗，圆角从 999px 过渡到 24px，内容延迟淡入并带遮罩。", ["fluid morph", "FLIP", "layout animation", "border-radius morph"]),
    "shared-element-expand": ("共享元素无缝展开", "列表卡片到详情页使用同一 layoutId，图片、标题和容器连续缩放，背景遮罩淡入，避免跳变。", ["shared element transition", "layoutId", "matched geometry", "continuous scale"]),
    "magnetic-cursor-odometer": ("磁吸游标与滚动码表", "折线图拖拽时数据点磁吸，顶部数值使用 Odometer 按位滚动，拖拽、吸附和数值用 lerp+spring 联动。", ["magnetic snap", "odometer", "tabular-nums", "lerp", "spring follow"]),
    "damped-bottom-sheet": ("阻尼弹性抽屉", "Bottom Sheet 根据位移和速度在 closed/peek/half/full 锚点间吸附，越界呈 rubber band 回弹。", ["rubber band", "velocity projection", "snap points", "spring snap"]),
    "diffused-glow-border": ("动态弥散光晕边框", "用 conic-gradient 旋转描边，叠加 blur+opacity 呼吸背光，并用 mask 保留描边区域。", ["conic-gradient", "breathing glow", "blur halo", "mask composite"]),
    "spring-stagger-flow": ("物理弹簧交错流", "列表子项按 index*0.03–0.06s 交错，从 y:20、opacity:0 进入并带轻微 spring。", ["staggerChildren", "spring cascade", "y-offset", "stagger delay"]),
    "elastic-press-feedback": ("弹性微缩触觉反馈", "按钮按压缩到 0.96 并增加内阴影，释放时 Spring 轻微超调回 1，支持快速连点。", ["whileTap", "scale 0.96", "inset shadow", "spring overshoot"]),
}
for leaf_id, (name, plain, params) in components.items():
    add_leaf(f"terms/component-design/{leaf_id}.json", leaf_id, "digital-product-uiux", "component-design", name, "template", [entry(leaf_id, name, plain, "需要给 AI 编程或设计工具描述可复用组件", params, ["follow", "interruption"])], ["generate-component", "spec-component"])

# Fill the adjacent UI/UX subdomains so routing can become finer without loading a
# monolithic UI package.
add_leaf("terms/visual-layout/composition-patterns.json", "composition-patterns", "digital-product-uiux", "visual-layout", "高级布局六式", "pattern", [
    entry("composition-patterns", "卡片错位/大图主导/非对称/层叠/留白/破格出血", "用比例、层级和安全区建立页面性格；每次只让少数元素破格。", "首屏、活动页、详情页和内容信息流", ["错位按 8/12/16px 节奏", "主图可占半屏或出血", "使用 7:3 或 8:2 非对称", "只破一处网格，内容留在安全区"], ["layout-patterns", "design-tokens"], ["错位无规律会像未对齐", "出血过多会削弱秩序", "留白必须仍有视觉焦点"])
], ["design-layout", "audit-layout"])
add_leaf("terms/design-tokens/token-system.json", "token-system", "digital-product-uiux", "design-tokens", "设计令牌系统", "parameter", [
    entry("token-system", "底色/强调色/层级/材质/主角五变量", "Dashboard 的审美方向主要由底色、强调色、布局层级、材质和内容主角决定。", "需要让 AI 生成非模板化后台或设计系统", ["背景色", "主强调色", "文字层级", "圆角/阴影", "卡片材质", "内容主角"], ["dashboard-style-system", "composition-patterns"], ["先定 token 再定组件，不要每张卡单独发明规则"])
], ["define-tokens", "audit-tokens"])
add_leaf("terms/information-architecture/information-hierarchy.json", "information-hierarchy", "digital-product-uiux", "information-architecture", "信息层级与密度", "principle", [
    entry("information-hierarchy", "信息层级", "先确定用户要做的决定，再按主次组织标题、数据、操作和辅助说明。", "复杂后台、内容页和移动端首页", ["主任务优先", "每屏保留一个视觉主角", "用密度和留白表达层级"], ["composition-patterns", "token-system"], ["不要用颜色和图标堆叠替代结构"])
], ["design-information", "audit-information"])

# AIGC is split by prompt concern so a character request does not load camera,
# negative-prompt and tool adapter knowledge at once.
add_leaf("terms/image-prompt/prompt-blocks.json", "prompt-blocks", "ai-aigc-meta-skills", "image-prompt", "图像提示词模块", "template", [
    entry("prompt-blocks", "主体/材质/光线/构图/质量模块", "把图像提示词拆为可重排模块，先锁主体，再补材质、光线、构图和质量。", "文生图、参考图重绘和产品效果图", ["subject", "material", "lighting", "composition", "quality"], ["character-ip", "negative-constraints"], ["不要把所有风格词混成一段无层级文本"])
], ["write-image-prompt", "audit-image-prompt"])
add_leaf("terms/video-prompt/video-direction.json", "video-direction", "ai-aigc-meta-skills", "video-prompt", "视频镜头与运动描述", "template", [
    entry("video-direction", "镜头/主体运动/声音三层描述", "视频提示词至少拆成景别、镜头运动、主体动作、节奏和声音。", "文生视频和分镜生成", ["shot", "camera_motion", "subject_motion", "tempo", "sound"], ["camera-language", "motion-language"], ["不要只写电影感而不说明可观察的镜头行为"])
], ["write-video-prompt", "audit-video-prompt"])
add_leaf("terms/material-style/material-library.json", "material-library", "ai-aigc-meta-skills", "material-style", "材质风格词", "term", [
    entry("material-library", "材质与反射", "用可观察的表面属性描述材质，例如高光泽釉面、短植绒、哑光纸张和半通透胶带。", "产品渲染、角色周边和材质迁移", ["roughness", "specular", "translucency", "texture"], ["prompt-blocks", "character-ip"], ["材质词不能替代主体和结构约束"])
], ["write-image-prompt"])
add_leaf("terms/camera-language/camera-language.json", "camera-language", "ai-aigc-meta-skills", "camera-language", "镜头语言", "term", [
    entry("camera-language", "景别/机位/焦段/运镜", "把电影感拆成可执行的景别、机位、焦段、景深和运动。", "想要电影感但需要稳定复现时", ["close/medium/wide", "high/low angle", "lens", "depth of field", "camera motion"], ["video-direction", "composition"], ["不要用受版权保护的具体作品名作为唯一指令"])
], ["write-image-prompt", "write-video-prompt"])
add_leaf("terms/composition/composition-language.json", "composition-language", "ai-aigc-meta-skills", "composition", "构图语言", "term", [
    entry("composition-language", "主体位置与视觉动线", "用中心、三分、对称、留白、前中后景和视觉引导线描述构图。", "需要主体位置和画面平衡可控时", ["subject placement", "negative space", "foreground/midground/background", "leading lines"], ["camera-language", "prompt-blocks"], ["构图要服务内容主角，不要为了术语堆叠"])
], ["write-image-prompt", "audit-image-prompt"])
add_leaf("terms/motion-control/motion-language.json", "motion-language", "ai-aigc-meta-skills", "motion-control", "动作与运动控制", "technique", [
    entry("motion-language", "方向/速度/幅度/节奏", "明确主体怎么动、镜头怎么动、速度和幅度如何变化。", "文生视频、产品动效和角色动作延展", ["direction", "speed", "amplitude", "rhythm", "follow"], ["video-direction", "velocity-inheritance"], ["动作必须可观察，避免只写情绪形容词"])
], ["write-video-prompt"])
add_leaf("terms/negative-prompt/negative-constraints.json", "negative-constraints", "ai-aigc-meta-skills", "negative-prompt", "负面约束", "guideline", [
    entry("negative-constraints", "结构/材质/一致性负面词", "把不希望出现的变形、额外肢体、颜色漂移、重复主体和低清晰度写成约束。", "角色一致性、产品渲染和批量出图", ["结构禁用", "材质禁用", "画面质量禁用"], ["character-ip", "prompt-blocks"], ["负面词不能掩盖主体描述不完整"])
], ["write-image-prompt", "audit-image-prompt"])
add_leaf("terms/tool-adapter/tool-parameters.json", "tool-parameters", "ai-aigc-meta-skills", "tool-adapter", "工具参数适配", "template", [
    entry("tool-parameters", "通用/Midjourney/SD 适配", "把同一套提示词拆成通用正文、画幅参数和工具专用控制字段。", "需要在多个生图工具间复用提示词", ["aspect_ratio", "style", "negative_prompt", "controlnet"], ["prompt-blocks", "negative-constraints"], ["工具参数是适配层，不改变核心语义"])
], ["write-image-prompt", "write-video-prompt"])

# Backend architecture is split into independently retrievable reliability concerns.
backend_leaves = {
    "service-boundary": ("backend-architecture", "服务边界与状态", "把服务职责、同步/异步边界、状态归属和数据一致性写清楚。", ["service ownership", "sync/async", "state ownership", "consistency"]),
    "availability-patterns": ("high-availability", "高可用模式", "跨实例、节点或可用区部署关键组件，并定义 RTO/RPO 和故障转移。", ["failure domain", "redundancy", "RTO", "RPO", "failover"]),
    "capacity-model": ("high-concurrency", "并发容量模型", "用平均值、峰值、突发、P95/P99 和增长率描述高并发，而不是只说高并发。", ["RPS", "burst", "P95/P99", "growth rate"]),
    "scaling-strategies": ("scalability", "扩展策略", "按无状态实例、缓存、分片和异步队列拆解增长路径。", ["horizontal scaling", "sharding", "cache", "async"]),
    "observability-contract": ("observability", "可观测性契约", "将 SLI/SLO、日志、指标、追踪、告警和故障演练绑定到服务目标。", ["SLI", "SLO", "logs", "metrics", "traces", "alerts"]),
    "idempotency-contract": ("idempotency", "幂等契约", "用操作身份、同键重试、内容一致性、并发响应和结果关联定义重复处理。", ["operation key", "retry", "payload match", "in-progress", "result record"]),
    "frontend-runtime": ("frontend-platform", "前端平台边界", "把组件、构建、运行时、发布和回滚能力作为平台契约。", ["component API", "build", "runtime", "release", "rollback"]),
    "cross-platform-rendering": ("desktop-web-mobile", "跨平台渲染边界", "按平台能力、渲染后端、输入方式和降级路径选择实现策略。", ["desktop", "web", "mobile", "renderer", "fallback"]),
}
backend_intents = {
    "backend-architecture": ["design-backend", "review-backend"],
    "high-availability": ["design-ha", "audit-ha"],
    "high-concurrency": ["model-capacity", "tune-performance"],
    "scalability": ["design-scale", "plan-migration"],
    "observability": ["define-slo", "debug-production"],
    "idempotency": ["design-idempotency", "diagnose-duplicate"],
    "frontend-platform": ["design-frontend", "audit-frontend"],
    "desktop-web-mobile": ["compare-platform", "choose-renderer"],
}
for leaf_id, (subdomain, title, plain, params) in backend_leaves.items():
    add_leaf(f"terms/software-engineering/{leaf_id}.json", leaf_id, "software-engineering-architecture", subdomain, title, "term", [
        entry(leaf_id, title, plain, "后端或平台方案需要拆解质量属性时", params, ["high-availability", "capacity-model", "scaling-strategies", "observability-contract", "idempotency-contract"], ["不要把质量属性当作无边界承诺"])
    ], backend_intents[subdomain])

# Workplace language stays explanatory: it translates vague phrases into questions,
# actions and acceptance criteria rather than preserving empty slogans.
workplace_leaves = {
    "jargon-translation": ("vague-expression", "职场黑话翻译", "把“拉齐、抓手、闭环、赋能”等模糊词翻译为对象、动作、负责人和结果。", ["原句", "真实对象", "动作", "负责人", "验收标准"]),
    "dependency-alignment": ("project-collaboration", "项目依赖对齐", "明确依赖方、输入、输出、阻塞风险和升级路径。", ["依赖方", "输入", "输出", "截止时间", "升级路径"]),
    "goal-metric": ("goal-alignment", "目标与指标", "把方向性目标拆成可观察结果、指标口径、范围和优先级。", ["目标", "指标", "口径", "范围", "优先级"]),
    "action-item": ("execution-language", "执行项", "每个执行项写清负责人、下一步、截止时间和完成证据。", ["owner", "next step", "due date", "evidence"]),
    "management-mechanism": ("management-terms", "管理机制", "把机制、复盘、资源配置和组织动作落到可观察的流程。", ["机制", "触发条件", "参与者", "输出", "复盘"]),
}
for leaf_id, (subdomain, title, plain, params) in workplace_leaves.items():
    workplace_intents = {
        "vague-expression": ["clarify-vague", "rewrite-actionable"],
        "project-collaboration": ["align-collaboration", "resolve-dependency"],
        "goal-alignment": ["define-goal", "review-priority"],
        "execution-language": ["write-action", "review-status"],
        "management-terms": ["explain-term", "translate-jargon"],
    }
    add_leaf(f"terms/workplace/{leaf_id}.json", leaf_id, "workplace-communication", subdomain, title, "term", [
        entry(leaf_id, title, plain, "用户说出职场模糊表达或需要改写协作要求时", params, ["information-hierarchy", "goal-metric"], ["不替用户猜测未提供的事实"])
    ], workplace_intents[subdomain])

# Platform research is intentionally scoped and non-generalized.
platforms = {
    "gpui-desktop-web": ("GPUIX 桌面与 Web 平台研究", "provider-specific", "待核验的桌面/Web 平台适配记录；不得推广为所有 GPU UI 框架事实。", ["macOS/Metal", "Windows/DirectX", "Linux/Vulkan", "WebGPU/WebGL2 降级"]),
    "gpui-mobile": ("GPUIX 移动端平台研究", "provider-specific", "移动端支持状态需以官方仓库和版本为准；社区实现不能等同官方支持。", ["iOS/Metal", "Android/Vulkan 或 GL", "触摸、软键盘、安全区"]),
    "three-ui-catalog": ("ThreeUI 组件目录研究", "provider-specific", "目录分类用于检索组件，不代表所有组件都适合生产环境。", ["Landing Pages", "Hero", "Backgrounds", "Buttons", "Text Animation", "Three.js", "UI Elements", "CSS/Motion/Sections"]),
}
for leaf_id, (title, scope, plain, params) in platforms.items():
    add_leaf(f"terms/platform-research/{leaf_id}.json", leaf_id, "digital-product-uiux", "3d-web-interface", title, "platform-research", [entry(leaf_id, title, plain, "用户明确询问指定平台或组件目录", params, [], ["必须标注 provider-specific", "检索时优先官方来源", "verified_at 未设置时不得当作确定事实"])], ["compare-platform", "choose-renderer"], scope=scope, extra={"do_not_generalize": True, "verified_at": None, "verification_required": True})

add_leaf("terms/character-ip/character-ip.json", "character-ip", "ai-aigc-meta-skills", "character-ip", "角色 IP 一致性", "template", [
    entry("base-ip", "基础 IP 设定", "先锁定角色体型、配色、五官、材质和负面约束，再按场景增量加载。", "同一角色需要生成三视图、动作、服装、表情或周边", ["主体描述", "一致性规则", "负面提示词", "参考图"], ["lineart-to-3d", "plush-texture", "merchandise-set"], ["一次只加载一个场景模板"]),
    entry("scene-module", "场景增量模块", "把材质、动作、镜头或周边作为独立模块叠加到基础 IP。", "需要复用角色但更换表现目标", ["scene_id", "aspect_ratio", "tool_adapter"], ["base-ip"], ["不要重复复制完整基础 IP"]),
], ["generate-character", "extend-character"])

# Index all target leaves.
discover_authored_leaves()
for spec in leaf_defs.values():
    domain_id = spec["domain_id"]
    subdomain_id = spec["subdomain_id"]
    if domain_id not in domain_specs:
        continue
    known_subdomains = {item[0] for item in domain_specs[domain_id]}
    if subdomain_id not in known_subdomains:
        domain_specs[domain_id].append(
            (subdomain_id, spec["title"], f"手工新增的 {subdomain_id} 叶子入口")
        )
leaf_refs = []
for leaf_id, spec in sorted(leaf_defs.items()):
    adopt_existing_leaf(spec)
    leaf_refs.append({
        "leaf_id": leaf_id, "title": spec["title"], "path": spec["path"], "domain_id": spec["domain_id"], "subdomain_id": spec["subdomain_id"],
        "knowledge_type": spec["knowledge_type"], "status": spec["status"], "intent_ids": spec["intent_ids"], "scope": spec["scope"],
        "entry_count": len(spec["entries"]), "do_not_generalize": spec.get("do_not_generalize", False)
    })

dump("index/leaves.json", {"schema_version": "1.0.0", "knowledge_types": ["term", "pattern", "technique", "guideline", "parameter", "template", "platform-research"], "leaves": leaf_refs})

for domain_id, subdomains in domain_specs.items():
    subdomain_items = []
    for subdomain_id, title, description in subdomains:
        leaves = [x for x in leaf_refs if x["domain_id"] == domain_id and x["subdomain_id"] == subdomain_id]
        if subdomain_id in intent_defaults:
            intents = intent_defaults[subdomain_id]
        else:
            derived_intents = sorted({
                intent_id
                for leaf in leaves
                for intent_id in leaf.get("intent_ids", [])
            })
            intents = [(intent_id, "匹配", title) for intent_id in derived_intents] or [("explore", "探索", title)]
        intent_index_path = f"index/intents/{domain_id}/{subdomain_id}.json"
        subdomain_items.append({
            "subdomain_id": subdomain_id, "title": title, "description": description,
            "intent_index": intent_index_path, "leaf_count": len(leaves),
            "status": "published" if leaves else "skeleton"
        })
        dump(intent_index_path, {
            "schema_version": "1.0.0", "subdomain_id": subdomain_id,
            "domain_id": domain_id,
            "intents": [{"id": iid, "action": action, "object": obj, "leaf_refs": [x["leaf_id"] for x in leaf_refs if x["domain_id"] == domain_id and x["subdomain_id"] == subdomain_id and iid in x["intent_ids"]]} for iid, action, obj in intents]
        })
    dump(f"index/domains/{domain_id}.json", {"schema_version": "1.0.0", "domain_id": domain_id, "subdomains": subdomain_items})

# Add subdomain refs and leaf count to legacy package entries.
packages = json.loads((ROOT / "index/packages.json").read_text(encoding="utf-8"))
packages["schema_version"] = "2.0.0"
for package in packages["packages"]:
    domain_id = package["domain_id"]
    package["subdomain_index"] = f"index/domains/{domain_id}.json"
    package["leaf_count"] = sum(1 for x in leaf_refs if x["domain_id"] == domain_id)
    package["loading_policy"] = "progressive"
dump("index/packages.json", packages)

# Runtime index: small routing records only; leaf content stays out of the runtime hot path.
keywords = {
    "undo-window": ["撤销", "undo", "删除后恢复", "可逆操作", "撤销条", "倒计时"],
    "reverse-animation": ["反向动画", "归位", "删除动画", "恢复动画"],
    "flip-reentry": ["FLIP", "列表恢复", "原索引", "共享元素"],
    "motion-accessibility": ["aria", "读屏", "键盘", "减少动态", "prefers-reduced-motion"],
    "follow": ["跟随", "跟手", "连续", "惯性"], "threshold": ["阈值", "触发条件", "断开"], "snap": ["吸附", "锚点", "回弹"],
    "velocity-inheritance": ["速度继承", "释放速度", "摩擦"], "interruption": ["中断", "快速连点", "动画接管"],
    **{k: [v[0], k.replace('-', ' ')] for k, v in interaction_12.items()},
    **{k: [v[0], "dashboard", "后台"] for k, v in dashboard_entries.items()},
    **{k: [v[0], "组件", "AI 生成"] for k, v in components.items()},
    "character-ip": ["角色 IP", "三视图", "周边", "一致性", "毛绒玩偶"],
    "gpui-desktop-web": ["GPUIX", "Metal", "DirectX", "Vulkan", "WebGPU", "WebGL2"],
    "gpui-mobile": ["GPUIX", "iOS", "Android", "移动端", "gpui-mobile"],
    "three-ui-catalog": ["ThreeUI", "Hero", "Backgrounds", "Three.js", "3D 组件"],
}
routes = []
for ref in leaf_refs:
    routes.append({
        "leaf_id": ref["leaf_id"], "keywords": keywords.get(ref["leaf_id"], [ref["title"], ref["leaf_id"], ref["subdomain_id"]]),
        "path": ref["path"], "domain_id": ref["domain_id"], "subdomain_id": ref["subdomain_id"],
        "knowledge_type": ref["knowledge_type"], "entry_count": ref["entry_count"],
        "intent_ids": ref["intent_ids"], "scope": ref["scope"], "do_not_generalize": ref["do_not_generalize"]
    })
dump("index/runtime.json", {
    "schema_version": "1.0.0", "index_type": "runtime-router", "generated_by": "scripts/bootstrap-progressive-content.py",
    "matching": {"normalization": ["lowercase", "unicode_nfkc"], "scoring": "token-overlap", "tie_break": "specificity_then_entry_count"},
    "limits": root["loading_policy"], "routes": routes
})
print(f"generated {len(leaf_refs)} granular leaves")
