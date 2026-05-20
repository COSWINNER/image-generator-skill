#!/usr/bin/env python3
"""
Image Generation Script (Gemini + OpenAI/GPT)

This script generates images using either Gemini 3 Pro Image API or OpenAI GPT Image API.
Supports both text-to-image and image-to-image generation.

Configuration (priority: .env > system environment variables > defaults):
    IMAGE_PROVIDER: Provider to use - "gemini" or "gpt" (default: gemini)

    Gemini:
        GEMINI_API_KEY: Your Gemini API key (required when provider=gemini)
        GEMINI_BASE_URL: Custom base URL for API endpoint (optional)
        GEMINI_MODEL: Model name for image generation (default: gemini-3-pro-image-preview)

    OpenAI/GPT:
        OPENAI_API_KEY: Your OpenAI API key (required when provider=gpt)
        OPENAI_BASE_URL: Custom base URL for API endpoint (optional)
        OPENAI_MODEL: Model name for image generation (default: gpt-image-2)

Usage:
    python generate_image.py --prompt-json '<json_string>' [--input-images <path1> <path2> ...]
"""

import os
import sys
import json
import argparse
import base64
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Error: google-genai package not installed.")
    print("Please install with: pip install -q -U google-genai")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow package not installed.")
    print("Please install with: pip install Pillow")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: python-dotenv package not installed.")
    print("Please install with: pip install python-dotenv")
    sys.exit(1)

try:
    import openai
except ImportError:
    openai = None


# Non-photorealistic quality/modifier values that should suppress
# automatic realistic skin texture and film aesthetic injections
NON_PHOTOREALISTIC_QUALITIES = {
    "anime_v6", "3d_render_octane", "oil_painting", "sketch",
    "pixel_art", "vector_illustration", "flat_illustration", "hand_drawn"
}
NON_PHOTOREALISTIC_MEDIUMS = {
    "anime", "3d_render", "oil_painting", "watercolor", "pencil_sketch",
    "ink_drawing", "concept_art", "flat_illustration", "isometric_design",
    "3d_minimal", "abstract_geometric", "collage_style"
}


