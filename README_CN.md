# Image Generator Skill

[English](./README.md) | 简体中文

一个支持多 AI 提供商（Gemini 和 OpenAI GPT Image）的 Claude Code Skill，支持文生图和图生图功能，涵盖多个创意领域。通过环境变量切换提供商。

## 功能特性

### 多提供商支持

- **Gemini 3 Pro Image**：集成 Google Search 实时搜索，超高分辨率最高可达 6336×2688
- **OpenAI GPT Image (gpt-image-2)**：通过 Image API 提供高质量图像生成和编辑
- **灵活配置**：通过 `IMAGE_PROVIDER` 环境变量切换提供商

### 核心能力

**多领域支持**
- **摄影**：人像、风景、场景，支持虚拟相机设置和灯光控制
- **平面设计**：海报、Logo、名片、社交媒体图片、横幅
- **UI 设计**：移动应用界面、仪表板、落地页、设置面板

**生成模式**
- **文生图 (Text-to-Image)**：通过自然语言描述生成高质量图片
- **图生图 (Image-to-Image)**：基于现有图片进行修改、转换或合并
  - 全图转换：人脸身份保持、姿势迁移、风格迁移、服装迁移
  - **精修模式 (partial_edit)**：局部精确修改，多条修改指令
  - **混合模式**：参考图 + 局部修改同时进行

### 独特优势

- **多提供商**：一个环境变量即可在 Gemini 和 GPT 之间切换
- **多领域 Schema**：针对摄影、平面设计、UI 设计定制的结构化 JSON prompt
- **灵活部署**：两个提供商都支持自定义 API 端点，可配合代理使用
- **智能交互**：Claude 自动分析需求，引导用户完善细节

### 使用场景

**摄影创作**
- 专业人像和头像
- 风景和场景摄影
- 带棚拍灯光的产品摄影
- 特定相机设定的艺术场景

**平面设计**
- 网站 LOGO 设计
- 活动海报和传单
- 名片和品牌物料
- 社交媒体图片和横幅
- 信息图表设计

**UI/UX 设计**
- 移动应用界面原型
- 数据可视化仪表板
- 落地页设计
- 设置和配置面板
- 组件库设计

**内容创作**
- 文章配图
- 封面图片
- 头像和个人形象
- 概念艺术图

## 支持的宽高比和分辨率

| 宽高比 | 1K 分辨率 | 2K 分辨率 | 4K 分辨率 |
|--------|-----------|-----------|-----------|
| 1:1    | 1024×1024 | 2048×2048 | 4096×4096 |
| 2:3    | 848×1264  | 1696×2528 | 3392×5056 |
| 3:2    | 1264×848  | 2528×1696 | 5056×3392 |
| 3:4    | 896×1200  | 1792×2400 | 3584×4800 |
| 4:3    | 1200×896  | 2400×1792 | 4800×3584 |
| 4:5    | 928×1152  | 1856×2304 | 3712×4608 |
| 5:4    | 1152×928  | 2304×1856 | 4608×3712 |
| 9:16   | 768×1376  | 1536×2752 | 3072×5504 |
| 16:9   | 1376×768  | 2752×1536 | 5504×3072 |
| 21:9   | 1584×672  | 3168×1344 | 6336×2688 |

## 安装

### 1. 安装依赖

```bash
pip install -q -U google-genai openai Pillow python-dotenv
```

### 2. 配置环境变量

**方式一：使用 .env 文件（推荐）**

复制示例文件并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件填入你的配置：

```bash
# 选择提供商：gemini 或 gpt
IMAGE_PROVIDER=gpt

# Gemini 配置（当 IMAGE_PROVIDER=gemini 时）
GEMINI_API_KEY=your-gemini-api-key-here
# GEMINI_BASE_URL=https://your-proxy-url.com

# OpenAI/GPT 配置（当 IMAGE_PROVIDER=gpt 时）
OPENAI_API_KEY=your-openai-api-key-here
# OPENAI_BASE_URL=https://your-proxy-url.com/v1
# OPENAI_MODEL=gpt-image-2
```

**方式二：使用系统环境变量**

```bash
# 提供商选择
export IMAGE_PROVIDER="gpt"

# Gemini
export GEMINI_API_KEY="your-gemini-api-key-here"
export GEMINI_BASE_URL="https://your-proxy-url.com"

# OpenAI/GPT
export OPENAI_API_KEY="your-openai-api-key-here"
export OPENAI_BASE_URL="https://your-proxy-url.com/v1"
```

> **注意**：配置优先级为 `.env > 系统环境变量 > 默认值`

### 3. 安装 Skill

先将代码 clone 下来，然后将 `image-generator-skill` 目录复制到你的项目的 `.claude/skills/` 目录下：

```
your-project/
├── .claude/
│   └── skills/
│       └── image-generator-skill/
│           ├── SKILL.md
│           ├── .env.example
│           ├── scripts/
│           │   └── generate_image.py
│           └── references/
│               ├── json_schema_t2i_reference.md
│               └── json_schema_i2i_reference.md
```

## 使用方法

### 在 Claude Code 中使用

安装完成后，有两种方式调用此 Skill：

**方式一：显式调用（推荐）**

使用 `/gemini-image-generator` 命令显式调用 Skill：

```
/gemini-image-generator 帮我生成一张猫睡觉的图片
```

```
/gemini-image-generator 把这张照片 ./photo.jpg 转换成动漫风格
```

**方式二：自然语言描述**

