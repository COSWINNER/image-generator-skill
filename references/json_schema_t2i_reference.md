# Nano Banana Structured JSON Prompt Reference

This document provides a comprehensive reference for the structured JSON prompt schema used by Gemini 3 Pro Image generation.

## Schema Overview

The JSON prompt schema contains the following main sections:

| Section | Description | Required | Domain |
|---------|-------------|----------|--------|
| `user_intent` | Natural language summary of the goal | No | All |
| `meta` | Global settings (aspect ratio, quality, domain, etc.) | Recommended | All |
| `subject` | Array of characters/objects in the image | Recommended | Photography |
| `scene` | Environment and atmosphere settings | Recommended | Photography |
| `technical` | Virtual photography/camera settings | No | Photography |
| `composition` | Framing and angle settings | No | Photography |
| `graphic_design` | Graphic design specific settings (poster, logo, etc.) | Recommended | Graphic Design |
| `ui_design` | UI/Interface design specific settings | Recommended | UI Design |
| `text_rendering` | Settings for text in the image | No | All |
| `style_modifiers` | Artistic style overrides | No | All |
| `advanced` | Negative prompts and fine-tuning | No | All |

## Section Details

### user_intent

A simple string describing the overall goal.

```json
{
  "user_intent": "A cyberpunk warrior standing in a neon-lit alley"
}
```

### meta

Global image generation settings.

| Field | Type | Options | Description |
|-------|------|---------|-------------|
| `domain` | string | `photography`, `graphic_design`, `ui_design` | Generation domain (default: `photography`) |
| `aspect_ratio` | string | `1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9` | Output dimensions |
| `image_size` | string | `1K`, `2K`, `4K` | Output resolution (default: `1K`) |
| `quality` | string | `ultra_photorealistic`, `standard`, `raw`, `anime_v6`, `3d_render_octane`, `oil_painting`, `sketch`, `pixel_art`, `vector_illustration` | Rendering mode |
| `safety_filter` | string | `block_none`, `block_few`, `block_some`, `block_most` | Content filtering |
| `seed` | integer | any number | For reproducible results |
| `steps` | integer | 10-100 | Denoising steps (higher = more detail) |
| `guidance_scale` | number | 1.0-20.0 | How strictly AI follows prompt |

### subject

Array of characters or objects. Each subject can have:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier (e.g., "hero", "villain") |
| `type` | string | `person`, `animal`, `cyborg`, `monster`, `statue`, `robot`, `vehicle`, `object` |
| `description` | string | Visual traits description |
| `name` | string | Famous character/person name |
| `age` | string | Age description |
| `gender` | string | `male`, `female`, `non-binary`, `androgynous` |
| `body_type` | string | Body/build description, e.g., `slim athletic build`, `curvy hourglass`, `broad-shouldered` |
| `skin_texture` | string | Skin rendering instruction, e.g., `visible pores and micro-details, natural dewy glow, no airbrushing` |
| `gaze` | string | Eye direction and emotional quality, e.g., `looking directly at viewer with soft doe eyes` |
| `hair` | object | Hair style and color |
| `position` | string | `center`, `left`, `right`, `far_left`, `far_right`, `background`, `foreground` |
| `pose` | string | Action/pose description |
| `expression` | string | Facial expression |
| `clothing` | array | Garments worn; supports `item`, `color`, `fabric`, `fit`, `texture`, `drape`, `pattern` |
| `accessories` | array | Jewelry, bags, eyewear, etc. |
| `input_image` | object | Reference image for image-to-image |

#### input_image (for image-to-image generation)

```json
{
  "input_image": {
    "path": "./reference.jpg",
    "usage_type": "face_id",
    "strength": 0.85
  }
}
```

Usage types:
- `face_id`: Swap/preserve face identity
- `pose_copy`: Copy skeleton/stance
- `clothing_transfer`: Copy outfit
- `depth_map`: Copy 3D shape
- `full_character_reference`: Full character reference
- `style_transfer`: Transfer artistic style

