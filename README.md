# Image Generator Skill

English | [简体中文](./README_CN.md)

A Claude Code Skill that supports multiple AI image generation providers (Gemini, OpenAI GPT Image, and Alibaba qwen-image), with text-to-image and image-to-image generation across multiple creative domains. Provider is configured via environment variables.

## Features

### Core Capabilities

**Multi-Provider Support**
- **Gemini 3 Pro Image**: Real-time web search integration, ultra-high resolution up to 6336×2688
- **OpenAI GPT Image (gpt-image-2)**: High-quality image generation and editing via Image API
- **Alibaba qwen-image (qwen-image-3.0, DashScope)**: Text-to-image and image-to-image/editing with 1-3 reference images
- **Configurable**: Switch providers via `IMAGE_PROVIDER` env variable

**Multi-Domain Support**
- **Photography**: Portraits, landscapes, scenes with virtual camera settings and lighting control
- **Graphic Design**: Posters, logos, business cards, social media graphics, banners
- **UI Design**: Mobile app screens, dashboards, landing pages, settings panels

**Generation Modes**
- **Text-to-Image**: Generate high-quality images from natural language descriptions
- **Image-to-Image**: Modify, transform, or combine existing images
  - Full image transform: Face identity, pose transfer, style transfer, clothing transfer
  - **Precision Edit Mode (partial_edit)**: Local precise modifications with multiple edit commands
  - **Hybrid Mode**: Reference images + local edits combined
- **Multi-Image Reference (多图参考)**: Extract elements from reference images and compose into a new text-driven scene
  - Works with 1-N reference images (even a single image can extract an element for a new scene)
  - Extract characters, backgrounds, objects, styles, colors from different sources
  - Text controls overall scene composition and spatial relationships
  - Distinct from I2I: text builds the scene, images provide elements to incorporate

### Unique Advantages

- **Multi-Provider**: Switch between Gemini, GPT, and qwen-image with a single env variable
- **Multi-Domain Schema**: Structured JSON prompts tailored for photography, graphic design, and UI design
- **Flexible Deployment**: Both providers support custom API endpoints for proxy usage
- **Smart Interaction**: Claude automatically analyzes requirements and guides users through details

## Supported Aspect Ratios and Resolutions

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

## Installation

### 1. Install Dependencies

```bash
pip install -q -U google-genai openai Pillow python-dotenv dashscope
```

### 2. Configure Environment Variables

**Method 1: Using .env file (Recommended)**

Copy the example file and configure:

```bash
cp .env.example .env
```

Edit `.env` with your values:

```bash
# Select provider: gemini | gpt | qwen
IMAGE_PROVIDER=gpt

# Gemini configuration (when IMAGE_PROVIDER=gemini)
GEMINI_API_KEY=your-gemini-api-key-here
# GEMINI_BASE_URL=https://your-proxy-url.com

# OpenAI/GPT configuration (when IMAGE_PROVIDER=gpt)
OPENAI_API_KEY=your-openai-api-key-here
# OPENAI_BASE_URL=https://your-proxy-url.com/v1
# OPENAI_MODEL=gpt-image-2

# Qwen/DashScope configuration (when IMAGE_PROVIDER=qwen)
DASHSCOPE_API_KEY=your-dashscope-api-key-here
# QWEN_BASE_URL=https://dashscope.aliyuncs.com/api/v1
# QWEN_MODEL=qwen-image-3.0
```

**Method 2: Using system environment variables**

```bash
# Provider selection
export IMAGE_PROVIDER="gpt"

# Gemini
export GEMINI_API_KEY="your-gemini-api-key-here"
export GEMINI_BASE_URL="https://your-proxy-url.com"

# OpenAI/GPT
export OPENAI_API_KEY="your-openai-api-key-here"
export OPENAI_BASE_URL="https://your-proxy-url.com/v1"
```

> **Note**: Configuration priority is `.env > system environment variables > default values`

### 3. Install the Skill

