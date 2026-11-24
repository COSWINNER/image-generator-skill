---
name: image-generator
description: Generate, edit, or combine raster images from a final text prompt and optional reference images using Gemini, OpenAI GPT Image, or Alibaba Qwen Image. Use for image generation requests when this provider-backed workflow is configured.
---

# Image Generator

1. Use the user's image description or the final prompt supplied by an upstream tool verbatim. The CLI requires nonblank text. Prompt writing and optimization requests belong to the user's chosen upstream tool or skill.
2. Pass explicitly requested reference paths and generation settings as separate arguments. Ask for a missing prompt or reference path when required to run.
3. Run `scripts/generate_image.py` from this skill directory or resolve its path relative to this file. Keep the current working directory so relative reference paths and the default output directory resolve in the user's workspace.

```bash
python /path/to/image-generator-skill/scripts/generate_image.py --prompt 'A small cabin in the snow'
python /path/to/image-generator-skill/scripts/generate_image.py --prompt 'Use the first image as the subject and the second as the background.' --input-images ./subject.png ./background.jpg
```

`IMAGE_PROVIDER` selects `gemini` (default), `gpt`, or `qwen`. The skill's `.env` overrides system environment values. Use `--model` for an explicitly requested model, and `--output-dir` for a different destination.

| Provider | Required key | Optional generation flags |
|---|---|---|
| Gemini | `GEMINI_API_KEY` | `--aspect-ratio 16:9`, `--image-size 2K` |
| GPT | `OPENAI_API_KEY` | `--size 1536x1024`, `--quality high` |
| Qwen | `DASHSCOPE_API_KEY` | `--size 1536x1024`, `--negative-prompt 'Motion blur'` |

Use the provider's defaults for omitted settings. `QWEN_PROMPT_EXTEND=true` enables Qwen's service-side prompt rewriting. `GEMINI_GOOGLE_SEARCH=true` enables grounding on Gemini models that support it. Both settings default to false. For installation, model limits, and custom endpoints, see [README.md](README.md) or [README_CN.md](README_CN.md).

On success, report the image path printed by the script. On failure, check stderr and the final entry for the run in `<output-dir>/generation.log`, then report the configured provider, model, and error. Keep the configured provider, model, and user input for the request.
