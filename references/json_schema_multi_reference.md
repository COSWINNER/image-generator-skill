# Multi-Image Reference (多图参考) JSON Prompt Reference

This document provides a comprehensive reference for **Multi-Image Reference** generation using structured JSON prompts.

## What is Multi-Image Reference?

Multi-Image Reference mode extracts specific elements from one or more reference images and composites them into a **brand new image** driven primarily by **text description**.

The core distinction is **what drives the creation**:

| Mode | Driver | Description |
|------|--------|-------------|
| Text-to-Image (T2I) | Pure text | Create from scratch, no reference images |
| Image-to-Image (I2I) | Image as primary subject | Transform image A → A' (style transfer, face swap, etc.) |
| **Multi-Image Reference** | **Text as primary driver** | **Text builds the overall scene, images provide specific elements to incorporate** |

### Key Insight

Multi-Image Reference is NOT defined by the number of images. Even **1 image** can use this mode when the user wants to **extract an element** from it but construct the overall image from text.

**Examples**:
- 1 image: "Use the cat from this image, draw a cyberpunk street scene" → Extract cat element, text builds the scene
- 1 image: "Borrow the color palette from this photo, create an underwater world" → Extract colors, text builds the scene
- 2 images: "Put the person from image A into the background of image B" → Extract elements, text determines composition
- 3 images: "Character from A, clothing style from B, background from C" → Multi-element fusion

### When to Use Multi-Image Reference vs I2I

| User Intent | Mode | Why |
|-------------|------|-----|
| "Transform this photo into anime style" | I2I | Image is the subject being transformed |
| "Swap my face into this photo" | I2I | Image is the base being modified |
| "Change the dress color to red" | I2I (partial_edit) | Local edit on existing image |
| "Use this cat in a cyberpunk city" | **Multi-Ref** | Cat is an element, text builds the scene |
| "Put person A into background B" | **Multi-Ref** | Text-driven composition from multiple sources |
| "Combine the style of A with scene B, add character C" | **Multi-Ref** | Multi-source element fusion |

---

## JSON Structure

### Core Structure

```json
{
  "user_intent": "Natural language description of the desired image",
  "meta": {
    "aspect_ratio": "16:9",
    "image_size": "2K",
    "quality": "ultra_photorealistic"
  },
  "multi_image_reference": {
    "mode": "multi_reference",
    "reference_sources": [
      {
        "id": "source_A",
        "path": "./person.jpg",
        "label": "人物来源",
        "element_to_extract": "the standing female person including facial features, hairstyle, and overall appearance",
        "extraction_role": "character_source",
        "strength": 0.85
      },
      {
        "id": "source_B",
        "path": "./landscape.jpg",
        "label": "背景来源",
        "element_to_extract": "the sunset landscape with mountains and a lake",
        "extraction_role": "background_source",
        "strength": 0.75
      }
    ],
    "composition_plan": {
      "description": "Place the female person from source A in the center foreground, with the mountain lake landscape from source B as the full-width background. The person should be standing by the lakeside, facing the mountains.",
      "spatial_layout": "Foreground: person from source A (center). Background: landscape from source B (full width).",
      "interactions": [],
      "blending_notes": "Match the lighting direction between the person and the landscape for seamless integration"
    }
  },
  "scene": {},
  "style_modifiers": {}
}
```

---

## Field Reference

### `multi_image_reference` Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mode` | string | ✅ Yes | Must be `"multi_reference"` |
| `reference_sources` | array | ✅ Yes | 1-5 source image specifications |
| `composition_plan` | object | ✅ Yes | How to combine extracted elements |

### `reference_sources[]` Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✅ Yes | Unique identifier, e.g., `"source_A"`, `"cat_ref"` |
| `path` | string | ✅ Yes | File path to the reference image |
| `label` | string | ✅ Yes | Human-readable label describing the source role |
| `element_to_extract` | string | ✅ Yes | Precise description of what visual elements to extract from this image |
| `extraction_role` | string | ✅ Yes | Category role (see extraction_role table below) |
| `strength` | number | ✅ Yes | Extraction fidelity, 0.5-0.95 |

### `composition_plan` Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | ✅ Yes | Complete description of how elements should be combined in the final image |
| `spatial_layout` | string | No | Explicit spatial arrangement (foreground/background/left/right positions) |
| `interactions` | array | No | Descriptions of how elements from different sources interact with each other |
| `blending_notes` | string | No | Guidance for lighting/style consistency between elements |

---

## `extraction_role` Reference

