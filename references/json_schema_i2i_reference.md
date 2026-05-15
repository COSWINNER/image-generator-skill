# Nano Banana Image-to-Image JSON Prompt Reference

This document provides a comprehensive reference for **Image-to-Image (I2I)** generation using structured JSON prompts with Gemini 3 Pro Image API.

## What is Image-to-Image?

Image-to-Image (I2I) generation transforms, modifies, or re-creates existing images. Unlike Text-to-Image which creates from scratch, I2I requires:

1. **Input image(s)** - The reference image(s) to transform
2. **Transformation intent** - What you want to change or achieve
3. **Usage type** - How the input image should be used

## Core Field: input_image

The `input_image` field is the **heart of I2I generation**. It specifies the reference image and how to use it.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `path` | string | ✅ Yes | Path to the input image file |
| `usage_type` | string | ✅ Yes | How to use the image (6 types available) |
| `strength` | number | ✅ Yes | How much to preserve from original (0.5-0.95) |

## usage_type - 7 Types Explained

| Type | Description | Recommended Strength | Use Cases |
|------|-------------|---------------------|-----------|
| `face_id` | Face identity preservation/swap | 0.85-0.95 | Face swap, keep identity, change appearance |
| `pose_copy` | Copy pose/skeleton structure | 0.75-0.90 | Pose reference, action imitation |
| `clothing_transfer` | Transfer outfit/clothing | 0.70-0.85 | Outfit transfer, fashion reference |
| `depth_map` | Copy 3D shape/composition | 0.65-0.85 | Composition reference, spatial structure |
| `full_character_reference` | Full character as reference | 0.75-0.90 | Character redraw, style conversion |
| `style_transfer` | Transfer artistic style only | 0.50-0.75 | Art style, filter effects, heavy re-stylization |
| **`partial_edit`** | **Partial precision editing** | **0.85-0.98** | **Local edits, multi-step modifications** |

## strength Parameter Guide

The `strength` parameter controls how much of the original image content is preserved:

| Range | Effect | Description |
|-------|--------|-------------|
| **0.95-0.90** | Almost identical | Minor edits only (photo editing level) |
| **0.85-0.75** | Keep main features | Change style/background/clothing, preserve subject |
| **0.70-0.65** | Significant transform | Keep basic structure, major redraw |
| **0.60-0.50** | Heavy redraw | Only preserve composition/mood |

**Quick Rules**:
- Higher strength (0.85+) for face identity preservation
- Medium strength (0.70-0.80) for character redraw with style change
- Lower strength (0.50-0.70) for style transfer only

## JSON Structure for I2I

### Basic Structure

```json
{
  "user_intent": "Natural language description of transformation goal",
  "meta": {
    "aspect_ratio": "16:9",
    "quality": "ultra_photorealistic"
  },
  "subject": [{
    "type": "person",
    "input_image": {
      "path": "./input.jpg",
      "usage_type": "face_id",
      "strength": 0.85
    }
  }]
}
```

### Multiple Input Images

You can use multiple input images for different purposes:

```json
{
  "user_intent": "Create a character with my face and this pose",
  "subject": [
    {
      "id": "face_source",
      "type": "person",
      "input_image": {
        "path": "./my_face.jpg",
        "usage_type": "face_id",
        "strength": 0.90
      }
    },
    {
      "id": "pose_source",
      "input_image": {
        "path": "./pose_reference.jpg",
        "usage_type": "pose_copy",
        "strength": 0.80
      }
    }
  ]
}
```

## 6 I2I Scenario Examples

### 1. Face Identity Preservation (face_id)

**Use when**: You want to keep the person's face/identity but change everything else.

```json
{
  "user_intent": "Keep my face, transform to cyberpunk style",
  "meta": {
    "quality": "ultra_photorealistic"
  },
  "subject": [{
    "type": "person",
    "input_image": {
      "path": "./my_photo.jpg",
      "usage_type": "face_id",
      "strength": 0.90
    }
  }],
  "scene": {
    "location": "cyberpunk street",
    "lighting": {"type": "neon", "direction": "rim_light"}
  },
  "style_modifiers": {
    "aesthetic": ["cyberpunk"]
  }
}
```