### scene

Environment settings.

| Field | Type | Description |
|-------|------|-------------|
| `location` | string | Setting description (e.g., "tokyo street", "mars colony") |
| `time` | string | `golden_hour`, `blue_hour`, `high_noon`, `midnight`, `sunrise`, `sunset`, `twilight`, `pitch_black` |
| `weather` | string | `clear_skies`, `overcast`, `rainy`, `stormy`, `snowing`, `foggy`, `hazy`, `sandstorm`, `acid_rain` |
| `lighting` | object | Lighting type and direction; recommended sub-fields: `type`, `direction`, `color_temperature`, `mood`, `specular_highlights`, `shadow_style` |
| `foreground_elements` | string | Elements closest to camera, e.g., `blurred drink bottles near camera` |
| `midground` | string | Main subject zone or middle layer description |
| `background_elements` | array | Background items (e.g., "flying cars", "cherry blossoms") |
| `atmosphere` | string | Overall mood, e.g., `intimate late-night convenience store`, `dreamy ethereal fog` |
| `depth_of_field` | string | Bokeh/DOF instruction, e.g., `shallow f/1.8 bokeh`, `deep focus, everything sharp` |

### technical

Camera/photography settings.

| Field | Type | Description |
|-------|------|-------------|
| `camera_model` | string | `iPhone 15 Pro`, `Sony A7R IV`, `Leica M6`, etc. |
| `lens` | string | `16mm` (ultra wide) to `400mm` (telephoto) |
| `aperture` | string | `f/1.2` (bokeh) to `f/16` (sharp) |
| `shutter_speed` | string | `1/8000` (freeze) to `long_exposure_bulb` |
| `iso` | string | `100` (clean) to `12800` (grainy) |
| `film_stock` | string | `Kodak Portra 400`, `CineStill 800T`, `Fujifilm Pro 400H`, `Kodak Gold 200`, `Ilford HP5`, `Kodak Ektar 100`, `Portra 800`, etc. |
| `filter_effect` | string | Post-processing filter, e.g., `soft black mist filter`, `CCD camera harsh flash`, `vintage warm grade` |
| `color_grade` | string | Color grading style, e.g., `pastel low contrast`, `high contrast neon`, `warm film shift` |
| `film_grain` | string | Grain/noise description, e.g., `authentic 35mm grain`, `fine subtle grain`, `heavy CCD noise` |

### composition

Framing settings.

| Field | Type | Options |
|-------|------|---------|
| `framing` | string | `extreme_close_up`, `close_up`, `medium_shot`, `cowboy_shot`, `full_body`, `wide_shot`, `extreme_wide_shot`, `macro_detail` |
| `angle` | string | `eye_level`, `low_angle`, `high_angle`, `dutch_angle`, `bird_eye_view`, `worm_eye_view`, `overhead`, `pov`, `drone_view` |
| `focus_point` | string | `face`, `eyes`, `hands`, `background`, `foreground_object`, `whole_scene` |

### text_rendering

For rendering text in images.

```json
{
  "text_rendering": {
    "enabled": true,
    "text_content": "HELLO",
    "placement": "neon_sign_on_wall",
    "font_style": "cyberpunk_digital",
    "color": "glowing cyan"
  }
}
```

### graphic_design

Graphic design specific settings (used when `domain="graphic_design"`).

| Field | Type | Description |
|-------|------|-------------|
| `design_type` | string | Design type (see options below) |
| `layout` | object | Layout system configuration |
| `hierarchy` | object | Visual hierarchy settings |
| `color_scheme` | object | Color palette configuration |
| `typography` | object | Typography settings |
| `elements` | array | Design elements (text, shapes, icons, etc.) |
| `visual_style` | object | Visual style and effects |

#### design_type Options

