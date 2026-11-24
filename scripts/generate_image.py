#!/usr/bin/env python3
"""Generate an image from a final prompt using the selected provider SDK."""

import argparse
import base64
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
import json
import os
from pathlib import Path
import re
import sys
from tempfile import NamedTemporaryFile
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import urlopen
from uuid import uuid4


PROVIDERS = {
    "gemini": ("GEMINI_API_KEY", "gemini-3-pro-image-preview"),
    "gpt": ("OPENAI_API_KEY", "gpt-image-2"),
    "qwen": ("DASHSCOPE_API_KEY", "qwen-image-3.0"),
}
ENV_PREFIXES = {"gemini": "GEMINI", "gpt": "OPENAI", "qwen": "QWEN"}

PROVIDER_OPTIONS = {
    "gemini": ("aspect_ratio", "image_size"),
    "gpt": ("size", "quality"),
    "qwen": ("size", "negative_prompt"),
}
REFERENCE_MIME_TYPES = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
GPT_IMAGE_MODELS = {"gpt-image-1", "gpt-image-1-mini", "gpt-image-1.5", "gpt-image-2",
                    "gpt-image-2-2026-04-21", "chatgpt-image-latest"}


@dataclass
class ReferenceImage:
    data: bytes
    mime_type: str


@dataclass
class ImageResult:
    request_id: str | None = None
    data: bytes | None = None
    encoded: str | None = None
    url: str | None = None
    detail: str = "Provider returned no image."


class DashScopeError(RuntimeError):
    def __init__(self, response):
        self.request_id = response.request_id
        self.status_code = response.status_code
        message = " - ".join(str(value) for value in (response.code, response.message) if value)
        super().__init__(message or f"DashScope returned HTTP {self.status_code}.")


def parse_size(value):
    if not re.fullmatch(r"[1-9][0-9]*[xX][1-9][0-9]*", value):
        raise argparse.ArgumentTypeError("expected WIDTHxHEIGHT with positive pixel dimensions")
    return value.lower()


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Generate an image with Gemini, GPT Image, or Qwen Image.",
        allow_abbrev=False,
    )
    parser.add_argument("--prompt", required=True, help="Final prompt to send unchanged to the provider")
    parser.add_argument("--input-images", nargs="+", metavar="PATH", help="Reference images in input order")
    parser.add_argument("--output-dir", type=Path, default=Path("generation-image"),
                        help="Output directory (default: ./generation-image)")
    parser.add_argument("--model", help="Override the configured model for this run")
    parser.add_argument("--aspect-ratio", help="Gemini aspect ratio, for example 16:9")
    parser.add_argument("--image-size", help="Gemini resolution tier, for example 2K")
    parser.add_argument("--size", type=parse_size, metavar="WIDTHxHEIGHT", help="GPT or Qwen pixel dimensions")
    parser.add_argument("--quality", choices=("auto", "low", "medium", "high"), help="GPT image quality")
    parser.add_argument("--negative-prompt", help="Qwen's separate negative prompt")
    args = parser.parse_args(argv)
    if not args.prompt.strip():
        parser.error("--prompt must contain non-whitespace text")
    return args


def env_flag(name):
    value = os.getenv(name, "false").strip().lower()
    if value in {"true", "1", "yes", "on"}:
        return True
    if value in {"false", "0", "no", "off"}:
        return False
    raise ValueError(f"{name} must be true or false.")


def load_references(paths, image_module, image_ops):
    references = []
    for path in paths:
        try:
            data = Path(path).read_bytes()
            with image_module.open(BytesIO(data)) as source:
                source.load()
                mime_type = REFERENCE_MIME_TYPES.get(source.format)
                orientation = source.getexif().get(image_module.ExifTags.Base.Orientation, 1)
                if mime_type and orientation == 1 and not getattr(source, "is_animated", False):
                    references.append(ReferenceImage(data, mime_type))
                    continue

                image = image_ops.exif_transpose(source)
                if image.mode not in {"RGB", "RGBA"}:
                    has_alpha = "A" in image.getbands() or "transparency" in image.info
                    image = image.convert("RGBA" if has_alpha else "RGB")
                with BytesIO() as buffer:
                    image.save(buffer, format="PNG")
                    references.append(ReferenceImage(buffer.getvalue(), "image/png"))
        except (OSError, ValueError, image_module.DecompressionBombError) as exc:
            raise ValueError(f"Cannot read reference image {path}: {exc}") from exc
    return references