**Why high strength (0.90)**: Face identity requires high preservation.

---

### 2. Pose Copy (pose_copy)

**Use when**: You want a new character to match the pose/body position from a reference image.

```json
{
  "user_intent": "Generate a fantasy warrior in this exact pose",
  "meta": {
    "aspect_ratio": "3:4",
    "quality": "ultra_photorealistic"
  },
  "subject": [{
    "type": "person",
    "description": "fantasy warrior wearing shiny armor, holding sword",
    "input_image": {
      "path": "./pose_reference.jpg",
      "usage_type": "pose_copy",
      "strength": 0.80
    }
  }],
  "scene": {
    "location": "battlefield"
  }
}
```

**Why medium-high strength (0.80)**: Need to preserve pose structure but allow character redesign.

---

### 3. Clothing Transfer (clothing_transfer)

**Use when**: You want to transfer the outfit/style from one image to a character.

```json
{
  "user_intent": "Put this outfit on a fashion model",
  "meta": {
    "aspect_ratio": "2:3",
    "quality": "ultra_photorealistic"
  },
  "subject": [{
    "type": "person",
    "description": "professional fashion model",
    "input_image": {
      "path": "./outfit_reference.jpg",
      "usage_type": "clothing_transfer",
      "strength": 0.75
    }
  }],
  "scene": {
    "location": "fashion studio",
    "lighting": {"type": "studio_softbox"}
  }
}
```

**Why medium strength (0.75)**: Preserve clothing details but allow model/scene changes.

---

### 4. Style Transfer (style_transfer)

**Use when**: You only want to transfer the artistic style, not the content.

```json
{
  "user_intent": "Transform my photo into oil painting style",
  "meta": {
    "quality": "oil_painting"
  },
  "subject": [{
    "input_image": {
      "path": "./my_photo.jpg",
      "usage_type": "style_transfer",
      "strength": 0.55
    }
  }],
  "style_modifiers": {
    "medium": "oil_painting",
    "artist_reference": ["Van Gogh style"]
  }
}
```

**Why low strength (0.55)**: We want style transformation, not content preservation.

---

### 5. Character Redraw (full_character_reference)

**Use when**: You want to redraw/restyle a character while keeping them recognizable.

```json
{
  "user_intent": "Transform my photo into anime style",
  "meta": {
    "quality": "anime_v6"
  },
  "subject": [{
    "type": "person",
    "input_image": {
      "path": "./my_photo.jpg",
      "usage_type": "full_character_reference",
      "strength": 0.75
    }
  }],
  "style_modifiers": {
    "medium": "anime",
    "aesthetic": ["clean", "vibrant"]
  }
}
```

**Why medium strength (0.75)**: Keep character recognizable but allow anime transformation.

---

### 6. Composition/Depth Reference (depth_map)

**Use when**: You want to keep the spatial layout/composition but change content entirely.

```json
{
  "user_intent": "Keep this composition, change to sci-fi cityscape",
  "meta": {
    "aspect_ratio": "16:9",
    "quality": "ultra_photorealistic"
  },
  "subject": [{
    "input_image": {
      "path": "./composition_reference.jpg",
      "usage_type": "depth_map",
      "strength": 0.70
    }
  }],
  "scene": {
    "location": "futuristic sci-fi city with flying cars",
    "time": "night",
    "lighting": {"type": "neon_lights"}
  },
  "style_modifiers": {
    "aesthetic": ["cyberpunk", "futuristic"]
  }
}
```

**Why medium-low strength (0.70)**: Preserve spatial structure but allow content transformation.

---

## I2I Best Practices

### 1. Start with Medium Strength
Begin with `strength: 0.75` and adjust based on results:
- Too much original visible? Lower the strength
- Too much changed? Raise the strength

### 2. Choose the Right usage_type

| If you want to... | Use this type |
|-------------------|---------------|
| Keep someone's face | `face_id` |
| Copy a body pose | `pose_copy` |
| Transfer an outfit | `clothing_transfer` |
| Copy the layout/composition | `depth_map` |
| Redraw a character in new style | `full_character_reference` |
| Apply art style only | `style_transfer` |