| Value | Description |
|-------|-------------|
| `poster` | Poster design |
| `flyer` | Flyer/handout |
| `business_card` | Business card |
| `logo` | Logo design |
| `social_media_post` | Social media image |
| `banner` | Banner/header |
| `infographic` | Information graphic |
| `book_cover` | Book cover |
| `album_cover` | Album cover |
| `packaging` | Product packaging |

#### layout Options

| Sub-field | Type | Options |
|-----------|------|---------|
| `grid_system` | string | `modular_grid`, `column_grid`, `hierarchical`, `free_form`, `golden_ratio` |
| `alignment` | string | `left_aligned`, `center_aligned`, `right_aligned`, `justified` |
| `spacing` | string | `minimal_whitespace`, `balanced`, `generous_whitespace`, `maximal_impact` |
| `balance` | string | `symmetric`, `asymmetric`, `radial`, `rule_of_thirds` |

#### hierarchy Options

| Sub-field | Type | Options |
|-----------|------|---------|
| `primary_focus` | string | `main_headline`, `hero_image`, `brand_logo`, `cta_button`, `product_image` |
| `visual_flow` | string | `z_pattern`, `f_pattern`, `circular`, `vertical_top_to_bottom`, `horizontal_left_to_right` |

#### color_scheme Options

| Sub-field | Type | Options |
|-----------|------|---------|
| `palette_type` | string | `monochromatic`, `analogous`, `complementary`, `triadic`, `split_complementary`, `tetradic`, `neutral`, `vibrant`, `pastel`, `dark`, `gradient` |
| `primary_color` | string | Primary color (hex code or color name) |
| `secondary_color` | string | Secondary color (hex code or color name) |
| `accent_color` | string | Accent color (hex code or color name) |

#### typography Options

| Sub-field | Type | Options |
|-----------|------|---------|
| `headline_font` | string | `bold_sans_serif`, `elegant_serif`, `display_font`, `handwritten`, `modern_geometric`, `vintage` |
| `body_font` | string | `clean_sans_serif`, `readable_serif`, `monospace`, `light`, `condensed` |

#### elements Array

Each element can have:

| Field | Type | Options |
|-------|------|---------|
| `type` | string | `headline`, `subheading`, `body_text`, `cta_button`, `icon`, `illustration`, `shape`, `pattern`, `background`, `logo`, `product_image` |
| `content` | string | Text content or description |
| `style` | string | Style description |
| `placement` | string | Position in layout (e.g., "top_left", "center", "bottom_right") |
| `font_style` | string | Text style, e.g., `ultra-bold condensed sans serif`, `elegant serif`, `handwritten brush` |
| `color` | string | Element or text color |
| `background_shape` | string | Shape behind text or content, e.g., `rounded orange badge`, `paper label`, `sticker burst` |
| `headline` | string | Main advertising headline |
| `tagline` | string | Supporting slogan or product promise |
| `brand_label` | string | Brand/product label to render or imply |

#### visual_style Options

| Sub-field | Type | Options |
|-----------|------|---------|
| `mood` | string | `professional`, `playful`, `elegant`, `bold`, `minimalist`, `luxurious`, `friendly`, `dramatic`, `calm`, `energetic` |
| `texture` | string | `smooth`, `grainy`, `paper_texture`, `metallic`, `glass_morphism`, `neomorphism`, `flat`, `3d_render` |
| `effects` | string | Effects like `drop_shadow`, `glow`, `gradient_overlay`, `noise`, `none` |

### ui_design

UI/Interface design specific settings (used when `domain="ui_design"`).

| Field | Type | Description |
|-------|------|-------------|
| `component_type` | string | UI component type (see options below) |
| `layout` | object | Layout structure |
| `components` | array | UI components array |
| `color_system` | object | Color system configuration |
| `typography_system` | object | Typography system |
| `interaction_states` | object | Interactive states |
| `styling` | object | Component styling details |
| `iconography` | object | Icon system |
| `design_system` | string | Design system reference |

