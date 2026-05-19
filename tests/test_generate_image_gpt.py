import base64
from types import SimpleNamespace

from PIL import Image

from scripts import generate_image


class FakeResponses:
    def __init__(self):
        self.create_calls = []

    def create(self, **kwargs):
        self.create_calls.append(kwargs)
        return SimpleNamespace(
            output=[
                SimpleNamespace(
                    type="image_generation_call",
                    result=base64.b64encode(b"fake-image").decode("ascii"),
                )
            ]
        )


class FakeImages:
    def __init__(self):
        self.edit_calls = []
        self.generate_calls = []

    def edit(self, **kwargs):
        self.edit_calls.append(kwargs)
        return SimpleNamespace(
            data=[SimpleNamespace(b64_json=base64.b64encode(b"fake-image").decode("ascii"))]
        )

    def generate(self, **kwargs):
        self.generate_calls.append(kwargs)
        return SimpleNamespace(
            data=[SimpleNamespace(b64_json=base64.b64encode(b"fake-image").decode("ascii"))]
        )


class FakeOpenAIClient:
    def __init__(self):
        self.images = FakeImages()
        self.responses = FakeResponses()


def test_gpt_text_to_image_still_uses_images_generate(monkeypatch, tmp_path):
    client = FakeOpenAIClient()
    monkeypatch.setattr(generate_image, "get_openai_client", lambda: client)
    monkeypatch.setattr(generate_image, "get_env_value", lambda key, default=None: default)

    prompt_json = {
        "user_intent": "生成一只睡觉的猫",
        "meta": {"aspect_ratio": "1:1", "image_size": "1K", "quality": "standard"},
    }

    output = generate_image.generate_image_gpt(
        prompt_json=prompt_json,
        output_dir=str(tmp_path),
    )

    assert output
    assert len(client.images.generate_calls) == 1
    assert client.responses.create_calls == []
    call = client.images.generate_calls[0]
    assert call["model"] == "gpt-image-2"
    assert call["size"] == "1024x1024"
    assert call["quality"] == "medium"


def test_gpt_reference_image_uses_images_edit(monkeypatch, tmp_path):
    client = FakeOpenAIClient()
    monkeypatch.setattr(generate_image, "get_openai_client", lambda: client)
    monkeypatch.setattr(generate_image, "get_env_value", lambda key, default=None: default)

    prompt_json = {
        "user_intent": "把人物放到山景背景中",
        "meta": {"aspect_ratio": "16:9", "image_size": "1K"},
    }
    input_image = Image.new("RGB", (1, 1), color="red")

    output = generate_image.generate_image_gpt(
        prompt_json=prompt_json,
        input_images=[input_image],
        output_dir=str(tmp_path),
    )

    assert output
    assert client.images.generate_calls == []
    assert client.responses.create_calls == []
    assert len(client.images.edit_calls) == 1
    call = client.images.edit_calls[0]
    assert call["model"] == "gpt-image-2"
    assert call["size"] == "1376x768"
    assert call["quality"] == "auto"
    assert call["prompt"].startswith("把人物放到山景背景中")
    assert call["image"].read().startswith(b"\x89PNG")


def test_gpt_reference_image_rewrites_orthographic_prompt(monkeypatch, tmp_path):
    client = FakeOpenAIClient()
    monkeypatch.setattr(generate_image, "get_openai_client", lambda: client)
    monkeypatch.setattr(generate_image, "get_env_value", lambda key, default=None: default)

    prompt_json = {
        "user_intent": "基于参考图生成便利店俯视布局图",
        "meta": {"domain": "graphic_design", "aspect_ratio": "16:9", "image_size": "1K"},
        "graphic_design": {
            "layout": {
                "grid_system": "strict orthographic architectural plan",
                "alignment": "precise rectangular layout",
            },
        },
    }
    input_image = Image.new("RGB", (1, 1), color="red")

    generate_image.generate_image_gpt(
        prompt_json=prompt_json,
        input_images=[input_image],
        output_dir=str(tmp_path),
    )

    prompt = client.images.edit_calls[0]["prompt"]
    assert "orthographic" not in prompt.lower()
    assert "top-down 2D" in prompt
