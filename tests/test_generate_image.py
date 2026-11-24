import base64
from email import policy
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Thread
import unittest

from PIL import Image


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "generate_image.py"
PROMPT = "  保留原文 orthographic\nAvoid: 改写\n  "
REQUEST_ID = "local-test-request"


def image_bytes(color, image_format):
    with BytesIO() as buffer:
        Image.new("RGB", (3, 3), color).save(buffer, format=image_format)
        return buffer.getvalue()


class GenerateImageTest(unittest.TestCase):
    def setUp(self):
        workspace = TemporaryDirectory()
        self.addCleanup(workspace.cleanup)
        self.workspace = Path(workspace.name).resolve()
        self.script = self.workspace / "scripts" / SCRIPT.name
        self.script.parent.mkdir()
        shutil.copyfile(SCRIPT, self.script)
        self.output = self.workspace / "output"
        self.reference_paths = [
            self.workspace / "第一张图.png",
            self.workspace / "second image.jpg",
        ]
        self.references = [image_bytes("red", "PNG"), image_bytes("blue", "JPEG")]
        for path, data in zip(self.reference_paths, self.references):
            path.write_bytes(data)
        self.jpeg = image_bytes("orange", "JPEG")
        self.encoded_image = base64.b64encode(self.jpeg).decode("ascii")
        self.requests = []
        self.scenario = "success"
        self.start_server()

    def start_server(self):
        test = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def respond(self, status, body, content_type):
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("x-request-id", REQUEST_ID)
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if self.path == "/mock/v1/result.jpg":
                    self.respond(200, test.jpeg, "application/octet-stream")
                else:
                    self.respond(404, b"missing image", "text/plain")

            def do_POST(self):
                raw = self.rfile.read(int(self.headers["Content-Length"]))
                content_type = self.headers["Content-Type"]
                if content_type.startswith("multipart/form-data"):
                    mime_header = f"MIME-Version: 1.0\r\nContent-Type: {content_type}\r\n\r\n"
                    multipart = BytesParser(policy=policy.default).parsebytes(mime_header.encode() + raw)
                    payload = {}
                    for part in multipart.iter_parts():
                        name = part.get_param("name", header="content-disposition")
                        payload.setdefault(name, []).append(part.get_payload(decode=True))
                else:
                    payload = json.loads(raw)
                test.requests.append((self.path, payload))
                status, result = test.provider_response(self.path)
                self.respond(status, json.dumps(result).encode(), "application/json")

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()

        self.addCleanup(thread.join)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        self.endpoint = f"http://127.0.0.1:{server.server_port}/mock"

    def provider_response(self, path):
        if "generateContent" in path:
            if self.scenario == "rejected":
                return 400, {"error": {"code": 400, "status": "INVALID_ARGUMENT", "message": "Mock Gemini error."}}
            return 200, {"candidates": [{"content": {"role": "model", "parts": [
                {"inlineData": {"data": self.encoded_image, "mimeType": "image/jpeg"}},
            ]}, "finishReason": "STOP"}]}
        if path.endswith(("/images/generations", "/images/edits")):
            if self.scenario == "rejected":
                return 400, {"error": {"message": "Mock provider rejected the prompt."}}
            if self.scenario == "empty":
                return 200, {"data": []}
            if self.scenario == "invalid_image":
                return 200, {"data": [{"b64_json": "aGVsbG8="}]}
            if self.scenario == "image_url":
                return 200, {"data": [{"url": "result.jpg"}]}
            if self.scenario == "missing_image_url":
                return 200, {"data": [{"url": "missing.jpg"}]}
            return 200, {"data": [{"b64_json": self.encoded_image}]}
        self.assertTrue(path.endswith("/services/aigc/multimodal-generation/generation"), path)
        if self.scenario == "rejected":
            return 400, {"request_id": REQUEST_ID, "code": "InvalidParameter", "message": "Mock Qwen error."}
        return 200, {"request_id": REQUEST_ID, "output": {"choices": [{"message": {
            "role": "assistant", "content": [{"image": self.endpoint + "/v1/result.jpg"}],
        }}]}, "usage": {}}

    def invoke(self, provider, *arguments, settings=None, prompt=PROMPT):
        env = {
            **os.environ,
            "PYTHONUTF8": "1",
            "NO_PROXY": "127.0.0.1",
            "no_proxy": "127.0.0.1",
            "IMAGE_PROVIDER": provider,
            "GEMINI_API_KEY": "test-key",
            "OPENAI_API_KEY": "test-key",
            "DASHSCOPE_API_KEY": "test-key",
            "GEMINI_BASE_URL": self.endpoint,
            "OPENAI_BASE_URL": self.endpoint + "/v1",
            "QWEN_BASE_URL": self.endpoint + "/v1",
            "GEMINI_GOOGLE_SEARCH": "false",
            "QWEN_PROMPT_EXTEND": "false",
            "GEMINI_MODEL": "",
            "OPENAI_MODEL": "",
            "QWEN_MODEL": "",
            **(settings or {}),
        }
        return subprocess.run(
            [sys.executable, str(self.script), "--output-dir", str(self.output),
             "--prompt", prompt, *arguments],
            cwd=self.workspace, env=env, capture_output=True, encoding="utf-8", timeout=30, check=False,
        )

    def final_log(self):
        lines = (self.output / "generation.log").read_text(encoding="utf-8").splitlines()
        return json.loads(lines[-1])

    def assert_image(self, process):
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(len(process.stdout.splitlines()), 1, process.stdout)
        path = Path(process.stdout.strip())
        self.assertEqual(path.parent, self.output)
        self.assertEqual(path.suffix, ".jpg")
        self.assertEqual(path.read_bytes(), self.jpeg)
        self.assertTrue(self.final_log()["ok"])
        self.assertEqual(self.final_log()["path"], str(path))
        self.assertFalse(list(self.output.glob(".generating_*")))

    def test_gemini(self):
        self.assert_image(self.invoke("gemini"))
        path, payload = self.requests[-1]
        self.assertIn("/mock/", path)
        self.assertIn("/models/gemini-3-pro-image-preview:generateContent", path)
        self.assertEqual(payload["contents"][0]["parts"], [{"text": PROMPT}])
        self.assertNotIn("imageConfig", payload["generationConfig"])
        self.assertNotIn("tools", payload)
        self.assertEqual(self.final_log()["request_id"], REQUEST_ID)

        self.assert_image(self.invoke(
            "gemini", "--aspect-ratio", "16:9", "--image-size", "2K",
            "--input-images", *map(str, self.reference_paths),
            "--model", "gemini-test-image", settings={"GEMINI_GOOGLE_SEARCH": "true"},
        ))
        path, payload = self.requests[-1]
        self.assertIn("/models/gemini-test-image:generateContent", path)
        self.assertIn("googleSearch", payload["tools"][0])
        self.assertEqual(payload["generationConfig"]["imageConfig"], {
            "aspectRatio": "16:9", "imageSize": "2K",
        })
        parts = payload["contents"][0]["parts"]
        self.assertEqual(parts[-1]["text"], PROMPT)
        blobs = [part["inlineData"] for part in parts[:-1]]
        self.assertEqual([blob.get("mimeType") or blob.get("mime_type") for blob in blobs], ["image/png", "image/jpeg"])
        self.assertEqual([base64.urlsafe_b64decode(blob["data"]) for blob in blobs], self.references)

    def test_gpt(self):
        self.assert_image(self.invoke("gpt"))
        path, payload = self.requests[-1]
        self.assertEqual(path, "/mock/v1/images/generations")
        self.assertEqual(payload, {"model": "gpt-image-2", "prompt": PROMPT})
        self.assertEqual(self.final_log()["request_id"], REQUEST_ID)

        self.scenario = "image_url"
        self.assert_image(self.invoke(
            "gpt", "--size", "1536X1024", "--quality", "high", "--input-images", *map(str, self.reference_paths),
        ))
        path, payload = self.requests[-1]
        self.assertEqual(path, "/mock/v1/images/edits")
        self.assertEqual(payload["prompt"], [PROMPT.encode()])
        self.assertEqual(payload["image[]"], self.references)
        self.assertEqual(payload["size"], [b"1536x1024"])
        self.assertEqual(payload["quality"], [b"high"])

    def test_qwen(self):
        self.assert_image(self.invoke("qwen"))
        path, payload = self.requests[-1]
        self.assertTrue(path.startswith("/mock/v1/"), path)
        self.assertEqual(payload["model"], "qwen-image-3.0")
        self.assertEqual(payload["input"]["messages"][0]["content"], [{"text": PROMPT}])
        self.assertIs(payload["parameters"]["prompt_extend"], False)
        self.assertNotIn("prompt_extend_mode", payload["parameters"])
        self.assertNotIn("size", payload["parameters"])
        self.assertEqual(self.final_log()["request_id"], REQUEST_ID)

        self.assert_image(self.invoke(
            "qwen", "--size", "1536x1024", "--negative-prompt", "  模糊\n",
            "--input-images", *map(str, self.reference_paths),
            settings={"QWEN_PROMPT_EXTEND": "true"},
        ))
        _, payload = self.requests[-1]
        self.assertEqual(payload["parameters"]["size"], "1536*1024")
        self.assertEqual(payload["parameters"]["negative_prompt"], "  模糊\n")
        self.assertIs(payload["parameters"]["prompt_extend"], True)
        self.assertEqual(payload["parameters"]["prompt_extend_mode"], "direct")
        content = payload["input"]["messages"][0]["content"]
        self.assertEqual(content[-1]["text"], PROMPT)
        self.assertEqual([item["image"].split(",", 1)[0] for item in content[:-1]], [
            "data:image/png;base64", "data:image/jpeg;base64",
        ])
        self.assertEqual(
            [base64.b64decode(item["image"].split(",", 1)[1]) for item in content[:-1]],
            self.references,
        )

    def test_api_and_image_errors_leave_no_image(self):
        scenarios = (("rejected", "api"), ("empty", "response"),
                     ("invalid_image", "image"), ("missing_image_url", "download"))
        for scenario, stage in scenarios:
            with self.subTest(scenario=scenario):
                self.scenario = scenario
                self.requests.clear()
                process = self.invoke("gpt")
                self.assertEqual(process.returncode, 1, process.stderr)
                self.assertEqual(process.stdout, "")
                self.assertIn(f"Error ({stage})", process.stderr)
                self.assertEqual(len(self.requests), 1)
                self.assertEqual(self.requests[0][1]["prompt"], PROMPT)
                log = self.final_log()
                self.assertEqual((log["stage"], log["provider"], log["model"]), (stage, "gpt", "gpt-image-2"))
                self.assertEqual(log["request_id"], REQUEST_ID)
                self.assertEqual([path.name for path in self.output.iterdir()], ["generation.log"])

    def test_gemini_and_qwen_report_api_errors(self):
        self.scenario = "rejected"
        for provider, message in (("gemini", "Mock Gemini error."), ("qwen", "Mock Qwen error.")):
            with self.subTest(provider=provider):
                process = self.invoke(provider)
                self.assertEqual(process.returncode, 1, process.stderr)
                self.assertEqual(process.stdout, "")
                self.assertIn(message, process.stderr)
                log = self.final_log()
                self.assertEqual((log["stage"], log["status_code"]), ("api", 400))
                self.assertEqual(log["request_id"], REQUEST_ID)
        self.assertEqual(len(self.requests), 2)
        self.assertEqual([path.name for path in self.output.iterdir()], ["generation.log"])

    def test_cli_and_reference_validation(self):
        help_process = subprocess.run(
            [sys.executable, "-S", str(self.script), "--help"],
            capture_output=True, text=True, check=False, timeout=10,
        )
        self.assertEqual(help_process.returncode, 0, help_process.stderr)
        self.assertIn("--prompt ", help_process.stdout)
        self.assertNotIn("--prompt-json", help_process.stdout)
        self.assertEqual(self.invoke("gpt", prompt="  \n").returncode, 2)
        self.assertEqual(self.invoke("gpt", "--prompt-json", "{}").returncode, 2)

        invalid = self.invoke("gpt", "--input-images", str(self.reference_paths[0]), "missing.png")
        self.assertEqual(invalid.returncode, 1)
        self.assertIn("Cannot read reference image", invalid.stderr)
        (self.workspace / "broken.png").write_bytes(b"not an image")
        corrupt = self.invoke("gemini", "--input-images", "broken.png")
        self.assertEqual(corrupt.returncode, 1)
        self.assertIn("Cannot read reference image", corrupt.stderr)
        for provider, limit in (("qwen", 3), ("gemini", 14), ("gpt", 16)):
            with self.subTest(provider=provider):
                paths = [str(self.reference_paths[0])] * (limit + 1)
                too_many = self.invoke(provider, "--input-images", *paths)
                self.assertEqual(too_many.returncode, 1)
                self.assertIn(f"at most {limit}", too_many.stderr)
        self.assertEqual(self.requests, [])

    def test_dotenv_configuration_and_model_override(self):
        (self.workspace / ".env").write_text("IMAGE_PROVIDER=gpt\nOPENAI_MODEL=gpt-image-from-env\n", encoding="utf-8")
        self.assert_image(self.invoke("qwen", settings={"OPENAI_MODEL": "gpt-image-from-system"}))
        self.assertEqual(self.requests[-1][1]["model"], "gpt-image-from-env")
        self.assert_image(self.invoke("qwen", "--model", "gpt-image-from-cli"))
        self.assertEqual(self.requests[-1][1]["model"], "gpt-image-from-cli")

    def test_only_selected_sdk_is_required(self):
        hidden_sdk = self.script.with_name("openai.py")
        hidden_sdk.write_text("raise ImportError('OpenAI unavailable in this test')\n", encoding="utf-8")
        invalid = self.invoke("gpt")
        self.assertEqual(invalid.returncode, 1)
        self.assertIn("pip install -U openai", invalid.stderr)
        self.assertEqual(self.requests, [])
        self.assert_image(self.invoke("qwen"))


if __name__ == "__main__":
    unittest.main()