| Role | Description | Recommended Strength | Example Use Cases |
|------|-------------|---------------------|-------------------|
| `character_source` | Person, animal, or character | 0.75-0.90 | "Use this person in a new scene", "Take the cat from this image" |
| `background_source` | Background, environment, or setting | 0.70-0.85 | "Use this landscape as background", "Take the cityscape from this photo" |
| `style_source` | Artistic style, visual treatment, or aesthetic | 0.50-0.75 | "Apply this art style", "Use this color grading" |
| `object_source` | Specific object, prop, or item | 0.75-0.90 | "Use this car in the scene", "Include this piece of furniture" |
| `color_source` | Color palette or color scheme | 0.50-0.70 | "Borrow the color palette", "Use these tones" |
| `pose_source` | Pose, gesture, or spatial arrangement | 0.70-0.85 | "Use this pose for the character", "Copy this body position" |
| `architecture_source` | Architecture, structure, or geometric elements | 0.65-0.80 | "Use this building style", "Borrow the architectural elements" |
| `clothing_source` | Clothing, fashion, or material texture | 0.70-0.85 | "Dress the character in this style", "Use this fabric texture" |

---

## `strength` Guide for Multi-Image Reference

In Multi-Image Reference mode, `strength` controls **how faithfully** the extracted element should be reproduced in the new image:

| Range | Effect | When to Use |
|-------|--------|-------------|
| **0.90-0.95** | Exact reproduction | Face identity, precise object replication |
| **0.80-0.89** | High fidelity with adaptation | Character in new environment, preserving key features |
| **0.70-0.79** | Moderate fidelity | General style/color borrowing, allowing scene adaptation |
| **0.50-0.69** | Loose reference | Artistic style, mood/atmosphere, color palette only |

**Quick Rules**:
- For face/identity: 0.85-0.95 (must be recognizable)
- For characters/objects: 0.75-0.90 (keep key features, allow adaptation)
- For backgrounds: 0.70-0.85 (recognizable but flexible)
- For style/color: 0.50-0.75 (essence, not exact copy)

---

## Complete Examples

### 1. Single Image: Extract Character into New Scene

**Scenario**: Use a cat from a photo to create a cyberpunk street scene.

```json
{
  "user_intent": "A cat walking through a neon-lit cyberpunk street at night",
  "meta": {
    "aspect_ratio": "16:9",
    "image_size": "2K",
    "quality": "ultra_photorealistic"
  },
  "multi_image_reference": {
    "mode": "multi_reference",
    "reference_sources": [
      {
        "id": "cat_source",
        "path": "./my_cat.jpg",
        "label": "猫咪来源",
        "element_to_extract": "the orange tabby cat including its fur pattern, body shape, and facial features",
        "extraction_role": "character_source",
        "strength": 0.85
      }
    ],
    "composition_plan": {
      "description": "The cat from the reference image is walking down the middle of a wet cyberpunk street, surrounded by neon signs and holographic advertisements. Rain is falling, reflecting the neon lights on the wet pavement.",
      "spatial_layout": "Cat in the center foreground, cyberpunk street stretching into the background with neon signs on both sides"
    }
  },
  "scene": {
    "location": "cyberpunk street with neon signs and holograms",
    "time": "night",
    "weather": "rain",
    "lighting": {"type": "neon", "direction": "multi_directional"}
  },
  "style_modifiers": {
    "aesthetic": ["cyberpunk", "neon_noir"]
  }
}
```

### 2. Single Image: Extract Style into New Scene

**Scenario**: Borrow the color palette from a photo to create an underwater world.

```json
{
  "user_intent": "An underwater coral reef scene using the color palette from the reference image",
  "meta": {
    "aspect_ratio": "3:2",
    "image_size": "2K",
    "quality": "ultra_photorealistic"
  },
  "multi_image_reference": {
    "mode": "multi_reference",
    "reference_sources": [
      {
        "id": "color_ref",
        "path": "./sunset_photo.jpg",
        "label": "配色参考",
        "element_to_extract": "the warm orange-gold-purple color palette and tonal gradations",
        "extraction_role": "color_source",
        "strength": 0.65
      }
    ],
    "composition_plan": {
      "description": "A vibrant underwater coral reef scene using the warm orange-gold-purple tones from the reference image. Tropical fish swim among the corals, with light rays filtering down from the surface.",
      "blending_notes": "Apply the warm sunset tones to the underwater lighting, creating golden-hour-like underwater illumination"
    }
  },
  "scene": {
    "location": "underwater coral reef",
    "lighting": {"type": "volumetric_light_rays", "direction": "from_above"}
  },
  "style_modifiers": {
    "aesthetic": ["vibrant", "dreamy"]
  }
}
```

### 3. Two Images: Character + Background Composition

**Scenario**: Place a person from one photo into the background of another.

