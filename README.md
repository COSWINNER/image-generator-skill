# Image Generator Skill

English | [简体中文](README_CN.md)

Generate or edit raster images from a final text prompt and optional local reference images. The script sends your prompt to the selected official SDK as supplied. You can prepare that text with another project or skill.

## Install

Use Python 3.11 or newer. Install Pillow and python-dotenv, then run the SDK installation command for your provider.

```bash
python -m pip install -U Pillow python-dotenv
python -m pip install -U google-genai  # Gemini
python -m pip install -U openai       # GPT
python -m pip install -U dashscope    # Qwen
```

Copy this directory into your agent's skills directory to use the skill, or run the script directly. Copy [`.env.example`](.env.example) to `.env` alongside [SKILL.md](SKILL.md) and configure your provider. The skill's `.env` takes precedence over system environment variables.

| `IMAGE_PROVIDER` | API key | Optional endpoint and model variables | Default model |
|---|---|---|---|
| `gemini` (default) | `GEMINI_API_KEY` | `GEMINI_BASE_URL`, `GEMINI_MODEL` | `gemini-3-pro-image-preview` |
| `gpt` | `OPENAI_API_KEY` | `OPENAI_BASE_URL`, `OPENAI_MODEL` | `gpt-image-2` |
| `qwen` | `DASHSCOPE_API_KEY` | `QWEN_BASE_URL`, `QWEN_MODEL` | `qwen-image-3.0` |

Use a custom endpoint that implements the selected SDK's API. OpenAI-compatible endpoints typically end in `/v1`. For DashScope, use an endpoint and key from the same region. The environment template includes regional examples.

## Generate images

Run these examples from the repository root, or use the installed script's absolute path from your workspace.

```bash
python scripts/generate_image.py --prompt 'A small cabin in the snow'

python scripts/generate_image.py \
  --prompt 'Use the first image as the subject and the second as the background.' \
  --input-images ./subject.png ./background.jpg \
  --output-dir ./images
```

`--model` overrides the provider's configured model. Reference paths are sent in order. The default models accept up to 14 reference images for Gemini, 16 for GPT, and 3 for Qwen.

### Provider options

| Provider | CLI options | Service settings |
|---|---|---|
| Gemini | `--aspect-ratio 16:9`, `--image-size 2K` | `GEMINI_GOOGLE_SEARCH=true` enables search grounding on supported models. |
| GPT | `--size 1536x1024`, `--quality auto\|low\|medium\|high` | |
| Qwen | `--size 1536x1024`, `--negative-prompt 'Motion blur'` | `QWEN_PROMPT_EXTEND=true` enables rewriting by DashScope. |

Both service settings default to false. Accepted sizes and other generation settings depend on the selected model. Omitted options use the provider's defaults.

## Output and errors

Successful runs print the absolute path of one generated image and exit with status 0. The default output directory is `./generation-image`, relative to the working directory. The file extension reflects the image's actual format.

On failure, the script exits with a nonzero status and reports the error on stderr. Check the latest run in `<output-dir>/generation.log` for the provider, model, failure stage, and request ID when available.

## Test

Install all three SDKs and run `python -m unittest discover -s tests -v`. The tests use a local server and test keys.

## License

MIT