def generate_gemini(api_key, base_url, model, prompt, references, options, google_search):
    from google import genai
    from google.genai import types

    client_options = {"vertexai": False, "api_key": api_key}
    if base_url:
        client_options["http_options"] = types.HttpOptions(base_url=base_url)

    config_options = {"response_modalities": ["TEXT", "IMAGE"]}
    if options:
        config_options["image_config"] = types.ImageConfig(**options)
    if google_search:
        config_options["tools"] = [types.Tool(google_search=types.GoogleSearch())]

    parts = [types.Part.from_bytes(data=image.data, mime_type=image.mime_type) for image in references]
    parts.append(types.Part.from_text(text=prompt))
    with genai.Client(**client_options) as client:
        response = client.models.generate_content(
            model=model, contents=parts, config=types.GenerateContentConfig(**config_options)
        )

    result = ImageResult(request_id=request_id_from(response.sdk_http_response))
    finish_reasons = []
    for candidate in response.candidates or []:
        if candidate.finish_reason:
            finish_reasons.append(str(candidate.finish_reason))
        parts = candidate.content.parts if candidate.content else None
        for part in parts or []:
            blob = part.inline_data
            if part.thought or not blob or not blob.data:
                continue
            if not blob.mime_type or blob.mime_type.startswith("image/"):
                result.data = blob.data
                return result

    block_reason = getattr(response.prompt_feedback, "block_reason", None)
    if block_reason:
        result.detail = f"Gemini blocked the prompt ({block_reason})."
    elif finish_reasons:
        result.detail = f"Gemini returned no image ({', '.join(finish_reasons)})."
    return result


def generate_gpt(api_key, base_url, model, prompt, references, options):
    from openai import OpenAI

    with OpenAI(api_key=api_key, base_url=base_url) as client:
        if references:
            files = [
                (f"reference-{index}.{image.mime_type.split('/')[1]}", image.data, image.mime_type)
                for index, image in enumerate(references, start=1)
            ]
            response = client.images.edit(
                model=model, prompt=prompt, image=files if len(files) > 1 else files[0], **options
            )
        else:
            response = client.images.generate(model=model, prompt=prompt, **options)

    result = ImageResult(request_id=response._request_id)
    for image in response.data or []:
        if image.b64_json or image.url:
            result.encoded = image.b64_json
            result.url = image.url
            break
    return result


def is_qwen_3_model(model):
    return model == "qwen-image-3.0" or model.startswith("qwen-image-3.0-")


def generate_qwen(api_key, base_url, model, prompt, references, options, prompt_extend):
    import dashscope

    if base_url:
        dashscope.base_http_api_url = base_url

    content = [
        {"image": f"data:{image.mime_type};base64," + base64.b64encode(image.data).decode("ascii")}
        for image in references
    ]
    content.append({"text": prompt})

    parameters = {**options, "prompt_extend": prompt_extend}
    if "size" in parameters:
        parameters["size"] = parameters["size"].replace("x", "*")
    if prompt_extend and is_qwen_3_model(model):
        parameters["prompt_extend_mode"] = "direct"

    response = dashscope.MultiModalConversation.call(
        api_key=api_key, model=model, messages=[{"role": "user", "content": content}], **parameters
    )
    if response.status_code != 200:
        raise DashScopeError(response)

    result = ImageResult(request_id=response.request_id)
    for choice in (response.output or {}).get("choices") or []:
        for item in (choice.get("message") or {}).get("content") or []:
            if isinstance(item, dict) and item.get("image"):
                result.url = item["image"]
                return result
    return result


def request_id_from(response):
    headers = getattr(response, "headers", None) or {}
    return headers.get("x-request-id") or headers.get("x-goog-request-id")


def download_image(url, base_url):
    if base_url:
        url = urljoin(base_url.rstrip("/") + "/", url)
    parsed = urlsplit(url)
    if parsed.scheme not in {"https", "http"} or not parsed.hostname:
        raise ValueError("Provider returned an invalid image URL.")

    try:
        with urlopen(url, timeout=30) as response:
            return response.read()
    except HTTPError as exc:
        raise ValueError(f"Image download from {parsed.hostname} returned HTTP {exc.code}.") from exc
    except (URLError, TimeoutError, OSError) as exc:
        reason = exc.reason if isinstance(exc, URLError) else exc
        raise ValueError(f"Image download from {parsed.hostname} failed: {reason}") from exc