#### component_type Options

| Value | Description |
|-------|-------------|
| `mobile_app_screen` | Mobile application screen |
| `dashboard` | Dashboard/data panel |
| `landing_page` | Landing page/homepage |
| `settings_panel` | Settings panel |
| `form` | Form interface |
| `card` | Card component |
| `modal` | Modal dialog |
| `navigation_bar` | Navigation bar |
| `sidebar` | Sidebar |
| `table` | Table view |
| `chat_interface` | Chat/messaging interface |
| `ecommerce_product` | E-commerce product page |

#### layout Options

| Sub-field | Type | Options |
|-----------|------|---------|
| `structure` | string | `single_column`, `two_column`, `three_column`, `grid`, `masonry`, `stack`, `tabs`, `accordion` |
| `columns` | integer | Number of columns (e.g., 2, 3, 4) |
| `spacing` | string | `compact`, `comfortable`, `spacious` |

#### components Array

Each component can have:

| Field | Type | Options |
|-------|------|---------|
| `type` | string | `button`, `card`, `input_field`, `dropdown`, `checkbox`, `toggle_switch`, `slider`, `progress_bar`, `badge`, `avatar`, `icon_button`, `tab_bar`, `breadcrumb`, `pagination`, `modal`, `tooltip`, `table`, `chart`, `sidebar`, `navigation_bar`, `bottom_sheet`, `search_bar`, `notification` |
| `variant` | string | `primary`, `secondary`, `outline`, `ghost`, `danger`, `success`, `warning`, `info` |
| `state` | string | `default`, `hover`, `active`, `focused`, `disabled`, `loading`, `error`, `success` |
| `size` | string | `small`, `medium`, `large` |
| `style` | string | Style description |

#### color_system Options

| Sub-field | Type | Options |
|-----------|------|---------|
| `mode` | string | `light_mode`, `dark_mode`, `high_contrast`, `auto` |
| `primary` | string | Primary color (hex code) |
| `secondary` | string | Secondary color (hex code) |
| `background` | string | Background color (hex code) |
| `surface` | string | Surface color (hex code) |

#### typography_system Options

| Sub-field | Type | Options |
|-----------|------|---------|
| `scale` | string | `material_design`, `apple_human_interface`, `fluent_typography`, `tailwind`, `custom` |
| `font_family` | string | Font family name |

#### interaction_states Options

| Sub-field | Type | Options |
|-----------|------|---------|
| `hover_effect` | string | `color_change`, `scale_up`, `underline`, `glow`, `elevation`, `none` |
| `focus_style` | string | `outline`, `ring`, `background_change`, `none` |

#### styling Options

| Sub-field | Type | Options |
|-----------|------|---------|
| `border_radius` | string | `none`, `small_rounded` (4px), `medium_rounded` (8px), `large_rounded` (16px), `extra_large_rounded` (24px), `fully_rounded` |
| `shadow` | string | `none`, `subtle_elevation`, `soft_elevation`, `medium_elevation`, `high_elevation`, `dramatic_shadow` |

#### iconography Options

| Sub-field | Type | Options |
|-----------|------|---------|
| `style` | string | `outlined`, `filled`, `rounded`, `sharp`, `two_tone`, `duotone`, `minimal`, `detailed` |
| `size` | string | `small`, `medium`, `large` |

#### design_system Options

| Value | Description |
|-------|-------------|
| `material_design` | Google Material Design |
| `apple_human_interface` | Apple Human Interface Guidelines |
| `fluent` | Microsoft Fluent Design |
| `bootstrap` | Bootstrap design system |
| `tailwind` | Tailwind CSS defaults |
| `ant_design` | Ant Design |
| `chakra_ui` | Chakra UI |
| `custom` | Custom design system |

### style_modifiers

Artistic style overrides.