def get_env_value(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get environment value with priority: .env > system env > default.

    Args:
        key: Environment variable name
        default: Default value if not found

    Returns:
        The value from the highest priority source
    """
    # Load .env file (overrides system env if set)
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path, override=True)

    # Check .env first (already loaded to os.environ)
    value = os.environ.get(key)

    return value if value is not None else default


def get_client() -> genai.Client:
    """Initialize Gemini client with environment configuration."""
    api_key = get_env_value("GEMINI_API_KEY")
    base_url = get_env_value("GEMINI_BASE_URL")

    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is not set.")
        sys.exit(1)

    client_kwargs = {"api_key": api_key}

    if base_url:
        # Configure custom base URL if provided
        client_kwargs["http_options"] = types.HttpOptions(base_url=base_url)

    return genai.Client(**client_kwargs)


def get_openai_client():
    """Initialize OpenAI client with environment configuration."""
    if openai is None:
        print("Error: openai package not installed.")
        print("Please install with: pip install -q -U openai")
        sys.exit(1)

    api_key = get_env_value("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable is not set.")
        sys.exit(1)

    client_kwargs = {"api_key": api_key}

    base_url = get_env_value("OPENAI_BASE_URL")
    if base_url:
        client_kwargs["base_url"] = base_url

    return openai.OpenAI(**client_kwargs)


def load_input_images(image_paths: list[str]) -> list:
    """Load input images for image-to-image generation."""
    images = []
    for path in image_paths:
        try:
            img = Image.open(path)
            images.append(img)
            print(f"Loaded input image: {path}")
        except Exception as e:
            print(f"Warning: Failed to load image {path}: {e}")
    return images


def extract_multi_ref_image_paths(prompt_json: dict) -> list[str]:
    """Extract image paths from multi_image_reference section."""
    multi_ref = prompt_json.get("multi_image_reference", {})
    if multi_ref.get("mode") != "multi_reference":
        return []
    return [s["path"] for s in multi_ref.get("reference_sources", []) if "path" in s]


def build_prompt_text(prompt_json: dict) -> str:
    """
    Convert structured JSON prompt to natural language prompt.
    Supports three domains: photography, graphic_design, ui_design
    """
    parts = []

    # User intent
    if "user_intent" in prompt_json:
        parts.append(prompt_json["user_intent"])

    # Multi-image reference mode (text-driven composition with element extraction)
    multi_ref = prompt_json.get("multi_image_reference")
    if multi_ref and multi_ref.get("mode") == "multi_reference":
        multi_parts = _build_multi_reference_prompt(multi_ref)
        if multi_parts:
            parts.extend(multi_parts)

    # Get domain, default to photography
    meta = prompt_json.get("meta", {})
    domain = meta.get("domain", "photography")

    # Quality (shared by all domains)
    if "quality" in meta:
        parts.append(f"Style: {meta['quality'].replace('_', ' ')}")

    # Domain-specific rendering
    if domain == "graphic_design":
        parts.extend(_build_graphic_design_prompt(prompt_json))
    elif domain == "ui_design":
        parts.extend(_build_ui_design_prompt(prompt_json))
    else:  # photography (default)
        parts.extend(_build_photography_prompt(prompt_json))

    # Style modifiers (shared by all domains)
    if "style_modifiers" in prompt_json:
        style_parts = _build_style_modifiers(prompt_json["style_modifiers"])
        if style_parts:
            parts.append(style_parts)

    # Negative prompt
    negative_items = []
    if "advanced" in prompt_json and "negative_prompt" in prompt_json["advanced"]:
        negative_items.extend(prompt_json["advanced"]["negative_prompt"])

    advanced = prompt_json.get("advanced", {})

    if domain == "photography":
        quality = meta.get("quality", "")
        medium = prompt_json.get("style_modifiers", {}).get("medium", "")
        is_non_photorealistic = (
            quality in NON_PHOTOREALISTIC_QUALITIES or
            medium in NON_PHOTOREALISTIC_MEDIUMS
        )

        if is_non_photorealistic:
            photo_excludes = ["blur", "watermark", "text overlay", "realistic pores",
                              "photorealistic skin", "bad hands", "deformed fingers", "low quality"]
        else:
            photo_excludes = ["blur", "watermark", "text overlay", "plastic skin",
                              "airbrushing", "bad hands", "deformed fingers", "low quality"]
        negative_items.extend(photo_excludes)

        subjects = prompt_json.get("subject", [])
        has_person_subject = any(subj.get("type", "person") == "person" for subj in subjects)
        has_skin_texture = any("skin_texture" in subj for subj in subjects)
        if advanced.get("auto_skin_texture", True) and has_person_subject and not has_skin_texture and not is_non_photorealistic:
            parts.append("realistic skin texture, visible pores, natural imperfections")

        if advanced.get("auto_film_aesthetic", True) and has_person_subject and "technical" not in prompt_json and not is_non_photorealistic:
            parts.append("photorealistic camera capture, natural lens rendering, subtle film aesthetic")

    # Domain-specific automatic negative prompts
    if domain == "ui_design":
        # For UI design, exclude device frames, monitors, screens to get pure UI
        ui_excludes = ["monitor", "computer screen", "device frame", "laptop", "phone frame", "tablet frame", "display bezel", "physical device", "realistic device rendering", "photograph of screen"]
        negative_items.extend(ui_excludes)
    elif domain == "graphic_design":
        # For graphic design, exclude photorealistic elements if using illustration quality
        if meta.get("quality") in ["vector_illustration", "flat_illustration"]:
            gd_excludes = ["photorealistic", "realistic lighting", "camera effects", "depth of field", "bokeh"]
            negative_items.extend(gd_excludes)

    if negative_items:
        negative_items = list(dict.fromkeys(negative_items))
        parts.append(f"Avoid: {', '.join(negative_items)}")

    return "\n".join(parts)


def _build_photography_prompt(prompt_json: dict) -> list[str]:
    """Build prompt for photography domain."""
    parts = []

    # Subject descriptions
    if "subject" in prompt_json:
        for idx, subj in enumerate(prompt_json["subject"]):
            subj_desc = []

            if "name" in subj:
                subj_desc.append(subj["name"])

            if "type" in subj:
                subj_desc.append(f"({subj['type']})")

            if "description" in subj:
                subj_desc.append(subj["description"])

            if "age" in subj:
                subj_desc.append(f", {subj['age']}")

            if "gender" in subj:
                subj_desc.append(f", {subj['gender']}")

            if "body_type" in subj:
                subj_desc.append(f", {subj['body_type']}")

            if "hair" in subj:
                hair = subj["hair"]
                hair_desc = []
                if "color" in hair:
                    hair_desc.append(hair["color"].replace("_", " "))
                if "style" in hair:
                    hair_desc.append(hair["style"].replace("_", " "))
                if hair_desc:
                    subj_desc.append(f", {' '.join(hair_desc)} hair")

            if "pose" in subj:
                subj_desc.append(f", {subj['pose']}")

            if "expression" in subj:
                subj_desc.append(f", {subj['expression']} expression")

            if "gaze" in subj:
                subj_desc.append(f", {subj['gaze']}")

            if "skin_texture" in subj:
                subj_desc.append(f", {subj['skin_texture']}")

            if "position" in subj:
                subj_desc.append(f", positioned {subj['position'].replace('_', ' ')}")

            # Clothing
            if "clothing" in subj:
                clothes = []
                for item in subj["clothing"]:
                    cloth_desc = []
                    if "color" in item:
                        cloth_desc.append(item["color"])
                    if "fabric" in item:
                        cloth_desc.append(item["fabric"])
                    if "item" in item:
                        cloth_desc.append(item["item"])
                    if "fit" in item:
                        cloth_desc.append(f"({item['fit']})")
                    if "texture" in item:
                        cloth_desc.append(f"with {item['texture']}")
                    if "drape" in item:
                        cloth_desc.append(f"with {item['drape']}")
                    if "pattern" in item:
                        cloth_desc.append(f"{item['pattern']} pattern")
                    if cloth_desc:
                        clothes.append(" ".join(cloth_desc))
                if clothes:
                    subj_desc.append(f", wearing {', '.join(clothes)}")

            # Accessories
            if "accessories" in subj:
                accs = []
                for acc in subj["accessories"]:
                    acc_desc = []
                    if "material" in acc:
                        acc_desc.append(acc["material"])
                    if "color" in acc:
                        acc_desc.append(acc["color"])
                    if "item" in acc:
                        acc_desc.append(acc["item"])
                    if acc_desc:
                        accs.append(" ".join(acc_desc))
                if accs:
                    subj_desc.append(f", with {', '.join(accs)}")

            if subj_desc:
                parts.append(f"Subject {idx + 1}: " + "".join(subj_desc))

    # Scene description
    if "scene" in prompt_json:
        scene = prompt_json["scene"]
        scene_desc = []

        if "location" in scene:
            scene_desc.append(f"Location: {scene['location']}")

        if "time" in scene:
            scene_desc.append(f"Time: {scene['time'].replace('_', ' ')}")

        if "weather" in scene:
            scene_desc.append(f"Weather: {scene['weather'].replace('_', ' ')}")

        if "lighting" in scene:
            lighting = scene["lighting"]
            light_parts = []
            if "type" in lighting:
                light_parts.append(lighting["type"].replace("_", " "))
            if "direction" in lighting:
                light_parts.append(lighting["direction"].replace("_", " "))
            if "color_temperature" in lighting:
                light_parts.append(lighting["color_temperature"].replace("_", " "))
            if "mood" in lighting:
                light_parts.append(lighting["mood"].replace("_", " "))
            if "specular_highlights" in lighting:
                light_parts.append(f"specular highlights: {lighting['specular_highlights']}")
            if "shadow_style" in lighting:
                light_parts.append(f"shadows: {lighting['shadow_style'].replace('_', ' ')}")
            if light_parts:
                scene_desc.append(f"Lighting: {', '.join(light_parts)}")

        if "foreground_elements" in scene:
            scene_desc.append(f"Foreground: {scene['foreground_elements']}")

        if "midground" in scene:
            scene_desc.append(f"Midground: {scene['midground']}")

        if "background_elements" in scene:
            scene_desc.append(f"Background: {', '.join(scene['background_elements'])}")

        if "atmosphere" in scene:
            scene_desc.append(f"Atmosphere: {scene['atmosphere']}")

        if "depth_of_field" in scene:
            scene_desc.append(f"DOF: {scene['depth_of_field']}")

        if scene_desc:
            parts.append("Scene: " + "; ".join(scene_desc))

    # Technical/Camera settings
    if "technical" in prompt_json:
        tech = prompt_json["technical"]
        tech_desc = []

        if "camera_model" in tech:
            tech_desc.append(f"Shot on {tech['camera_model']}")

        if "lens" in tech:
            tech_desc.append(f"{tech['lens']} lens")

        if "aperture" in tech:
            tech_desc.append(tech["aperture"])

        if "film_stock" in tech:
            tech_desc.append(f"{tech['film_stock']} film look")

        if "filter_effect" in tech:
            tech_desc.append(tech["filter_effect"])

        if "color_grade" in tech:
            tech_desc.append(tech["color_grade"])

        if "film_grain" in tech:
            tech_desc.append(tech["film_grain"])

        if tech_desc:
            parts.append("Technical: " + ", ".join(tech_desc))

    # Composition
    if "composition" in prompt_json:
        comp = prompt_json["composition"]
        comp_desc = []

        if "framing" in comp:
            comp_desc.append(comp["framing"].replace("_", " "))

        if "angle" in comp:
            comp_desc.append(f"{comp['angle'].replace('_', ' ')} angle")

        if "focus_point" in comp:
            comp_desc.append(f"focus on {comp['focus_point'].replace('_', ' ')}")

        if comp_desc:
            parts.append("Composition: " + ", ".join(comp_desc))

    # Text rendering
    if "text_rendering" in prompt_json and prompt_json["text_rendering"].get("enabled"):
        text = prompt_json["text_rendering"]
        text_desc = []

        if "text_content" in text:
            text_desc.append(f'text "{text["text_content"]}"')

        if "placement" in text:
            text_desc.append(f"as {text['placement'].replace('_', ' ')}")

        if "font_style" in text:
            text_desc.append(f"in {text['font_style'].replace('_', ' ')} style")

        if "color" in text:
            text_desc.append(f"colored {text['color']}")

        if text_desc:
            parts.append("Text: " + " ".join(text_desc))

    return parts


def _build_graphic_design_prompt(prompt_json: dict) -> list[str]:
    """Build prompt for graphic design domain."""
    parts = []

    if "graphic_design" not in prompt_json:
        return parts

    gd = prompt_json["graphic_design"]

    # Design type
    if "design_type" in gd:
        parts.append(f"Design: {gd['design_type'].replace('_', ' ')}")

    # Layout
    if "layout" in gd:
        layout = gd["layout"]
        layout_desc = []
        if "grid_system" in layout:
            layout_desc.append(layout["grid_system"].replace("_", " "))
        if "alignment" in layout:
            layout_desc.append(layout["alignment"].replace("_", " "))
        if "spacing" in layout:
            layout_desc.append(layout["spacing"].replace("_", " "))
        if "balance" in layout:
            layout_desc.append(layout["balance"].replace("_", " "))
        if layout_desc:
            parts.append(f"Layout: {', '.join(layout_desc)}")

    # Hierarchy
    if "hierarchy" in gd:
        hierarchy = gd["hierarchy"]
        hierarchy_desc = []
        if "primary_focus" in hierarchy:
            hierarchy_desc.append(f"focus on {hierarchy['primary_focus'].replace('_', ' ')}")
        if "visual_flow" in hierarchy:
            hierarchy_desc.append(f"{hierarchy['visual_flow'].replace('_', ' ')} flow")
        if hierarchy_desc:
            parts.append(f"Hierarchy: {', '.join(hierarchy_desc)}")

    # Color scheme
    if "color_scheme" in gd:
        colors = gd["color_scheme"]
        color_desc = []
        if "palette_type" in colors:
            color_desc.append(colors["palette_type"].replace("_", " "))
        if "primary_color" in colors:
            color_desc.append(f"primary {colors['primary_color'].replace('_', ' ')}")
        if "secondary_color" in colors:
            color_desc.append(f"secondary {colors['secondary_color'].replace('_', ' ')}")
        if "accent_color" in colors:
            color_desc.append(f"accent {colors['accent_color'].replace('_', ' ')}")
        if color_desc:
            parts.append(f"Colors: {', '.join(color_desc)}")

    # Typography
    if "typography" in gd:
        typo = gd["typography"]
        typo_desc = []
        if "headline_font" in typo:
            typo_desc.append(f"headline: {typo['headline_font'].replace('_', ' ')}")
        if "body_font" in typo:
            typo_desc.append(f"body: {typo['body_font'].replace('_', ' ')}")
        if typo_desc:
            parts.append(f"Typography: {', '.join(typo_desc)}")

    # Elements
    if "elements" in gd:
        elements_desc = []
        for elem in gd["elements"]:
            elem_desc = elem.get("type", "element").replace("_", " ")
            if "content" in elem:
                elem_desc += f" '{elem['content']}'"
            if "style" in elem:
                elem_desc += f" ({elem['style'].replace('_', ' ')})"
            if "font_style" in elem:
                elem_desc += f" [font: {elem['font_style'].replace('_', ' ')}]"
            if "color" in elem:
                elem_desc += f" [color: {elem['color'].replace('_', ' ')}]"
            if "background_shape" in elem:
                elem_desc += f" [on {elem['background_shape'].replace('_', ' ')}]"
            if "brand_label" in elem:
                elem_desc += f" [brand: {elem['brand_label']}]"
            if "headline" in elem:
                elem_desc += f" [headline: {elem['headline']}]"
            if "tagline" in elem:
                elem_desc += f" [tagline: {elem['tagline']}]"
            if "placement" in elem:
                elem_desc += f" [{elem['placement'].replace('_', ' ')}]"
            elements_desc.append(elem_desc)
        if elements_desc:
            parts.append(f"Elements: {', '.join(elements_desc)}")

    # Visual style
    if "visual_style" in gd:
        style = gd["visual_style"]
        style_desc = []
        if "mood" in style:
            style_desc.append(style["mood"])
        if "texture" in style:
            style_desc.append(style["texture"].replace("_", " "))
        if "effects" in style and style["effects"] != "none":
            style_desc.append(style["effects"].replace("_", " "))
        if style_desc:
            parts.append(f"Style: {', '.join(style_desc)}")

    return parts


def _build_ui_design_prompt(prompt_json: dict) -> list[str]:
    """Build prompt for UI design domain."""
    parts = []

    if "ui_design" not in prompt_json:
        return parts

    ui = prompt_json["ui_design"]

    # Component type
    if "component_type" in ui:
        parts.append(f"UI Component: {ui['component_type'].replace('_', ' ')}")

    # Layout
    if "layout" in ui:
        layout = ui["layout"]
        layout_desc = []
        if "structure" in layout:
            layout_desc.append(layout["structure"].replace("_", " "))
        if "columns" in layout:
            layout_desc.append(f"{layout['columns']} columns")
        if "spacing" in layout:
            layout_desc.append(layout["spacing"].replace("_", " "))
        if layout_desc:
            parts.append(f"Layout: {', '.join(layout_desc)}")

    # Components
    if "components" in ui:
        comp_desc = []
        for comp in ui["components"]:
            c = f"{comp['type'].replace('_', ' ')}"
            if "variant" in comp:
                c += f" ({comp['variant']})"
            if "state" in comp and comp["state"] != "default":
                c += f" [{comp['state']}]"
            if "size" in comp:
                c += f" size: {comp['size']}"
            if "style" in comp:
                c += f" style: {comp['style'].replace('_', ' ')}"
            comp_desc.append(c)
        if comp_desc:
            parts.append(f"Components: {', '.join(comp_desc)}")

    # Color system
    if "color_system" in ui:
        colors = ui["color_system"]
        color_desc = []
        if "mode" in colors:
            color_desc.append(colors["mode"].replace("_", " "))
        if "primary" in colors:
            color_desc.append(f"primary {colors['primary']}")
        if color_desc:
            parts.append(f"Colors: {', '.join(color_desc)}")

    # Typography system
    if "typography_system" in ui:
        typo = ui["typography_system"]
        typo_desc = []
        if "scale" in typo:
            typo_desc.append(typo["scale"].replace("_", " "))
        if "font_family" in typo:
            typo_desc.append(typo["font_family"].replace("_", " "))
        if typo_desc:
            parts.append(f"Typography: {', '.join(typo_desc)}")

    # Interaction states
    if "interaction_states" in ui:
        states = ui["interaction_states"]
        states_desc = []
        if "hover_effect" in states and states["hover_effect"] != "none":
            states_desc.append(f"hover: {states['hover_effect'].replace('_', ' ')}")
        if "focus_style" in states and states["focus_style"] != "none":
            states_desc.append(f"focus: {states['focus_style'].replace('_', ' ')}")
        if states_desc:
            parts.append(f"Interactions: {', '.join(states_desc)}")

    # Styling
    if "styling" in ui:
        styling = ui["styling"]
        style_desc = []
        if "border_radius" in styling:
            style_desc.append(f"radius: {styling['border_radius'].replace('_', ' ')}")
        if "shadow" in styling and styling["shadow"] != "none":
            style_desc.append(styling["shadow"].replace("_", " "))
        if style_desc:
            parts.append(f"Styling: {', '.join(style_desc)}")

    # Iconography
    if "iconography" in ui:
        icons = ui["iconography"]
        icon_desc = []
        if "style" in icons:
            icon_desc.append(icons["style"])
        if "size" in icons:
            icon_desc.append(f"{icons['size']} size")
        if icon_desc:
            parts.append(f"Icons: {', '.join(icon_desc)}")

    # Design system reference
    if "design_system" in ui:
        parts.append(f"Design System: {ui['design_system'].replace('_', ' ')}")

    return parts


def _build_style_modifiers(style_modifiers: dict) -> str:
    """Build style modifiers string (shared by all domains)."""
    style_desc = []

    if "medium" in style_modifiers:
        style_desc.append(style_modifiers["medium"].replace("_", " "))

    if "aesthetic" in style_modifiers:
        aesthetics = [a.replace("_", " ") for a in style_modifiers["aesthetic"]]
        style_desc.append(", ".join(aesthetics))

    if "artist_reference" in style_modifiers:
        style_desc.append(f"in the style of {', '.join(style_modifiers['artist_reference'])}")

    if style_desc:
        return "Style: " + ", ".join(style_desc)
    return ""


def _build_multi_reference_prompt(multi_ref: dict) -> list[str]:
    """Build prompt for multi-image reference mode."""
    parts = []
    sources = multi_ref.get("reference_sources", [])
    if not sources:
        return parts

    parts.append("MULTI-IMAGE COMPOSITING TASK:")
    parts.append("Create a NEW image combining specific elements extracted from the provided source images. The overall scene is described by text; images provide specific elements to incorporate.")

    parts.append("\nSOURCE IMAGES (provided in order):")
    for i, source in enumerate(sources, 1):
        source_id = source.get("id", f"source_{i}")
        role = source.get("extraction_role", "reference")
        element = source.get("element_to_extract", "all visual elements")
        label = source.get("label", source_id)
        parts.append(f'- Image {i} ("{source_id}" - {role}): Extract {element}.')

    comp = multi_ref.get("composition_plan", {})
    if comp:
        parts.append("\nCOMPOSITION INSTRUCTIONS:")
        if "description" in comp:
            parts.append(comp["description"])
        if "spatial_layout" in comp:
            parts.append(f"SPATIAL LAYOUT: {comp['spatial_layout']}")
        if "camera_perspective" in comp:
            parts.append(f"CAMERA PERSPECTIVE: {comp['camera_perspective']}")
        if "lighting_consistency" in comp:
            parts.append(f"LIGHTING CONSISTENCY: {comp['lighting_consistency']}")
        if "scale_relationships" in comp:
            parts.append(f"SCALE RELATIONSHIPS: {comp['scale_relationships']}")
        if "interactions" in comp and comp["interactions"]:
            parts.append(f"INTERACTIONS: {'; '.join(comp['interactions'])}")
        if "blending_notes" in comp:
            parts.append(f"BLENDING: {comp['blending_notes']}")

    return parts


def generate_image(
    client: genai.Client,
    prompt_json: dict,
    input_images: Optional[list] = None,
    output_dir: str = "./generation-image",
    model_override: Optional[str] = None
) -> str:
    """
    Generate image using Gemini 3 Pro Image.

    Args:
        client: Gemini client instance
        prompt_json: Structured JSON prompt
        input_images: Optional list of PIL Image objects for image-to-image
        output_dir: Directory to save generated images
        model_override: Optional model name to override env config

    Returns:
        Path to the generated image file
    """
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Build text prompt from JSON
    prompt_text = build_prompt_text(prompt_json)
    print(f"\n--- Generated Prompt ---\n{prompt_text}\n------------------------\n")

    # Build content list
    contents = []

    # Add input images for image-to-image generation
    if input_images:
        for img in input_images:
            contents.append(img)
        contents.append(prompt_text)
    else:
        contents.append(prompt_text)

    # Extract configuration from JSON
    meta = prompt_json.get("meta", {})

    # Build image configuration
    image_config_kwargs = {}

    # Aspect ratio
    if "aspect_ratio" in meta:
        image_config_kwargs["aspect_ratio"] = meta["aspect_ratio"]

    # Image size (resolution): 1K, 2K, or 4K (default: 2K)
    image_config_kwargs["image_size"] = meta.get("image_size", "2K")

    # Build generation config
    config = types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
        image_config=types.ImageConfig(**image_config_kwargs) if image_config_kwargs else None,
        tools=[{"google_search": {}}]
    )

    # Get model (priority: CLI override > .env > system env > default)
    model = model_override or get_env_value("GEMINI_MODEL", "gemini-3-pro-image-preview")

    # Generate image
    print(f"Generating image with {model}...")
    try:
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config
        )
    except Exception as e:
        print(f"Error generating image: {e}")
        sys.exit(1)

    # Process response and save image
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_saved = False
    response_text = ""

    for part in response.candidates[0].content.parts:
        if part.text is not None:
            response_text = part.text
            print(f"Model response: {part.text}")
        elif part.inline_data is not None:
            # Use the official as_image() method to get PIL Image
            try:
                image = part.as_image()

                # Generate filename
                filename = f"generated_{timestamp}.png"
                filepath = output_path / filename

                # Save using PIL
                image.save(str(filepath))

                print(f"Image saved to: {filepath}")
                image_saved = True
                return str(filepath)
            except AttributeError:
                # Fallback: if as_image() not available, try direct data access
                # inline_data.data is already bytes, no need to base64 decode
                image_data = part.inline_data.data

                # Determine file extension based on mime type
                mime_type = part.inline_data.mime_type
                ext = "png"
                if "jpeg" in mime_type or "jpg" in mime_type:
                    ext = "jpg"
                elif "webp" in mime_type:
                    ext = "webp"

                # Generate filename
                filename = f"generated_{timestamp}.{ext}"
                filepath = output_path / filename

                with open(filepath, "wb") as f:
                    f.write(image_data)

                print(f"Image saved to: {filepath}")
                image_saved = True
                return str(filepath)

    if not image_saved:
        print("Warning: No image was generated in the response.")
        if response_text:
            print(f"Model only returned text: {response_text}")
        return ""

    return ""


# ===== GPT/OpenAI Image Generation =====

# Size mapping: (aspect_ratio, image_size) -> GPT pixel size string
GPT_SIZE_MAP = {
    ("1:1", "1K"): "1024x1024",
    ("1:1", "2K"): "2048x2048",
    ("1:1", "4K"): "4096x4096",
    ("2:3", "1K"): "864x1296",
    ("2:3", "2K"): "1728x2592",
    ("3:2", "1K"): "1296x864",
    ("3:2", "2K"): "2592x1728",
    ("3:4", "1K"): "896x1184",
    ("3:4", "2K"): "1792x2368",
    ("4:3", "1K"): "1184x896",
    ("4:3", "2K"): "2368x1792",
    ("4:5", "1K"): "928x1152",
    ("4:5", "2K"): "1856x2304",
    ("5:4", "1K"): "1152x928",
    ("5:4", "2K"): "2304x1856",
    ("9:16", "1K"): "768x1376",
    ("9:16", "2K"): "1536x2752",
    ("16:9", "1K"): "1376x768",
    ("16:9", "2K"): "2752x1536",
    ("21:9", "1K"): "1584x672",
    ("21:9", "2K"): "3168x1344",
}

GPT_QUALITY_MAP = {
    "ultra_photorealistic": "high",
    "standard": "medium",
    "raw": "high",
    "anime_v6": "medium",
    "3d_render_octane": "high",
    "oil_painting": "high",
    "sketch": "low",
    "pixel_art": "low",
    "vector_illustration": "medium",
    "flat_illustration": "medium",
    "hand_drawn": "low",
}


def map_size_for_gpt(aspect_ratio: str, image_size: str) -> str:
    """Map Gemini aspect_ratio + image_size to GPT pixel size string."""
    # Normalize image_size
    size = image_size.upper() if image_size else "1K"

    # 4K sizes - map to largest valid GPT sizes under constraints
    if size == "4K":
        landscape_ratios = ["3:2", "4:3", "5:4", "16:9", "21:9"]
        if aspect_ratio in landscape_ratios:
            return "3840x2160"
        elif aspect_ratio == "1:1":
            return "4096x4096"
        else:
            return "2160x3840"

    key = (aspect_ratio, size)
    if key in GPT_SIZE_MAP:
        return GPT_SIZE_MAP[key]

    # Fallback: ensure both dimensions are multiples of 16
    return "1024x1024"


def map_quality_for_gpt(quality: Optional[str]) -> str:
    """Map Gemini quality value to GPT quality (low/medium/high/auto)."""
    if not quality:
        return "auto"
    return GPT_QUALITY_MAP.get(quality, "auto")


def sanitize_gpt_reference_prompt(prompt: str) -> str:
    lines = [line for line in prompt.splitlines() if not line.startswith("Avoid:")]
    return "\n".join(lines).replace("orthographic", "top-down 2D")


def build_safe_prompt_text(prompt_json: dict) -> str:
    return prompt_json.get("user_intent") or "Generate a clean natural image."


def build_safe_gpt_reference_prompt(prompt_json: dict) -> str:
    intent = prompt_json.get("user_intent") or "Use the input image as visual reference and generate a clean image."
    return sanitize_gpt_reference_prompt(intent)


def is_proxy_tool_error(error: Exception) -> bool:
    message = str(error)
    return "Tool choice 'image_generation'" in message and "tools" in message


def edit_image_gpt(client, model: str, image, prompt: str, size: str, quality: str):
    return client.images.edit(
        model=model,
        image=image,
        prompt=prompt,
        size=size,
        quality=quality,
    )


def generate_image_gpt(
    prompt_json: dict,
    input_images: Optional[list] = None,
    output_dir: str = "./generation-image",
    model_override: Optional[str] = None
) -> str:
    """Generate image using OpenAI GPT Image API."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    prompt_text = build_prompt_text(prompt_json)
    print(f"\n--- Generated Prompt ---\n{prompt_text}\n------------------------\n")

    meta = prompt_json.get("meta", {})
    aspect_ratio = meta.get("aspect_ratio", "1:1")
    image_size = meta.get("image_size", "1K")
    quality = map_quality_for_gpt(meta.get("quality"))
    size = map_size_for_gpt(aspect_ratio, image_size)
    model = model_override or get_env_value("OPENAI_MODEL", "gpt-image-2")

    client = get_openai_client()

    if input_images:
        prompt_text = sanitize_gpt_reference_prompt(prompt_text)
        print(f"\n--- Sanitized GPT Reference Prompt ---\n{prompt_text}\n--------------------------------------\n")
        print(f"Editing image with {model} (size={size}, quality={quality})...")
        from io import BytesIO
        image_files = []
        for img in input_images:
            buf = BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            image_files.append(buf)

        image_input = image_files if len(image_files) > 1 else image_files[0]
        try:
            result = edit_image_gpt(client, model, image_input, prompt_text, size, quality)
        except Exception as e:
            if not is_proxy_tool_error(e):
                raise
            print("Warning: GPT image edit proxy rejected the prompt; retrying with a simplified prompt...")
            for image_file in image_files:
                image_file.seek(0)
            image_input = image_files if len(image_files) > 1 else image_files[0]
            prompt_text = build_safe_gpt_reference_prompt(prompt_json)
            print(f"\n--- Safe GPT Reference Prompt ---\n{prompt_text}\n---------------------------------\n")
            result = edit_image_gpt(client, model, image_input, prompt_text, size, quality)
        if not result.data:
            print("Warning: No image data in response.")
            return ""
        image_base64 = result.data[0].b64_json
    else:
        # Text-to-image: use generate endpoint
        print(f"Generating image with {model} (size={size}, quality={quality})...")
        try:
            result = client.images.generate(
                model=model,
                prompt=prompt_text,
                size=size,
                quality=quality,
            )
        except Exception as e:
            if not is_proxy_tool_error(e):
                raise
            print("Warning: GPT image generation proxy rejected the prompt; retrying with a simplified prompt...")
            prompt_text = build_safe_prompt_text(prompt_json)
            print(f"\n--- Safe GPT Prompt ---\n{prompt_text}\n-----------------------\n")
            result = client.images.generate(
                model=model,
                prompt=prompt_text,
                size=size,
                quality=quality,
            )
        if not result.data:
            print("Warning: No image data in response.")
            return ""
        image_base64 = result.data[0].b64_json

    if not image_base64:
        print("Warning: No image data in response.")
        return ""

    image_bytes = base64.b64decode(image_base64)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"generated_{timestamp}.png"
    filepath = output_path / filename

    with open(filepath, "wb") as f:
        f.write(image_bytes)

    print(f"Image saved to: {filepath}")
    return str(filepath)


def main():
    parser = argparse.ArgumentParser(
        description="Generate images using Gemini or OpenAI GPT Image API"
    )

    parser.add_argument(
        "--prompt-json",
        type=str,
        required=True,
        help="JSON string containing the structured prompt"
    )

    parser.add_argument(
        "--input-images",
        nargs="+",
        type=str,
        help="Paths to input images for image-to-image generation"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="./generation-image",
        help="Directory to save generated images (default: ./generation-image)"
    )

    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model name to use (overrides env config). Gemini default: gemini-3-pro-image-preview, GPT default: gpt-image-2"
    )

    args = parser.parse_args()

    # Load prompt JSON
    try:
        prompt_json = json.loads(args.prompt_json)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON prompt: {e}")
        sys.exit(1)

    # Determine provider
    provider = get_env_value("IMAGE_PROVIDER", "gemini").lower()
    print(f"Using image provider: {provider}")

    # Load input images if provided
    input_images = None
    if args.input_images:
        input_images = load_input_images(args.input_images)

    # Auto-load images from multi_image_reference section in JSON
    multi_ref_paths = extract_multi_ref_image_paths(prompt_json)
    if multi_ref_paths and not input_images:
        input_images = load_input_images(multi_ref_paths)
    elif multi_ref_paths and input_images:
        all_paths = list(args.input_images)
        for p in multi_ref_paths:
            if p not in all_paths:
                all_paths.append(p)
        input_images = load_input_images(all_paths)

    # Route to appropriate generator
    if provider == "gpt":
        result = generate_image_gpt(
            prompt_json=prompt_json,
            input_images=input_images,
            output_dir=args.output_dir,
            model_override=args.model
        )
    else:
        client = get_client()
        result = generate_image(
            client=client,
            prompt_json=prompt_json,
            input_images=input_images,
            output_dir=args.output_dir,
            model_override=args.model
        )

    if result:
        print(f"\nGeneration complete! Image saved to: {result}")
    else:
        print("\nGeneration completed but no image was saved.")


if __name__ == "__main__":
    main()