```json
{
  "user_intent": "Place the person from the portrait photo in front of the mountain landscape",
  "meta": {
    "aspect_ratio": "16:9",
    "image_size": "2K",
    "quality": "ultra_photorealistic"
  },
  "multi_image_reference": {
    "mode": "multi_reference",
    "reference_sources": [
      {
        "id": "person_source",
        "path": "./portrait.jpg",
        "label": "人物来源",
        "element_to_extract": "the standing person including facial features, hairstyle, body proportions, and current outfit",
        "extraction_role": "character_source",
        "strength": 0.85
      },
      {
        "id": "bg_source",
        "path": "./mountain_landscape.jpg",
        "label": "背景来源",
        "element_to_extract": "the mountain landscape with a lake in the foreground and snow-capped peaks in the distance",
        "extraction_role": "background_source",
        "strength": 0.80
      }
    ],
    "composition_plan": {
      "description": "The person from source A is standing on the lakeside shore, facing the mountain range. The mountain lake landscape from source B fills the entire background. The person is positioned slightly off-center (rule of thirds) in the foreground.",
      "spatial_layout": "Person in left-center foreground (about 1/3 from left edge). Mountain lake landscape filling the full background.",
      "blending_notes": "Match the natural daylight direction on the person to the lighting in the landscape. Ensure realistic shadow direction."
    }
  },
  "composition": {
    "framing": "full_body",
    "angle": "eye_level",
    "focus_point": "person"
  }
}
```

### 4. Two Images: Character + Clothing Style

**Scenario**: Dress a character in clothing from another image.

```json
{
  "user_intent": "The person from photo A wearing the outfit style from photo B, walking in a modern city",
  "meta": {
    "aspect_ratio": "4:5",
    "image_size": "2K",
    "quality": "ultra_photorealistic"
  },
  "multi_image_reference": {
    "mode": "multi_reference",
    "reference_sources": [
      {
        "id": "person_ref",
        "path": "./person_photo.jpg",
        "label": "人物参考",
        "element_to_extract": "the person's face, body type, and overall physical appearance",
        "extraction_role": "character_source",
        "strength": 0.88
      },
      {
        "id": "outfit_ref",
        "path": "./fashion_photo.jpg",
        "label": "服装参考",
        "element_to_extract": "the outfit including the jacket design, fabric texture, and overall styling",
        "extraction_role": "clothing_source",
        "strength": 0.80
      }
    ],
    "composition_plan": {
      "description": "The person from source A wearing the outfit from source B, walking confidently down a modern city street with glass buildings. The outfit should be adapted to fit the person's body type.",
      "spatial_layout": "Person in center, walking towards camera, city street extending into the background",
      "blending_notes": "Adapt the outfit fabric and color accurately but fit it naturally to the person's body proportions"
    }
  },
  "scene": {
    "location": "modern city street with glass buildings",
    "time": "golden_hour",
    "lighting": {"type": "natural", "direction": "backlight"}
  }
}
```

### 5. Three Images: Character + Style + Background

**Scenario**: Combine character, artistic style, and background from three different sources.

```json
{
  "user_intent": "The person rendered in Studio Ghibli style, standing in the forest background",
  "meta": {
    "aspect_ratio": "3:2",
    "image_size": "2K",
    "quality": "anime_v6"
  },
  "multi_image_reference": {
    "mode": "multi_reference",
    "reference_sources": [
      {
        "id": "char_ref",
        "path": "./person.jpg",
        "label": "角色参考",
        "element_to_extract": "the person's facial features, hairstyle, and overall appearance for character recognition",
        "extraction_role": "character_source",
        "strength": 0.82
      },
      {
        "id": "style_ref",
        "path": "./ghibli_art.jpg",
        "label": "风格参考",
        "element_to_extract": "the Studio Ghibli art style including soft watercolor textures, warm tones, and hand-drawn quality",
        "extraction_role": "style_source",
        "strength": 0.70
      },
      {
        "id": "bg_ref",
        "path": "./forest_photo.jpg",
        "label": "背景参考",
        "element_to_extract": "the lush green forest with sunlight filtering through the canopy and a small stream",
        "extraction_role": "background_source",
        "strength": 0.75
      }
    ],
    "composition_plan": {
      "description": "The person from source A rendered in the Ghibli art style from source B, standing in the forest from source C. The character has a gentle expression, looking up at the sunlight through the trees.",
      "spatial_layout": "Character in the center-left foreground. Forest fills the background with sunlight rays coming from the upper right.",
      "blending_notes": "Apply the watercolor texture and warm color grading uniformly across the entire image to maintain Ghibli aesthetic consistency"
    }
  },
  "style_modifiers": {
    "medium": "anime",
    "aesthetic": ["ghibli", "soft", "warm"]
  }
}
```