| Field | Type | Description |
|-------|------|-------------|
| `medium` | string | `photography`, `3d_render`, `oil_painting`, `watercolor`, `pencil_sketch`, `ink_drawing`, `anime`, `concept_art`, `flat_illustration`, `isometric_design`, `3d_minimal`, `abstract_geometric`, `swiss_style`, `brutalist_design`, `neo_brutalism`, `glass_morphism`, `neomorphism`, `gradient_mesh`, `collage_style`, etc. |
| `aesthetic` | array | `cyberpunk`, `steampunk`, `vaporwave`, `synthwave`, `noir`, `minimalist`, `gothic`, `baroque`, `retro_80s`, etc. |
| `artist_reference` | array | Names of artists to mimic (use with caution) |

### advanced

Fine-tuning options.

| Field | Type | Description |
|-------|------|-------------|
| `negative_prompt` | array | Elements to exclude (e.g., "blur", "low quality", "bad hands") |
| `magic_prompt_enhancer` | boolean | When true, Claude should expand the JSON during prompt construction with richer concrete details; the script does not call an extra LLM |
| `auto_skin_texture` | boolean | Auto-add realistic skin texture hints for photography when not explicitly provided (default: true) |
| `auto_film_aesthetic` | boolean | Auto-add camera/film aesthetic hints for photography when technical settings are absent (default: true) |
| `hdr_mode` | boolean | High Dynamic Range balancing |

## Example Prompts

### Simple Portrait

```json
{
  "user_intent": "Professional headshot of a business executive",
  "meta": {
    "aspect_ratio": "4:5",
    "quality": "ultra_photorealistic"
  },
  "subject": [{
    "type": "person",
    "description": "confident business executive",
    "gender": "female",
    "age": "40s",
    "expression": "smiling",
    "clothing": [{
      "item": "blazer",
      "color": "navy blue",
      "fabric": "wool"
    }]
  }],
  "scene": {
    "location": "modern office",
    "lighting": {
      "type": "studio_softbox",
      "direction": "front_lit"
    }
  },
  "composition": {
    "framing": "close_up",
    "angle": "eye_level",
    "focus_point": "eyes"
  }
}
```

### Cyberpunk Scene

```json
{
  "user_intent": "Cyberpunk hacker in a neon-lit alley",
  "meta": {
    "aspect_ratio": "21:9",
    "quality": "ultra_photorealistic"
  },
  "subject": [{
    "type": "cyborg",
    "description": "young hacker with cybernetic eye implant",
    "hair": {
      "style": "undercut",
      "color": "electric_blue"
    },
    "pose": "crouching while typing on holographic keyboard",
    "clothing": [{
      "item": "hoodie",
      "color": "matte black",
      "fabric": "mesh"
    }],
    "accessories": [{
      "item": "VR goggles",
      "material": "chrome",
      "location": "head"
    }]
  }],
  "scene": {
    "location": "cyberpunk alley",
    "time": "midnight",
    "weather": "rainy",
    "lighting": {
      "type": "neon_lights",
      "direction": "rim_light"
    },
    "background_elements": ["holographic advertisements", "flying drones", "steam vents"]
  },
  "style_modifiers": {
    "aesthetic": ["cyberpunk", "noir"]
  },
  "technical": {
    "film_stock": "CineStill 800T"
  }
}
```