### 3. strength Quick Reference

| Goal | Recommended strength |
|------|---------------------|
| Face swap/identity | 0.85-0.95 |
| Character redraw | 0.70-0.85 |
| Style transfer | 0.50-0.70 |
| Composition only | 0.60-0.75 |

### 4. Multiple Images Strategy

When using multiple input images:
- Assign different `usage_type` to each image
- Higher `strength` for the primary reference
- Lower `strength` for secondary references

### 5. Aspect Ratio Handling

For I2I, the output aspect ratio:
- **Default**: Matches the input image aspect ratio
- **Custom**: Specify in `meta.aspect_ratio` to override

## Command Usage

### Basic I2I Generation

```bash
python .claude/skills/gemini-image-generator/scripts/generate_image.py \
  --prompt-json '{"user_intent":"...","subject":[{"input_image":{"path":"./input.jpg","usage_type":"face_id","strength":0.85}}]}' \
  --input-images ./input.jpg
```

### Multiple Input Images

```bash
python .claude/skills/gemini-image-generator/scripts/generate_image.py \
  --prompt-json '{"user_intent":"..."}' \
  --input-images ./face.jpg ./pose.jpg
```

## Common I2I Scenarios

| Scenario | usage_type | strength |
|----------|-----------|----------|
| "Make me anime" | `full_character_reference` | 0.75 |
| "Swap face onto X" | `face_id` | 0.90 |
| "Use this pose" | `pose_copy` | 0.80 |
| "Wear this outfit" | `clothing_transfer` | 0.75 |
| "Painting style" | `style_transfer` | 0.55 |
| "Keep composition" | `depth_map` | 0.70 |
| "Change dress color" | `partial_edit` | 0.92 |

---

# Precision Edit Mode (partial_edit)

## What is Precision Edit Mode?

**Precision Edit Mode** (`partial_edit`) is designed for **local modifications** where you want to:
- Change specific parts of an image while keeping everything else intact
- Apply multiple distinct edits in a single generation
- Combine reference images with targeted modifications

**Key Principle**: What you don't specify stays unchanged.

## JSON Structure for Precision Edit

### Basic Precision Edit

```json
{
  "user_intent": "Change model's dress to red, make expression smiling",
  "meta": {
    "aspect_ratio": "3:4",
    "quality": "ultra_photorealistic"
  },
  "input_image": {
    "path": "./portrait.jpg",
    "usage_type": "partial_edit",
    "strength": 0.92
  },
  "edits": {
    "clothing": {
      "edits": [
        {
          "target": "color",
          "action": "change_to",
          "value": "red"
        }
      ]
    },
    "face": {
      "edits": [
        {
          "target": "expression",
          "action": "change_to",
          "value": "smiling"
        }
      ]
    }
  }
}
```

## edits Field Structure

The `edits` field contains **nested edit instructions** grouped by element:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `edits` | array | ✅ Yes | List of edit operations |
| `target` | string | ✅ Yes | What to modify |
| `action` | string | ✅ Yes | How to modify it |
| `value` | any | varies | New value or setting |
| `property` | string | No | Sub-property to target |
| `scope` | string | No | Specific scope (variant, state, position) |
| `intensity` | string | No | `subtle`, `natural`, `strong` |
| `element_id` | string | No | Target element identifier |
| `preserve` | array | No | Properties to preserve during change |

## Supported Actions

| Action | Description | Example value |
|--------|-------------|---------------|
| `change_to` | Change property to new value | `"red"`, `"smiling"`, `"#3B82F6"` |
| `replace_with` | Replace content entirely | `"New Text"`, `"dropdown"` |
| `remove` | Delete element | - |
| `add` | Add new element | `["A", "B", "C"]` |
| `adjust` | Fine-tune numeric value | `+10`, `"larger"` |
| `swap` | Exchange positions/contents | `["element1", "element2"]` |

## element_key Categories

### Photography