### 6. Multiple Characters: Two People in a New Scene

**Scenario**: Combine two people from different photos into one new scene.

```json
{
  "user_intent": "Two friends walking together on a beach at sunset",
  "meta": {
    "aspect_ratio": "16:9",
    "image_size": "2K",
    "quality": "ultra_photorealistic"
  },
  "multi_image_reference": {
    "mode": "multi_reference",
    "reference_sources": [
      {
        "id": "person_A",
        "path": "./friend_1.jpg",
        "label": "朋友A",
        "element_to_extract": "the person's face, build, and appearance for recognition",
        "extraction_role": "character_source",
        "strength": 0.85
      },
      {
        "id": "person_B",
        "path": "./friend_2.jpg",
        "label": "朋友B",
        "element_to_extract": "the person's face, build, and appearance for recognition",
        "extraction_role": "character_source",
        "strength": 0.85
      }
    ],
    "composition_plan": {
      "description": "Person A and Person B walking side by side on a sandy beach during golden hour sunset. They are walking towards the camera, both smiling and laughing. Waves gently lapping at the shore.",
      "spatial_layout": "Person A on the left, Person B on the right. Both in the middle ground. Sunset ocean behind them.",
      "interactions": ["Person A and Person B are walking close together, Person A's arm slightly reaching towards Person B as if mid-conversation"],
      "blending_notes": "Ensure both characters have consistent lighting from the sunset direction (warm golden light from behind-right). Match skin tones between the two characters."
    }
  },
  "scene": {
    "location": "sandy beach with ocean",
    "time": "golden_hour",
    "lighting": {"type": "natural_sunset", "direction": "backlight"}
  }
}
```

---

## Best Practices

### 1. Precise Element Description

The `element_to_extract` field is the most critical for good results. Be specific:

| Bad | Good |
|-----|------|
| "the cat" | "the orange tabby cat including its fur pattern, body shape, and facial features" |
| "the background" | "the mountain landscape with a lake in the foreground and snow-capped peaks in the distance" |
| "the style" | "the watercolor texture, warm tones, and soft brushwork of the impressionist painting" |

### 2. Composition Plan Clarity

The `composition_plan.description` should read like a single, coherent image description that weaves all elements together. Don't just list elements — describe the **final image** with spatial relationships.

### 3. Strength Selection

- Start with **0.80** for characters and objects
- Use **0.70** for backgrounds and styles
- Increase to **0.85-0.90** when identity/recognition is critical
- Decrease to **0.50-0.65** for abstract style/color references

### 4. Blending Notes

Always include `blending_notes` when combining elements from different lighting conditions:
- Specify light direction matching
- Mention color temperature consistency
- Describe how to handle edge transitions

### 5. When to Use Interactions

Use the `interactions` array when:
- Multiple characters need to physically interact (holding hands, hugging)
- One element affects another (shadow casting, reflection)
- There's a narrative relationship between elements

---

## Command Usage

### Single Image Multi-Reference

```bash
python .claude/skills/gemini-image-generator-skill/scripts/generate_image.py \
  --prompt-json '{"user_intent":"A cat in a cyberpunk street","multi_image_reference":{"mode":"multi_reference","reference_sources":[{"id":"cat_source","path":"./my_cat.jpg","label":"猫咪","element_to_extract":"the cat","extraction_role":"character_source","strength":0.85}],"composition_plan":{"description":"Cat walking in neon-lit cyberpunk street"}}}' \
  --input-images ./my_cat.jpg
```

### Multiple Image Multi-Reference

```bash
python .claude/skills/gemini-image-generator-skill/scripts/generate_image.py \
  --prompt-json '{"user_intent":"Person in mountain landscape","multi_image_reference":{"mode":"multi_reference","reference_sources":[{"id":"person","path":"./portrait.jpg","label":"人物","element_to_extract":"the person","extraction_role":"character_source","strength":0.85},{"id":"bg","path":"./landscape.jpg","label":"背景","element_to_extract":"the mountain landscape","extraction_role":"background_source","strength":0.80}],"composition_plan":{"description":"Person standing in front of mountain lake"}}}' \
  --input-images ./portrait.jpg ./landscape.jpg
```

---

## Signal Words for Multi-Image Reference

| User says | Mode |
|-----------|------|
| "用图里的猫，画一个XX场景" | Multi-Ref (1 image) |
| "借鉴这张图的配色" | Multi-Ref (1 image) |
| "把图A的人放到图B的背景里" | Multi-Ref (2 images) |
| "人物来自图A，风格来自图B" | Multi-Ref (2 images) |
| "Combine person from A with background from B" | Multi-Ref (2 images) |
| "Use the style of A, scene of B, character of C" | Multi-Ref (3 images) |
