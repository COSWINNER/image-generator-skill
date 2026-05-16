---
name: image-generator
description: "This skill generates images using either Gemini 3 Pro Image API or OpenAI GPT Image API (gpt-image-2), configurable via environment variables. It supports both text-to-image and image-to-image generation including image editing, style transfer, and image merging. The Gemini provider includes real-time web search capabilities via Google Search integration. The provider is selected via the IMAGE_PROVIDER env variable (gemini or gpt). This skill should be used when users want to create, modify, or transform images using AI. The workflow involves three steps: first, Claude analyzes user intent and clarifies unclear requirements through conversation; second, Claude converts intent to structured JSON prompt format; third, Claude calls the generate_image.py script to generate images and save results to the generation-image directory."
---

# Gemini / GPT Image Generator Skill

Generate high-quality images using Gemini 3 Pro Image API or OpenAI GPT Image API with structured JSON prompts. Provider is configured via the `IMAGE_PROVIDER` environment variable.

## Capabilities

- **Text-to-Image**: Generate images from natural language descriptions
  - Photography: Portraits, landscapes, scenes with virtual camera settings
  - Graphic Design: Posters, logos, business cards, social media images, banners
  - UI Design: Mobile app screens, dashboards, landing pages, settings panels
- **Image-to-Image**: Modify, transform, or combine existing images
  - Face identity preservation
  - Pose transfer
  - Style transfer
  - Clothing transfer
  - Image editing and enhancement