| element_key | Supported targets |
|-------------|-------------------|
| `clothing` | color, style, material, pattern |
| `face` | expression, makeup, age |
| `skin` | tone, texture, glow |
| `hair` | color, style, length |
| `body` | pose, posture |
| `background` | blur, color, scene |
| `environment` | add_element, remove_element, change_scene |
| `accessories` | add, remove, change_material |
| `lighting` | type, direction, intensity |

### Graphic Design

| element_key | Supported targets |
|-------------|-------------------|
| `visual_style` | style, texture, effects |
| `text_elements` | text_content, font_style, color |
| `color_scheme` | palette, primary, secondary |
| `images` | replace_with, adjust |
| `layout` | position, alignment, spacing, grid_system, balance |
| `illustration` | style, detail_level, color_palette |

### UI Design

| element_key | Supported targets |
|-------------|-------------------|
| `input_field` | component_type, placeholder, label |
| `button` | color, text, size, state |
| `dropdown` | options, selected_value |
| `card` | content, style, shadow |
| `navigation` | items, active_state |
| `text` | content, font, alignment |

---

# Hybrid Mode: Multiple Reference + Edits

## What is Hybrid Mode?

Hybrid Mode combines multiple reference images with precision edits in a single generation:

**Use when**: You need to simultaneously:
1. Use reference images for pose/style/face
2. Make specific local edits
3. Keep certain parts locked

## Hybrid Mode JSON Structure

```json
{
  "user_intent": "Change pose to reference image, make bag leather material",
  "meta": {"aspect_ratio": "3:4"},
  "base_image": {
    "path": "./main_model.jpg",
    "strength": 0.92
  },
  "reference_images": [
    {
      "path": "./pose_reference.jpg",
      "usage_type": "pose_copy",
      "strength": 0.80
    }
  ],
  "lock": ["face"],
  "edits": {
    "accessories": {
      "edits": [
        {
          "target": "material",
          "action": "change_to",
          "value": "leather",
          "element_id": "handbag"
        }
      ]
    }
  }
}
```

## Hybrid Mode Fields

| Field | Type | Description |
|-------|------|-------------|
| `base_image` | object | Main image to edit (strength: 0.90-0.98) |
| `reference_images` | array | Reference images with their usage_type |
| `lock` | array | Elements to force-keep unchanged |
| `edits` | object | Precision edit instructions |

## Priority Order

1. **`lock`** - Highest priority, these never change
2. **`reference_images`** - Applied in order
3. **`edits`** - Applied last, on top of reference effects

---

# Precision Edit Examples

## Photography: Change Color + Expression

```json
{
  "user_intent": "把模特衣服改成红色，表情改成微笑",
  "meta": {"aspect_ratio": "3:4", "quality": "ultra_photorealistic"},
  "input_image": {
    "path": "./portrait.jpg",
    "usage_type": "partial_edit",
    "strength": 0.92
  },
  "edits": {
    "clothing": {
      "edits": [
        {"target": "color", "action": "change_to", "value": "red", "scope": "all"}
      ]
    },
    "face": {
      "edits": [
        {"target": "expression", "action": "change_to", "value": "smiling", "intensity": "natural"}
      ]
    }
  }
}
```

## Graphic Design: Style + Text Content

```json
{
  "user_intent": "把海报改为手绘风格，修改产品名称",
  "meta": {
    "domain": "graphic_design",
    "aspect_ratio": "3:4",
    "quality": "hand_drawn"
  },
  "input_image": {
    "path": "./poster.png",
    "usage_type": "partial_edit",
    "strength": 0.70
  },
  "edits": {
    "visual_style": {
      "edits": [
        {
          "target": "style",
          "action": "change_to",
          "value": "hand_drawn_sketch",
          "preserve": ["layout", "composition", "text_positions"]
        }
      ]
    },
    "text_elements": {
      "edits": [
        {
          "target": "text_content",
          "action": "change_to",
          "element_id": "product_name",
          "value": "NEW_PRODUCT_NAME"
        }
      ]
    }
  }
}
```

## UI Design: Component Type + Button Color