直接描述你的图片生成需求，Claude 会自动识别并调用此 Skill：

```
帮我生成一张赛博朋克风格的城市夜景图
```

```
把这张照片 ./photo.jpg 转换成动漫风格
```

Claude 会自动：
1. 分析你的需求并询问必要的细节（宽高比、分辨率等）
2. 将需求转换为结构化 JSON 格式
3. 调用生成脚本生成图片

### 输出位置

生成的图片默认保存在 `./generation-image/` 目录，文件名格式为 `generated_YYYYMMDD_HHMMSS.png`。

## JSON Prompt 结构

完整的 JSON prompt 结构参考 `references/` 目录下的文档：
- `json_schema_t2i_reference.md` - 文生图完整参考
- `json_schema_i2i_reference.md` - 图生图完整参考（含精修模式）

Schema 支持三种创意领域：

### 摄影模式（默认）

```json
{
  "user_intent": "赛博朋克武士站在霓虹灯照亮的巷子里",
  "meta": {
    "domain": "photography",
    "aspect_ratio": "16:9",
    "quality": "ultra_photorealistic"
  },
  "subject": [{
    "type": "cyborg",
    "description": "带有赛博义眼植入物的年轻黑客"
  }],
  "scene": {
    "location": "赛博朋克巷子",
    "lighting": {"type": "neon_lights", "direction": "rim_light"}
  },
  "style_modifiers": {
    "aesthetic": ["cyberpunk", "noir"]
  }
}
```

### 平面设计

```json
{
  "user_intent": "夏日促销海报，50% 折扣优惠",
  "meta": {
    "domain": "graphic_design",
    "aspect_ratio": "3:4",
    "quality": "ultra_photorealistic"
  },
  "graphic_design": {
    "design_type": "poster",
    "layout": {
      "grid_system": "hierarchical",
      "alignment": "center_aligned",
      "spacing": "generous_whitespace"
    },
    "color_scheme": {
      "palette_type": "vibrant",
      "primary_color": "tropical orange",
      "secondary_color": "sky blue"
    },
    "elements": [
      {"type": "headline", "content": "夏日促销", "placement": "top_center"},
      {"type": "headline", "content": "5折优惠", "placement": "center"},
      {"type": "cta_button", "content": "立即购买", "placement": "bottom_center"}
    ],
    "visual_style": {
      "mood": "energetic",
      "texture": "smooth"
    }
  }
}
```

### UI 设计

```json
{
  "user_intent": "现代深色模式数据分析仪表板",
  "meta": {
    "domain": "ui_design",
    "aspect_ratio": "16:9"
  },
  "ui_design": {
    "component_type": "dashboard",
    "layout": {"structure": "grid", "columns": 3, "spacing": "comfortable"},
    "components": [
      {"type": "card", "variant": "primary"},
      {"type": "chart", "variant": "primary"},
      {"type": "sidebar", "variant": "secondary"}
    ],
    "color_system": {
      "mode": "dark_mode",
      "primary": "#6366f1",
      "background": "#0f172a"
    },
    "styling": {
      "border_radius": "medium_rounded",
      "shadow": "subtle_elevation"
    }
  }
}
```

### 精修模式 (Precision Edit)

局部精确修改，多条修改指令同时执行：

```json
{
  "user_intent": "把模特衣服改成红色，表情改成微笑",
  "meta": {"aspect_ratio": "3:4"},
  "input_image": {
    "path": "./portrait.jpg",
    "usage_type": "partial_edit",
    "strength": 0.92
  },
  "edits": {
    "clothing": {
      "edits": [{"target": "color", "action": "change_to", "value": "red"}]
    },
    "face": {
      "edits": [{"target": "expression", "action": "change_to", "value": "smiling"}]
    }
  }
}
```

### 混合模式 (Hybrid Mode)

参考图 + 局部修改同时进行：

```json
{
  "user_intent": "姿势参考图二，手中的包改为皮革材质",
  "meta": {"aspect_ratio": "3:4"},
  "base_image": {"path": "./main.jpg", "strength": 0.92},
  "reference_images": [
    {"path": "./pose.jpg", "usage_type": "pose_copy", "strength": 0.80}
  ],
  "lock": ["face"],
  "edits": {
    "accessories": {
      "edits": [{"target": "material", "action": "change_to", "value": "leather"}]
    }
  }
}
```

## 常见问题

| 问题 | 解决方案 |
|------|----------|
| API Key not found | 确保为所选提供商设置了对应的 API Key 环境变量 |
| 图片生成失败 | 检查 prompt 是否违反内容策略 |
| 图片质量不佳 | 调整 `meta.quality` 和 `meta.image_size` 参数 |
| 宽高比不对 | 检查 `meta.aspect_ratio` 是否为支持的值 |
| 代理连接失败 | 确保 base URL 包含正确路径（如 OpenAI 代理需包含 `/v1`） |

## 目录结构

```
image-generator-skill/
├── SKILL.md                         # Skill 定义文件（Claude 读取）
├── README.md                        # 英文文档
├── README_CN.md                     # 中文文档（本文件）
├── .env.example                     # 环境变量模板
├── scripts/
│   └── generate_image.py            # 图片生成脚本（Gemini + GPT）
└── references/
    ├── json_schema_t2i_reference.md # 文生图 JSON prompt 完整参考
    └── json_schema_i2i_reference.md # 图生图 JSON prompt 完整参考（含精修模式）
```

## License

MIT