def save_image(data, output_dir, run_id, image_module):
    with image_module.open(BytesIO(data)) as image:
        image.load()
        extension = "jpg" if image.format == "JPEG" else image.format.lower()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = output_dir / f"generated_{timestamp}_{run_id}.{extension}"
    temporary_path = None
    try:
        with NamedTemporaryFile(dir=output_dir, prefix=".generating_", delete=False) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(data)
        temporary_path.replace(path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return path


def log_event(output_dir, event, **fields):
    record = {"ts": datetime.now().isoformat(timespec="milliseconds"), "event": event, **fields}
    try:
        with (output_dir / "generation.log").open("a", encoding="utf-8") as log:
            log.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass


def main(argv=None):
    args = parse_args(argv)
    run = {"run_id": uuid4().hex, "provider": None, "model": None}
    stage = "configuration"
    request_id = None
    output_dir = args.output_dir
    install_command = "Install the shared dependencies with: python -m pip install Pillow python-dotenv"
    try:
        output_dir = output_dir.resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)
        provider = os.getenv("IMAGE_PROVIDER", "gemini").strip().lower()
        run["provider"] = provider
        if provider not in PROVIDERS:
            raise ValueError("IMAGE_PROVIDER must be gemini, gpt, or qwen.")
        key_name, default_model = PROVIDERS[provider]
        prefix = ENV_PREFIXES[provider]
        model = args.model or os.getenv(f"{prefix}_MODEL") or default_model
        run["model"] = model
        paths = args.input_images or []
        log_event(output_dir, "start", **run, reference_count=len(paths))

        api_key = os.getenv(key_name)
        if not api_key:
            raise ValueError(f"Set {key_name} for the {provider} provider.")
        base_url = os.getenv(f"{prefix}_BASE_URL") or None
        options = {}
        for option in ("aspect_ratio", "image_size", "size", "quality", "negative_prompt"):
            value = getattr(args, option)
            if value is not None:
                if option not in PROVIDER_OPTIONS[provider]:
                    raise ValueError(f"--{option.replace('_', '-')} is unsupported by {provider}.")
                options[option] = value
        google_search = provider == "gemini" and env_flag("GEMINI_GOOGLE_SEARCH")
        prompt_extend = provider == "qwen" and env_flag("QWEN_PROMPT_EXTEND")

        stage = "input"
        if provider == "qwen" and is_qwen_3_model(model) and len(paths) > 3:
            raise ValueError(f"{model} accepts at most 3 reference images.")
        if provider == "gemini" and model.rsplit("/", 1)[-1] == "gemini-3-pro-image-preview" and len(paths) > 14:
            raise ValueError(f"{model} accepts at most 14 reference images.")
        if provider == "gpt" and model in GPT_IMAGE_MODELS and len(paths) > 16:
            raise ValueError(f"{model} accepts at most 16 reference images.")
        from PIL import Image, ImageOps

        references = load_references(paths, Image, ImageOps)
        stage = "api"
        if provider == "gemini":
            install_command = "Install the Gemini SDK with: python -m pip install -U google-genai"
            result = generate_gemini(api_key, base_url, model, args.prompt, references, options, google_search)
        elif provider == "gpt":
            install_command = "Install the OpenAI SDK with: python -m pip install -U openai"
            result = generate_gpt(api_key, base_url, model, args.prompt, references, options)
        else:
            install_command = "Install the DashScope SDK with: python -m pip install -U dashscope"
            result = generate_qwen(api_key, base_url, model, args.prompt, references, options, prompt_extend)

        request_id = result.request_id
        stage = "response"
        if result.encoded:
            data = base64.b64decode(result.encoded, validate=True)
        elif result.data:
            data = result.data
        elif result.url:
            stage = "download"
            data = download_image(result.url, base_url)
        else:
            raise ValueError(result.detail)

        stage = "image"
        path = save_image(data, output_dir, run["run_id"], Image)
    except Exception as exc:
        request_id = request_id or getattr(exc, "request_id", None) or request_id_from(getattr(exc, "response", None))
        status_code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
        message = f"{exc}. {install_command}" if isinstance(exc, ImportError) else str(exc)
        print(f"Error ({stage}): {message}", file=sys.stderr)
        log_event(output_dir, "final", **run, ok=False, stage=stage, status_code=status_code,
                  request_id=request_id, error=message[:1000])
        return 1

    log_event(output_dir, "final", **run, ok=True, request_id=request_id, path=str(path))
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