- **Multi-Image Reference (多图参考)**: Extract elements from reference images and compose into a new image driven by text
  - Works with 1-N reference images (even 1 image can use this mode)
  - Extract characters, backgrounds, objects, styles from different sources
  - Text controls overall scene composition, spatial layout, and element relationships
  - Key distinction from I2I: I2I transforms an image (A→A'), Multi-Ref builds a new image from text while incorporating elements from reference(s)
- **Real-time Search**: Integrated Google Search for real-time web queries, ensuring generated content is based on up-to-date information and accurate references

## Prerequisites

Ensure the following dependencies are installed:

```bash
pip install -q -U google-genai openai Pillow python-dotenv
```

### Environment Configuration (Priority: `.env` file > system env vars > defaults)

**🚨 CRITICAL**: The script reads configuration from the `.env` file FIRST, which OVERRIDES system environment variables. Always configure via the `.env` file as the primary method.

**`.env` file location**: `./.env` (same directory as this `SKILL.md` file)

```bash
# .env file example (place in the same directory as SKILL.md)
IMAGE_PROVIDER=gpt
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key
OPENAI_BASE_URL=https://your-proxy.example.com/v1
```

Configuration variables:
- `IMAGE_PROVIDER`: Choose provider - `gemini` or `gpt` (default: `gemini`)

**Gemini configuration** (when `IMAGE_PROVIDER=gemini`):
- `GEMINI_API_KEY`: Your Gemini API key (required)
- `GEMINI_BASE_URL`: Custom API endpoint URL (optional, for proxy or alternative endpoints)
- `GEMINI_MODEL`: Model name (optional, default: `gemini-3-pro-image-preview`)

**OpenAI/GPT configuration** (when `IMAGE_PROVIDER=gpt`):
- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `OPENAI_BASE_URL`: Custom API endpoint URL (optional, for proxy or alternative endpoints)
- `OPENAI_MODEL`: Model name (optional, default: `gpt-image-2`)

## Supported Aspect Ratios and Resolutions

Gemini 3 Pro Image supports the following aspect ratios and resolutions:

| Aspect Ratio | 1K Resolution | 2K Resolution | 4K Resolution |
|--------------|---------------|---------------|---------------|
| 1:1          | 1024×1024     | 2048×2048     | 4096×4096     |
| 2:3          | 848×1264      | 1696×2528     | 3392×5056     |
| 3:2          | 1264×848      | 2528×1696     | 5056×3392     |
| 3:4          | 896×1200      | 1792×2400     | 3584×4800     |
| 4:3          | 1200×896      | 2400×1792     | 4800×3584     |
| 4:5          | 928×1152      | 1856×2304     | 3712×4608     |
| 5:4          | 1152×928      | 2304×1856     | 4608×3712     |
| 9:16         | 768×1376      | 1536×2752     | 3072×5504     |
| 16:9         | 1376×768      | 2752×1536     | 5504×3072     |
| 21:9         | 1584×672      | 3168×1344     | 6336×2688     |

**Common Use Cases**:
- `1:1` - Social media posts, profile pictures
- `4:3` / `3:4` - Standard photos
- `16:9` / `9:16` - Desktop wallpapers / Mobile wallpapers
- `4:5` - Instagram portrait
- `21:9` - Ultra-wide cinematic

## Workflow

### Step 1: Analyze User Intent (Claude's Responsibility)

When a user requests image generation, Claude should analyze and clarify their intent:

1. **Identify the generation domain and type**:
   - **Domain** (determines which schema sections to use):
     * `photography` - Portraits, scenes, landscapes with camera settings (default)
     * `graphic_design` - Posters, logos, business cards, social media graphics
     * `ui_design` - App screens, dashboards, web interfaces, UI components
   - **Text-to-image (Pure Creation)**: User describes a new image without any reference images
   - **Image-to-image (Reference-based)**: User provides reference image(s) for ANY of these scenarios:
     * Style transfer (e.g., "make it look like this style")
     * Structure/composition reference (e.g., "similar layout/arrangement")
     * Content reference (e.g., "based on this example")
     * Face/identity preservation
     * Pose copying
     * Object/scene transformation

#### Concept Auto-Expansion Table

When the user's input contains any of the following aesthetic/theme keywords (or their Chinese equivalents / common variants), Claude MUST automatically populate the corresponding JSON fields with the mapped visual details — unless the user explicitly overrides them.

| User Concept | Auto-expanded JSON Fields |
|---|---|
| `cyberpunk` | scene.lighting: neon, rim_light; scene.time: midnight; scene.weather: rainy; scene.atmosphere: neon-lit urban dystopia; scene.background_elements: holographic ads, steam vents, flying drones; color palette: electric blue, magenta, deep shadow; subject accessories: tech implants, chrome, LED accents |
| `noir` | scene.lighting: high contrast single source, harsh shadows; scene.time: midnight; scene.weather: foggy; technical.film_stock: CineStill 800T; technical.color_grade: desaturated high contrast; scene.atmosphere: ominous shadows, moral ambiguity |
| `anime` | meta.quality: anime_v6; style_modifiers.medium: anime; subject skin: smooth flawless, no realistic pores; scene.lighting: bright, clean, even illumination |
| `vaporwave` | color palette: pink, cyan, purple; scene.background_elements: greek statues, grid floor, sunset gradients, palm trees; style_modifiers.aesthetic: retro_80s, synthwave |
| `steampunk` | color palette: brass, copper, brown, sepia; subject accessories: gears, goggles, Victorian-era clothing; scene.background_elements: steam pipes, clockwork mechanisms, brass instruments |
| `minimalist` / `极简` | scene: clean solid or gradient background; composition: centered subject, generous negative space; color palette: monochromatic or limited palette; graphic_design.visual_style.effects: none |
| `ghibli` / `吉卜力` | style_modifiers.medium: anime; color palette: soft watercolor, warm natural tones; scene.atmosphere: dreamy, gentle, nostalgic; scene.lighting: soft diffused natural light |
| `gothic` / `暗黑` | color palette: deep burgundy, black, dark purple; scene: cathedral, graveyard, or dark interior; lighting: candlelight, stained glass; atmosphere: dark, mysterious, brooding |
| `retro_80s` / `复古` | color palette: neon pink, cyan, purple; scene.lighting: neon glow; technical.color_grade: high contrast neon, warm vintage shift; scene.background_elements: synthwave grid, VHS artifacts, CRT scan lines |
| `cinematic` / `电影感` | technical.film_stock: CineStill 800T; technical.camera_model: Arri Alexa or RED; scene.lighting: cinematic three-point or practical lights; composition: wide shot or medium shot; scene.depth_of_field: shallow, cinematic bokeh |
| `editorial` / `时尚` | scene.lighting: studio fashion, dramatic directional; composition: editorial pose; technical.camera_model: Hasselblad medium format; background: clean studio backdrop or architectural |
| `fantasy` / `奇幻` | scene: enchanted forest or castle ruins; lighting: magical volumetric rays; background_elements: floating particles, ethereal glow, ancient runes; atmosphere: dreamlike wonder |
| `sci-fi` / `科幻` | scene: spaceship interior or futuristic city; lighting: cool blue-white; background_elements: holographic displays, sleek technology; color palette: cool metallic, blue accent |
| `watercolor` / `水彩` | style_modifiers.medium: watercolor; scene.atmosphere: soft, flowing; texture: visible paper grain, paint bleeding at edges, translucent washes |
| `oil_painting` / `油画` | style_modifiers.medium: oil_painting; texture: visible brushstrokes, rich impasto; lighting: chiaroscuro if classical, thick pigment texture |
| `pastel` / `马卡龙` | color palette: soft pink, lavender, mint, baby blue; lighting: soft diffused, even; scene.atmosphere: gentle, dreamy, sweet |
| `dark_fantasy` / `暗黑奇幻` | scene: dark forest or ruined castle; lighting: moonlight, volumetric fog; color palette: deep blues, dark gold, crimson; atmosphere: ominous, mysterious, ancient power |

**Expansion Rules**:
- User-specified values **always override** auto-expanded defaults (e.g., "赛博朋克但白天" → keep midnight overridden by user's daytime preference)
- Multiple concepts stack and merge ("dark fantasy" → gothic + fantasy merged)
- If the user's concept is NOT in the table, Claude should use its own knowledge to infer the concept's typical visual elements and apply the same expansion principle
- Expansion applies to **all modes** (T2I, I2I, Multi-Ref) whenever a concept keyword is present

#### Domain-Specific Clarification Dimensions

When analyzing user intent, Claude MUST use the relevant domain checklist below. Do not ask every item mechanically; fill reasonable high-quality defaults for unspecified details when the user's intent is already clear.

**Photography / Portrait — 9 dimensions**:

| # | Dimension | What to clarify or infer | High-value examples |
|---|-----------|--------------------------|---------------------|
| 1 | Camera/Film | Camera body, film stock, capture style | `Sony A7R IV`, `Leica M6`, `35mm film`, `CineStill 800T`, `Fujifilm Pro 400H`, `CCD camera` |
| 2 | Filter/Grade | Filter, color grade, grain | `soft black mist filter`, `pastel low contrast`, `warm vintage grade`, `authentic 35mm grain` |
| 3 | Lighting | Type, direction, temperature, shadows | `diffused window light`, `harsh direct flash`, `golden hour`, `neon rim light`, `soft falloff` |
| 4 | Subject Appearance | Face/body/skin details | `visible skin texture`, `subtle freckles`, `dewy glow`, `almond-shaped eyes`, `slim athletic build` |
| 5 | Clothing Material | Fabric, fit, texture, drape | `oversized white cotton shirt`, `soft wrinkles`, `natural drape`, `ribbed knit texture` |
| 6 | Pose/Action | Body position and dynamics | `leaning against a door frame`, `one leg bent`, `sitting with one leg tucked` |
| 7 | Expression/Gaze | Eye direction, mouth, emotion | `looking directly at viewer`, `soft doe-eyed gaze`, `lips slightly parted`, `subtle smile` |
| 8 | Environment/Background | Foreground, midground, background layers | `blurred drink bottles in foreground`, `convenience store shelves`, `neon refrigerator lights` |
| 9 | Exclusions | Things to avoid | `no plastic skin`, `no airbrushing`, `no watermark`, `no text overlay`, `no bad hands` |

**Graphic Design / Poster — WHAT / FEEL / SHOW / TYPE / TECH**:

| Section | What to clarify or infer |
|---------|--------------------------|
| WHAT | Main subject, product, event, city, abstract concept, or information topic |
| FEEL | Mood and atmosphere: elegant, playful, luxurious, cyberpunk, Chinese aesthetic, editorial |
| SHOW | Composition and layout: grid, freeform, golden ratio, foreground/background, focal hierarchy |
| TYPE | Required text: headline, slogan, brand label, CTA, Chinese/English copy |
| TECH | Rendering style: vector, print poster, hand-drawn illustration, photoreal product render, paper texture |

**UI Design**:

| Dimension | What to clarify or infer |
|-----------|--------------------------|
| Platform | Mobile app, dashboard, landing page, web app, component mockup |
| Theme | Dark mode, light mode, glassmorphism, minimal, enterprise, playful |
| Design system | Apple HIG, Material Design, Tailwind-style, custom brand system |
| Components | Cards, charts, navigation, inputs, buttons, tables, empty states |
| Color accent | Primary brand color and supporting semantic colors |

**E-commerce / Product Advertising**:

| Dimension | What to clarify or infer |
|-----------|--------------------------|
| Product and brand | Product name, brand label, category, packaging |
| Hero shot angle | Studio product shot, lifestyle scene, macro detail, flat lay, tilted hero object |
| Text/labels | Headline, tagline, price, discount badge, feature callouts |
| Color theme | Brand color, accent color, seasonal palette |
| Background | White studio, marble, paper texture, kitchen, bathroom, outdoor lifestyle scene |

#### Infer vs Ask Decision Framework

Core principle: **Infer whenever possible; ask only when inference is ambiguous. Do NOT mechanically ask every dimension.**

| Decision Type | When to Apply | Examples |
|---|---|---|
| **Always auto-infer** | Color palette, lighting direction, time of day, atmosphere, film style — these are direct consequences of the user's high-level concept | User says "赛博朋克" → auto-fill neon lighting, midnight, rainy. No need to ask. |
| **Default infer, allow override** | Scene elements, clothing details, accessories, composition — fill theme-appropriate defaults | User says "赛博朋克女孩" → auto-fill tech accessories, dark clothing. User can override: "不，穿白色连衣裙". |
| **Ask when ambiguous** | Subject identity (age, gender, ethnicity if relevant), specific pose, text content, brand info, named entities | User says "画一个女孩" → ask: age range? style? But if context already implies enough, skip. |
| **Always ask** | aspect_ratio (in T2I mode), image_size, whether precise face identity is needed | Cannot be inferred from context. |

**Asking Strategy**:
- Ask at most **2-3 questions per turn**, never interrogate dimension by dimension
- Prioritize questions that **most impact the final image** (subject appearance, overall style, composition)
- If the user already provides enough context (e.g., a detailed description), **infer everything** and only ask aspect_ratio + image_size
- Use **choice questions** over open-ended ones: "明亮清新还是暗调电影感？" rather than "你想要什么风格？"
- If the user's intent is clear and rich enough, skip asking entirely — just generate the JSON with inferred details and let the user review

2. **🚨 CRITICAL: Mode Detection** (determine generation mode):

   **Mode Decision Table** (by what drives creation):

   | Mode | Driver | Trigger | Key Difference |
   |------|--------|---------|----------------|
   | T2I | Pure text | No images, all from imagination | Create from scratch |
   | I2I | Image as primary | "Transform/modify/change this image" | A → A' |
   | **Multi-Ref** | **Text as primary** | **"Use element from image, create/draw a scene"** | **Text builds scene, images provide elements** |

   **IF user mentions ANY existing image**, determine which mode:

   - **Image-to-Image** — Image is the subject being transformed:
     * "Transform this into anime style" / "把这张图变成动漫"
     * "Swap my face into this photo" / "把脸换成我的"
     * "Change the dress color" / "把衣服改成红色" (partial_edit)
     * "Make it look like this" / "做成这种风格"
     * ✅ Include the reference image in `input_image` field
     * ✅ Pass the image path via `--input-images` parameter
     * ❌ DO NOT just read the image and describe it in text

   - **Multi-Image Reference** — Text drives the scene, images provide elements to incorporate:
     * 1 image: "用图里的猫，画一个赛博朋克街景" / "Use this cat in a cyberpunk city"
     * 1 image: "借鉴这张图的配色，画一个海底世界" / "Borrow the color palette for an underwater scene"
     * 2+ images: "把图A的人放到图B的背景里" / "Put person from A into background B"
     * 2+ images: "人物来自图A，风格来自图B" / "Character from A, style from B"
     * ✅ Use `multi_image_reference` section in JSON
     * ✅ Specify `element_to_extract` and `extraction_role` for each source
     * ✅ Use `composition_plan` to describe spatial arrangement
     * ✅ Pass image paths via `--input-images` parameter
     * ❌ DO NOT just read images and describe them in text

   - **Only if user describes a brand new image from imagination**: Use text-to-image

3. **Determine aspect ratio and resolution**:
   - **For text-to-image**: If user does NOT explicitly specify aspect ratio or resolution, Claude MUST ask the user which aspect ratio and resolution they prefer (refer to the supported options table above)
   - **For image-to-image**: Automatically select the closest matching aspect ratio based on the source image dimensions. For multiple input images, use the primary/main image as reference. If user explicitly specifies a different aspect ratio, use the user's preference instead.
   - **🚨 CRITICAL: image_size selection**: If user does NOT explicitly specify `image_size`, Claude MUST ask the user to choose between `1K`, `2K`, or `4K` ONLY. No other options are allowed. DO NOT suggest or accept any other values.

4. **Clarify unclear aspects** using the domain-specific dimensions above:
   - **Photography/portrait**: Cover the 9-dimension checklist, especially camera/film, lighting, pose, gaze, skin/material texture, and exclusions
   - **Graphic design/poster**: Use the WHAT / FEEL / SHOW / TYPE / TECH framework
   - **UI design**: Cover platform, theme, design system, key components, and color accent
   - **E-commerce/product advertising**: Cover product/brand, hero shot angle, text labels, color theme, and background
   - Do not ask about every dimension if the intent is clear; infer tasteful defaults and encode them in JSON

5. **For image-to-image**, additionally clarify:
   - Which input images to use?
   - What kind of transformation? (face swap, style transfer, pose copy, etc.)
   - How much to preserve from the original? (strength parameter: 0.5-0.95, higher = more similar)

6. **🚨 CRITICAL: Precision Edit Mode Detection**:
   - **IF user requests LOCAL/MULTIPLE modifications** (e.g., "把衣服改成红色", "修改这个按钮", "换这个文字"):
     * ✅ This is **Partial Edit Mode** (`usage_type: "partial_edit"`)
     * ✅ Use `edits` field to list ALL modifications
     * ✅ strength should be **0.85-0.98** (higher than normal I2I)
     * ✅ What user doesn't mention stays unchanged (reverse thinking)
   - **IF user combines reference images + local edits** (e.g., "姿势参考图二，衣服改成红色"):
     * ✅ This is **Hybrid Mode** (use `base_image` + `reference_images` + `edits`)
     * ✅ Use `lock` array for elements that must never change
   - **Signal words for Precision Edit**: "把X改成Y", "只改...", "保持...不变", "修改这个..."

### Precision Edit: Listing Modifications

When in Precision Edit Mode, list ALL modifications explicitly:

```
修改项：
1. 衣服颜色 → 红色
2. 表情 → 微笑
3. 背景 → 模糊
```

Each modification becomes an entry in the `edits` object.

### Step 2: Convert Intent to JSON Format (Claude's Responsibility)

Claude converts the clarified user intent to a structured JSON prompt.

**🚨 IMPORTANT: Use the correct reference document**
- **For Text-to-Image (文生图)**: Reference `references/json_schema_t2i_reference.md`
- **For Image-to-Image (图生图)**: Reference `references/json_schema_i2i_reference.md`
- **For Multi-Image Reference (多图参考)**: Reference `references/json_schema_multi_reference.md`

**Key sections to include** (only include relevant fields):

```json
{
  "user_intent": "Natural language summary of the goal",
  "meta": {
    "domain": "photography",
    "aspect_ratio": "16:9",
    "image_size": "2K",
    "quality": "ultra_photorealistic"
  },
  "subject": [{
    "type": "person",
    "description": "Visual traits",
    "pose": "Action description",
    "expression": "neutral",
    "clothing": [{"item": "...", "color": "..."}],
    "input_image": {
      "path": "./input.jpg",
      "usage_type": "face_id",
      "strength": 0.85
    }
  }],
  "scene": {
    "location": "Setting description",
    "time": "golden_hour",
    "lighting": {"type": "cinematic", "direction": "rim_light"}
  },
  "composition": {
    "framing": "medium_shot",
    "angle": "eye_level"
  },
  "style_modifiers": {
    "medium": "photography",
    "aesthetic": ["cyberpunk"]
  }
}
```

**For graphic design**, use `domain: "graphic_design"` and include `graphic_design` section:

```json
{
  "meta": {"domain": "graphic_design", "aspect_ratio": "3:4"},
  "graphic_design": {
    "design_type": "poster",
    "layout": {"grid_system": "hierarchical", "alignment": "center_aligned"},
    "color_scheme": {"palette_type": "vibrant", "primary_color": "tropical orange"},
    "elements": [...]
  }
}
```

**For UI design**, use `domain: "ui_design"` and include `ui_design` section:

```json
{
  "meta": {"domain": "ui_design", "aspect_ratio": "16:9"},
  "ui_design": {
    "component_type": "dashboard",
    "layout": {"structure": "grid", "columns": 3},
    "color_system": {"mode": "dark_mode", "primary": "#6366f1"},
    "components": [...]
  }
}
```

**For Precision Edit Mode (partial_edit)**, use `edits` field to list modifications:

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

**For Hybrid Mode (reference + edits)**, use `base_image` + `reference_images`:

```json
{
  "user_intent": "姿势参考图二，手中的包改为皮革材质",
  "meta": {"aspect_ratio": "3:4"},
  "base_image": {"path": "./main.jpg", "strength": 0.92},
  "reference_images": [
    {"path": "./pose.jpg", "usage_type": "pose_copy", "strength": 0.80}
  ],
  "edits": {
    "accessories": {
      "edits": [{"target": "material", "action": "change_to", "value": "leather"}]
    }
  }
}
```

**For Multi-Image Reference (多图参考)**, use `multi_image_reference` section:

```json
{
  "user_intent": "把图A的人放到图B的山景背景中",
  "meta": {"aspect_ratio": "16:9", "image_size": "2K"},
  "multi_image_reference": {
    "mode": "multi_reference",
    "reference_sources": [
      {
        "id": "source_A",
        "path": "./person.jpg",
        "label": "人物来源",
        "element_to_extract": "站立的女性，包括面部特征和整体外观",
        "extraction_role": "character_source",
        "strength": 0.85
      },
      {
        "id": "source_B",
        "path": "./landscape.jpg",
        "label": "背景来源",
        "element_to_extract": "山脉湖泊的日落景观",
        "extraction_role": "background_source",
        "strength": 0.75
      }
    ],
    "composition_plan": {
      "description": "将女性放在画面中心前景，山脉湖泊作为全宽背景",
      "spatial_layout": "前景：人物居中；背景：山湖全景",
      "blending_notes": "匹配人物与背景的光照方向"
    }
  },
  "scene": {
    "lighting": {"type": "natural", "direction": "backlight"}
  }
}
```

**Multi-Ref key points**:
- `reference_sources`: 1-5 images, each with `extraction_role` (character_source, background_source, style_source, object_source, color_source, pose_source, architecture_source, clothing_source)
- `element_to_extract`: Be specific about what to extract from each image
- `composition_plan`: Describe how elements combine spatially — this is the most important part
- `strength`: 0.5-0.95, higher = more faithful reproduction of the extracted element
- Other fields (scene, style_modifiers, etc.) still apply as normal

**Important guidelines**:
- Only include fields relevant to the user's request
- Do not add unnecessary optional fields
- For image-to-image, include `input_image` in the subject
- `aspect_ratio`: One of `1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9`
- `image_size`: One of `1K`, `2K`, `4K` (default: `1K`)

### Prompt Enhancement Rules (CRITICAL)

When converting user intent to JSON, Claude MUST apply these rules to improve image quality and preserve useful structure:

1. **Specificity over abstraction**
   - Bad: `"expression": "happy"`
   - Good: `"expression": "soft smile, lips slightly parted, gentle warmth in eyes"`
   - Bad: `"lighting": {"type": "natural"}`
   - Good: `"lighting": {"type": "diffused natural window light", "direction": "from left side", "color_temperature": "warm golden", "shadow_style": "soft falloff"}`
   - Bad: `"clothing": [{"item": "shirt"}]`
   - Good: `"clothing": [{"item": "oversized button-up shirt", "color": "white", "fabric": "cotton", "fit": "loosely tied at waist", "texture": "soft wrinkles", "drape": "natural relaxed drape"}]`

2. **Lighting is the first quality lever**
   - Prefer lighting objects that include `type`, `direction`, `color_temperature`, `mood`, `specular_highlights`, and `shadow_style` when relevant.
   - For portraits, describe how light touches skin, eyes, hair, and background separation.

3. **Layer the environment**
   - Prefer `foreground_elements`, `midground`, and `background_elements` over a single flat location when the scene matters.
   - Mention blur/depth with `depth_of_field` if the image should feel photographic.

4. **Add realistic texture**
   - For people, include `skin_texture` such as `visible pores, natural micro-details, subtle imperfections, no airbrushing` unless the user requests stylized/anime output.
   - For clothing and products, include material, fit, texture, drape, reflections, grain, or surface finish.

5. **Always include useful exclusions**
   - Photography default: `blur`, `low quality`, `bad hands`, `deformed fingers`, `watermark`, `text overlay`, `plastic skin`, `airbrushing`.
   - Graphic design default: `blurry`, `low resolution`, `watermark`, `cluttered layout`.
   - UI default: `device frame`, `monitor`, `physical device`, `screen reflection`.

6. **Preserve Chinese descriptions**
   - If the user's intent is in Chinese, keep Chinese details in `user_intent`, `description`, text content, cultural aesthetics, food/city names, and layout requirements.
   - Do not translate culturally specific Chinese concepts unless the user asks.

7. **Use camera/film aesthetics for photography**
   - For photographic output, include a `technical` section with `camera_model`, `lens`, `film_stock`, `filter_effect`, or `color_grade` when the user did not provide a conflicting style.
   - Good defaults include `35mm lens`, `Sony A7R IV`, `Leica M6`, `Kodak Portra 400`, `CineStill 800T`, `Fujifilm Pro 400H`, and `soft black mist filter`.

8. **Aesthetic concept auto-expansion**
   - When the user's input contains aesthetic concept keywords (cyberpunk, noir, anime, etc.), Claude MUST:
     1. Map the concept to concrete visual elements (see Concept Auto-Expansion Table above)
     2. Write the mapped details into the corresponding JSON fields (scene, lighting, color, accessories, etc.)
     3. Reflect the expanded details in `user_intent` as a rich, vivid sentence
   - Example: User says "一个赛博朋克女孩" → Expanded user_intent: "一个年轻女性站在午夜时分的霓虹灯街道，雨水打湿的地面反射着电蓝色和品红色的霓虹灯光，她有着发光的赛博手臂植入物和电蓝色短发，穿着哑光黑色战术夹克"

9. **Description richness**
   - Every `description` field in the JSON must be specific enough to evoke a mental image on its own.
   - Bad: `"description": "confident business executive"`
   - Good: `"description": "confident business executive in her early 40s, sharp features, warm olive skin with natural undertones, subtle freckles across the nose, wearing minimal professional makeup"`
   - Bad: `"description": "cyberpunk street"`
   - Good: `"description": "rain-soaked cyberpunk alley at midnight, neon signs reflecting off wet asphalt, steam rising from metal grates, holographic advertisements flickering on building facades"`
   - Principle: **Each description should let the reader "see" the image in their mind**, not just know the concept label.

10. **user_intent as the primary prompt**
    - The `user_intent` field is the **most important prompt field** in the entire JSON — it gets passed directly to the generation model.
    - It should NOT be a mere restatement of the user's raw input. It must be Claude's analyzed and expanded **complete, vivid, visually rich sentence**.
    - Must include: subject appearance + scene environment + lighting atmosphere + composition hint.
    - Recommended length: 30-80 English words (or equivalent Chinese), detailed enough but not excessive.

### Step 3: Generate Image

Execute the image generation script with the JSON prompt.

**IMPORTANT**: Use the skill's path relative to project root: `.claude/skills/gemini-image-generator-skill/scripts/generate_image.py`

**🚨 CRITICAL - After Image Generation**:
- ✅ Report the output file path to the user
- ✅ Inform the user that image generation is complete
- ❌ DO NOT automatically read or display the generated image
- ❌ DO NOT use the Read tool on the generated image file
- ⚠️ Let the user decide if they want to view the generated image

#### For Text-to-Image

```bash
python .claude/skills/gemini-image-generator-skill/scripts/generate_image.py --prompt-json '{"user_intent":"..."}'
```

#### For Image-to-Image

```bash
python .claude/skills/gemini-image-generator-skill/scripts/generate_image.py --prompt-json '{"user_intent":"..."}' --input-images ./input1.jpg ./input2.jpg
```

#### For Multi-Image Reference

```bash
python .claude/skills/gemini-image-generator-skill/scripts/generate_image.py --prompt-json '{"user_intent":"...","multi_image_reference":{"mode":"multi_reference","reference_sources":[...],"composition_plan":{...}}}' --input-images ./person.jpg ./landscape.jpg
```

#### Custom Output Directory

```bash
python .claude/skills/gemini-image-generator-skill/scripts/generate_image.py --prompt-json '{"user_intent":"..."}' --output-dir ./my-images
```

#### Output Location

Generated images are saved to `./generation-image/` directory (or custom directory) with timestamp-based filenames:
- Format: `generated_YYYYMMDD_HHMMSS.png`

## Usage Examples

### Example 1: Simple Portrait

**User**: "Generate a professional headshot of a business woman"

**Claude's Analysis**:
1. Ask: "What style do you prefer - formal corporate or more casual professional? Any specific background preference? And what expression - friendly smile or serious/confident?"

**After Clarification**, Claude generates JSON:

```json
{
  "user_intent": "Professional headshot of a business woman",
  "meta": {"aspect_ratio": "4:5", "quality": "ultra_photorealistic"},
  "subject": [{
    "type": "person",
    "gender": "female",
    "description": "confident business executive",
    "expression": "smiling",
    "clothing": [{"item": "blazer", "color": "navy blue"}]
  }],
  "scene": {
    "location": "modern office",
    "lighting": {"type": "studio_softbox"}
  },
  "composition": {"framing": "close_up", "focus_point": "eyes"}
}
```

**Execute**:
```bash
python .claude/skills/gemini-image-generator-skill/scripts/generate_image.py --prompt-json '{"user_intent":"Professional headshot..."}'
```

### Example 2: Image Style Transfer

**User**: "Transform this photo into anime style" (provides input image path)

**Claude's Analysis**:
1. Confirm the input image path
2. Ask: "Which anime style do you prefer? Studio Ghibli soft style, or modern sharp anime? How much stylization - keep recognizable or fully transform?"

**After Clarification**, Claude generates JSON:

```json
{
  "user_intent": "Transform photo into anime style",
  "meta": {"quality": "anime_v6"},
  "subject": [{
    "type": "person",
    "input_image": {
      "path": "./user_photo.jpg",
      "usage_type": "full_character_reference",
      "strength": 0.8
    }
  }],
  "style_modifiers": {"medium": "anime"}
}
```

**Execute**:
```bash
python .claude/skills/gemini-image-generator-skill/scripts/generate_image.py --prompt-json '...' --input-images ./user_photo.jpg
```

### Example 3: Complex Scene with Multiple Elements

**User**: "Create a cyberpunk street scene with a hacker character"

**Claude's Analysis**:
1. Ask about character: "What does the hacker look like? Male/female? Cybernetic enhancements? Clothing style?"
2. Ask about scene: "Time of day? Rainy? What elements in the background - neon signs, flying cars, crowds?"
3. Ask about style: "Ultra-realistic or more stylized/artistic?"

**After Clarification**, Claude generates comprehensive JSON with all scene details.

### Example 4: Image Editing

**User**: "Add a wizard hat to my cat in this photo"

**Claude's Analysis**:
1. Confirm the input image path
2. Ask: "What style of wizard hat - classic pointy purple, colorful magical, or something else?"

**JSON**:
```json
{
  "user_intent": "Add wizard hat to cat photo",
  "subject": [{
    "type": "animal",
    "description": "cat with wizard hat",
    "input_image": {
      "path": "./cat.jpg",
      "usage_type": "full_character_reference",
      "strength": 0.9
    },
    "accessories": [{"item": "wizard hat", "color": "purple", "material": "fabric"}]
  }]
}
```

### Example 5: Multi-Image Reference — Single Image Element Extraction

**User**: "用这张图里的猫，画一个赛博朋克风格的街景"

**Claude's Analysis**:
1. This is Multi-Ref mode: text builds the cyberpunk scene, image provides the cat element
2. Ask: "What aspect ratio? How realistic? Should the cat be walking, sitting, or doing something specific?"

**JSON**:
```json
{
  "user_intent": "A cat walking through a neon-lit cyberpunk street at night",
  "meta": {"aspect_ratio": "16:9", "image_size": "2K", "quality": "ultra_photorealistic"},
  "multi_image_reference": {
    "mode": "multi_reference",
    "reference_sources": [
      {
        "id": "cat_source",
        "path": "./my_cat.jpg",
        "label": "猫咪来源",
        "element_to_extract": "the cat including fur pattern, body shape, and facial features",
        "extraction_role": "character_source",
        "strength": 0.85
      }
    ],
    "composition_plan": {
      "description": "The cat walking down the middle of a wet cyberpunk street, neon signs and holographic advertisements, rain reflecting neon on wet pavement",
      "spatial_layout": "Cat in center foreground, cyberpunk street stretching into background"
    }
  },
  "style_modifiers": {"aesthetic": ["cyberpunk", "neon_noir"]}
}
```

**Execute**:
```bash
python .claude/skills/gemini-image-generator-skill/scripts/generate_image.py --prompt-json '...' --input-images ./my_cat.jpg
```

### Example 6: Multi-Image Reference — Character + Background

**User**: "把这张人物照片放到那个风景背景里"

**Claude's Analysis**:
1. Multi-Ref mode: extract person from image A, extract background from image B
2. Auto-detect aspect ratio from images, ask user for resolution preference

**JSON**:
```json
{
  "user_intent": "Place the person in front of the mountain landscape",
  "meta": {"aspect_ratio": "16:9", "image_size": "2K", "quality": "ultra_photorealistic"},
  "multi_image_reference": {
    "mode": "multi_reference",
    "reference_sources": [
      {
        "id": "person_source",
        "path": "./portrait.jpg",
        "label": "人物来源",
        "element_to_extract": "the standing person including facial features, hairstyle, body proportions",
        "extraction_role": "character_source",
        "strength": 0.85
      },
      {
        "id": "bg_source",
        "path": "./landscape.jpg",
        "label": "背景来源",
        "element_to_extract": "the mountain landscape with a lake",
        "extraction_role": "background_source",
        "strength": 0.80
      }
    ],
    "composition_plan": {
      "description": "Person standing on the lakeside, facing mountains, landscape filling the background",
      "spatial_layout": "Person left-center foreground, mountain lake full background",
      "blending_notes": "Match natural daylight direction on person to landscape lighting"
    }
  }
}
```

**Execute**:
```bash
python .claude/skills/gemini-image-generator-skill/scripts/generate_image.py --prompt-json '...' --input-images ./portrait.jpg ./landscape.jpg
```

## Resources

### scripts/

- `generate_image.py`: Main image generation script using Gemini API
  - Accepts JSON prompt via `--prompt-json`
  - Supports input images via `--input-images`
  - Saves output to `--output-dir` (default: `./generation-image/`)

### references/

- `json_schema_t2i_reference.md`: Text-to-Image (T2I) complete reference - for generating images from scratch
- `json_schema_i2i_reference.md`: Image-to-Image (I2I) complete reference - for transforming existing images
- `json_schema_multi_reference.md`: Multi-Image Reference (多图参考) complete reference - for extracting elements from reference images and composing into text-driven scenes

## Troubleshooting

### Common Issues

1. **API Key not found**: Ensure the corresponding API key is set in the `.env` file (same directory as `SKILL.md`), e.g. `GEMINI_API_KEY=...` or `OPENAI_API_KEY=...`
2. **Image not generated**: Check if the prompt violates content policies
3. **Low quality output**: Adjust quality settings in meta section
4. **Wrong aspect ratio**: Verify `aspect_ratio` in meta section matches your needs

### Tips for Better Results

- Be specific about subject details (age, clothing, pose)
- Include lighting and atmosphere descriptions
- Use technical photography terms for realistic images
- Reference specific art styles for artistic images
- Use negative prompts in advanced section to avoid common issues (blur, bad hands, etc.)