### Image-to-Image Example

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
      "strength": 0.8
    }
  }],
  "style_modifiers": {
    "medium": "anime",
    "aesthetic": ["minimalist"]
  }
}
```

### Summer Sale Poster (Graphic Design)

```json
{
  "user_intent": "Vibrant summer sale poster with 50% off promotion",
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
      "spacing": "generous_whitespace",
      "balance": "asymmetric"
    },
    "hierarchy": {
      "primary_focus": "main_headline",
      "visual_flow": "vertical_top_to_bottom"
    },
    "color_scheme": {
      "palette_type": "vibrant",
      "primary_color": "tropical orange",
      "secondary_color": "sky blue",
      "accent_color": "sunset yellow"
    },
    "typography": {
      "headline_font": "bold_sans_serif",
      "body_font": "clean_sans_serif"
    },
    "elements": [
      {
        "type": "headline",
        "content": "SUMMER SALE",
        "style": "large bold",
        "placement": "top_center"
      },
      {
        "type": "headline",
        "content": "50% OFF",
        "style": "giant display",
        "placement": "center"
      },
      {
        "type": "cta_button",
        "content": "SHOP NOW",
        "style": "rounded rectangular",
        "placement": "bottom_center"
      },
      {
        "type": "illustration",
        "content": "tropical beach scene with palm trees",
        "placement": "background"
      }
    ],
    "visual_style": {
      "mood": "energetic",
      "texture": "smooth",
      "effects": "gradient_overlay"
    }
  }
}
```

### Tech Dashboard (UI Design)

```json
{
  "user_intent": "Modern dark mode analytics dashboard with data visualization",
  "meta": {
    "domain": "ui_design",
    "aspect_ratio": "16:9",
    "quality": "ultra_photorealistic"
  },
  "ui_design": {
    "component_type": "dashboard",
    "layout": {
      "structure": "grid",
      "columns": 3,
      "spacing": "comfortable"
    },
    "components": [
      {
        "type": "card",
        "variant": "primary",
        "state": "default",
        "size": "medium",
        "style": "elevated with subtle shadow"
      },
      {
        "type": "chart",
        "variant": "primary",
        "style": "line chart with smooth curves"
      },
      {
        "type": "sidebar",
        "variant": "secondary",
        "style": "collapsed with icon navigation"
      },
      {
        "type": "search_bar",
        "variant": "outline",
        "state": "default",
        "style": "rounded with search icon"
      }
    ],
    "color_system": {
      "mode": "dark_mode",
      "primary": "#6366f1",
      "secondary": "#8b5cf6",
      "background": "#0f172a",
      "surface": "#1e293b"
    },
    "typography_system": {
      "scale": "material_design",
      "font_family": "Inter"
    },
    "interaction_states": {
      "hover_effect": "elevation",
      "focus_style": "ring"
    },
    "styling": {
      "border_radius": "medium_rounded",
      "shadow": "subtle_elevation"
    },
    "iconography": {
      "style": "rounded",
      "size": "medium"
    },
    "design_system": "material_design"
  }
}
```

### Tech Company Logo (Graphic Design)

```json
{
  "user_intent": "Minimalist logo for a cloud computing company named 'CloudNine'",
  "meta": {
    "domain": "graphic_design",
    "aspect_ratio": "1:1",
    "quality": "vector_illustration"
  },
  "graphic_design": {
    "design_type": "logo",
    "layout": {
      "grid_system": "golden_ratio",
      "alignment": "center_aligned",
      "spacing": "minimal_whitespace",
      "balance": "symmetric"
    },
    "hierarchy": {
      "primary_focus": "brand_logo",
      "visual_flow": "circular"
    },
    "color_scheme": {
      "palette_type": "monochromatic",
      "primary_color": "electric blue",
      "secondary_color": "white",
      "accent_color": "cyan"
    },
    "typography": {
      "headline_font": "modern_geometric",
      "body_font": "clean_sans_serif"
    },
    "elements": [
      {
        "type": "logo",
        "content": "stylized cloud icon with nine distinct segments",
        "style": "geometric minimalist",
        "placement": "center"
      },
      {
        "type": "headline",
        "content": "CloudNine",
        "style": "modern sans-serif",
        "placement": "bottom_center"
      }
    ],
    "visual_style": {
      "mood": "professional",
      "texture": "smooth",
      "effects": "none"
    }
  },
  "style_modifiers": {
    "medium": "flat_illustration",
    "aesthetic": ["minimalist"]
  }
}
```