```json
{
  "user_intent": "把输入框改为下拉框，提交按钮改为蓝色",
  "meta": {
    "domain": "ui_design",
    "aspect_ratio": "16:9"
  },
  "input_image": {
    "path": "./ui_form.png",
    "usage_type": "partial_edit",
    "strength": 0.90
  },
  "edits": {
    "input_field": {
      "edits": [
        {
          "target": "component_type",
          "action": "change_to",
          "value": "dropdown",
          "label": "用户名称"
        }
      ]
    },
    "submit_button": {
      "edits": [
        {
          "target": "color",
          "action": "change_to",
          "value": "#3B82F6",
          "property": "background_color"
        }
      ]
    }
  }
}
```

## Hybrid: Pose Reference + Material Edit

```json
{
  "user_intent": "姿势参考图二，手中的包改为皮革材质",
  "meta": {"aspect_ratio": "3:4"},
  "base_image": {
    "path": "./main_model.jpg",
    "strength": 0.92
  },
  "reference_images": [
    {
      "path": "./pose_reference.jpg",
      "usage_type": "pose_copy",
      "strength": 0.80
    }
  ],
  "edits": {
    "accessories": {
      "edits": [
        {
          "target": "material",
          "action": "change_to",
          "value": "leather",
          "element_id": "handbag"
        }
      ]
    }
  }
}
```

## Hybrid: Face Lock + Pose + Color

```json
{
  "user_intent": "保持我的脸，姿势参考图二，衣服换成红色",
  "meta": {"aspect_ratio": "3:4"},
  "base_image": {
    "path": "./my_photo.jpg",
    "strength": 0.90
  },
  "reference_images": [
    {
      "path": "./pose.jpg",
      "usage_type": "pose_copy",
      "strength": 0.75
    }
  ],
  "lock": ["face"],
  "edits": {
    "clothing": {
      "edits": [
        {
          "target": "color",
          "action": "change_to",
          "value": "red",
          "intensity": "subtle"
        }
      ]
    }
  }
}
```

---

# Advanced Features

## Batch Edit Same Element Type

Edit multiple elements of the same type:

```json
{
  "user_intent": "把所有主要按钮改成蓝色，次要按钮改成灰色",
  "edits": {
    "button": {
      "edits": [
        {"target": "color", "action": "change_to", "value": "#3B82F6", "scope": "variant:primary"},
        {"target": "color", "action": "change_to", "value": "#6B7280", "scope": "variant:secondary"}
      ]
    }
  }
}
```

## Conditional Edit

Edit based on current state:

```json
{
  "user_intent": "把悬停状态的按钮颜色改为深蓝色",
  "edits": {
    "button": {
      "edits": [
        {"target": "color", "action": "change_to", "value": "#1D4ED8", "when_state": "hover"}
      ]
    }
  }
}
```

## Chained Edits

Execute edits sequentially:

```json
{
  "user_intent": "把输入框改成下拉框，并设置默认选项",
  "edits": {
    "input_field": {
      "edits": [
        {
          "target": "component_type",
          "action": "change_to",
          "value": "dropdown",
          "then": {
            "target": "options",
            "action": "add",
            "value": ["选项A", "选项B", "选项C"]
          }
        }
      ]
    }
  }
}
```

---

# Precision Edit Best Practices

### strength for partial_edit

| Edit Type | Recommended strength |
|-----------|---------------------|
| Color/Material change | 0.92-0.98 |
| Expression/Pose change | 0.88-0.95 |
| Text content change | 0.90-0.95 |
| Component type change | 0.85-0.92 |
| Style conversion | 0.70-0.85 |

### Edit Strategy

1. **Be specific** - Use `element_id` when targeting specific elements
2. **Use scope** - Limit edits to specific variants or states
3. **Preserve what matters** - Use `preserve` array for style conversions
4. **Lock critical elements** - Use `lock` for elements that must never change

### Signal Words for Precision Edit

| User says | Mode |
|-----------|------|
| "把X改成Y" | partial_edit |
| "只改..." | partial_edit |
| "保持...不变" | partial_edit + lock |
| "修改这个按钮" | partial_edit |
| "换这个文字" | partial_edit |
