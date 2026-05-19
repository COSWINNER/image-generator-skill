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
        self.generate_calls = []

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


def test_gpt_reference_image_uses_responses_image_generation_tool(monkeypatch, tmp_path):
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
    assert len(client.responses.create_calls) == 1
    call = client.responses.create_calls[0]
    assert call["model"] == "gpt-image-2"
    assert call["tools"] == [{"type": "image_generation", "size": "1376x768", "quality": "auto"}]
    assert "tool_choice" not in call
    message_content = call["input"][0]["content"]
    assert message_content[0]["type"] == "input_text"
    assert message_content[1]["type"] == "input_image"
    assert message_content[1]["image_url"].startswith("data:image/png;base64,")