Clone the repository, then copy the `image-generator-skill` directory to your project's `.claude/skills/` directory:

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
│               ├── json_schema_i2i_reference.md
│               └── json_schema_multi_reference.md
```

## Usage

### Using in Claude Code

After installation, there are two ways to invoke this Skill:

**Method 1: Explicit Invocation (Recommended)**

Use the `/gemini-image-generator` command to explicitly invoke the Skill:

```
/gemini-image-generator Generate an image of a sleeping cat
```

```
/gemini-image-generator Convert this photo ./photo.jpg to anime style
```

**Method 2: Natural Language Description**

Simply describe your image generation needs, and Claude will automatically recognize and invoke this Skill:

```
Generate a cyberpunk style city night scene
```

```
Convert this photo ./photo.jpg to anime style
```

Claude will automatically:
1. Analyze your requirements and ask for necessary details (aspect ratio, resolution, etc.)
2. Convert requirements into structured JSON format
3. Call the generation script to create the image

### Output Location

Generated images are saved by default in the `./generation-image/` directory with filename format `generated_YYYYMMDD_HHMMSS.png`.

## JSON Prompt Structure

For the complete JSON prompt structure, refer to the documents in `references/`:
- `json_schema_t2i_reference.md` - Complete Text-to-Image reference
- `json_schema_i2i_reference.md` - Complete Image-to-Image reference (includes Precision Edit Mode)
- `json_schema_multi_reference.md` - Complete Multi-Image Reference reference (extract elements from images, compose with text)

The schema supports three creative domains:

### Photography (Default)

```json
{
  "user_intent": "A cyberpunk warrior standing in a neon-lit alley",
  "meta": {
    "domain": "photography",
    "aspect_ratio": "16:9",
    "quality": "ultra_photorealistic"
  },
  "subject": [{
    "type": "cyborg",
    "description": "young hacker with cybernetic eye implant"
  }],
  "scene": {
    "location": "cyberpunk alley",
    "lighting": {"type": "neon_lights", "direction": "rim_light"}
  },
  "style_modifiers": {
    "aesthetic": ["cyberpunk", "noir"]
  }
}
```

### Graphic Design

```json
{
  "user_intent": "Summer sale poster with 50% off promotion",
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
      {"type": "headline", "content": "SUMMER SALE", "placement": "top_center"},
      {"type": "headline", "content": "50% OFF", "placement": "center"},
      {"type": "cta_button", "content": "SHOP NOW", "placement": "bottom_center"}
    ],
    "visual_style": {
      "mood": "energetic",
      "texture": "smooth"
    }
  }
}
```

### UI Design

```json
{
  "user_intent": "Modern dark mode analytics dashboard",
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

### Precision Edit Mode

Local precise modifications with multiple edit commands:

```json
{
  "user_intent": "Change model's dress to red, make expression smiling",
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

### Hybrid Mode

Reference images + local edits combined:

```json
{
  "user_intent": "Change pose to reference image, make bag leather material",
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

### Multi-Image Reference

Extract elements from reference images and compose into a text-driven scene:

```json
{
  "user_intent": "Place the person in front of the mountain landscape",
  "meta": {"aspect_ratio": "16:9", "image_size": "2K"},
  "multi_image_reference": {
    "mode": "multi_reference",
    "reference_sources": [
      {
        "id": "person_source",
        "path": "./portrait.jpg",
        "label": "Person",
        "element_to_extract": "the person including facial features and body proportions",
        "extraction_role": "character_source",
        "strength": 0.85
      },
      {
        "id": "bg_source",
        "path": "./landscape.jpg",
        "label": "Background",
        "element_to_extract": "the mountain landscape with a lake",
        "extraction_role": "background_source",
        "strength": 0.80
      }
    ],
    "composition_plan": {
      "description": "Person standing on lakeside, facing mountains, landscape as full background",
      "spatial_layout": "Person left-center foreground, mountain lake full background",
      "blending_notes": "Match daylight direction between person and landscape"
    }
  }
}
```

## FAQ

| Issue | Solution |
|-------|----------|
| API Key not found | Ensure corresponding API key env variable is set for your provider |
| Image generation failed | Check if prompt violates content policy |
| Poor image quality | Adjust `meta.quality` and `meta.image_size` parameters |
| Wrong aspect ratio | Check if `meta.aspect_ratio` is a supported value |
| Proxy connection error | Ensure base URL includes the correct path (e.g., `/v1` for OpenAI proxies) |

## Directory Structure

```
image-generator-skill/
├── SKILL.md                         # Skill definition file (read by Claude)
├── README.md                        # English documentation
├── README_CN.md                     # Chinese documentation
├── .env.example                     # Environment variables template
├── scripts/
│   └── generate_image.py            # Image generation script (Gemini + GPT + Qwen)
└── references/
    ├── json_schema_t2i_reference.md # Complete Text-to-Image JSON reference
    ├── json_schema_i2i_reference.md # Complete Image-to-Image JSON reference
    └── json_schema_multi_reference.md # Complete Multi-Image Reference JSON reference
```

## License

MIT
