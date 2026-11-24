# Image Generator Skill

简体中文 | [English](README.md)

使用最终提示词和可选的本地参考图生成或编辑图片。脚本将提示词原样交给所选服务商的官方 SDK。最终文本也可以由其他项目或 Skill 提供。

## 安装

使用 Python 3.11 或更高版本。安装 Pillow 和 python-dotenv，再执行所选服务商对应的 SDK 安装命令。

```bash
python -m pip install -U Pillow python-dotenv
python -m pip install -U google-genai  # Gemini
python -m pip install -U openai       # GPT
python -m pip install -U dashscope    # Qwen
```

可将此目录复制到 Agent 的技能目录，也可以直接运行脚本。将 [`.env.example`](.env.example) 复制为与 [SKILL.md](SKILL.md) 同级的 `.env`，填写服务商配置。`.env` 的值优先于系统环境变量。

| `IMAGE_PROVIDER` | API Key | 可选端点和模型变量 | 默认模型 |
|---|---|---|---|
| `gemini`（默认） | `GEMINI_API_KEY` | `GEMINI_BASE_URL`、`GEMINI_MODEL` | `gemini-3-pro-image-preview` |
| `gpt` | `OPENAI_API_KEY` | `OPENAI_BASE_URL`、`OPENAI_MODEL` | `gpt-image-2` |
| `qwen` | `DASHSCOPE_API_KEY` | `QWEN_BASE_URL`、`QWEN_MODEL` | `qwen-image-3.0` |

自定义端点须兼容所选 SDK 的 API。OpenAI 兼容端点通常以 `/v1` 结尾。DashScope 的端点与密钥须属于同一区域。环境变量模板中有区域端点示例。

## 生成图片

以下示例从仓库根目录运行。安装为技能后，可在工作目录中通过脚本的绝对路径调用。

```bash
python scripts/generate_image.py --prompt '雪地里的一间小木屋'

python scripts/generate_image.py \
  --prompt '将第一张图中的主体放到第二张图的背景里。' \
  --input-images ./subject.png ./background.jpg \
  --output-dir ./images
```

`--model` 可覆盖配置中的模型。参考图按传入顺序提交。默认模型的参考图上限分别为 Gemini 14 张、GPT 16 张和 Qwen 3 张。

### 服务商选项

| 服务商 | 命令行参数 | 服务端配置 |
|---|---|---|
| Gemini | `--aspect-ratio 16:9`、`--image-size 2K` | `GEMINI_GOOGLE_SEARCH=true` 为支持的模型启用搜索。 |
| GPT | `--size 1536x1024`、`--quality auto\|low\|medium\|high` | |
| Qwen | `--size 1536x1024`、`--negative-prompt '运动模糊'` | `QWEN_PROMPT_EXTEND=true` 启用 DashScope 服务端改写。 |

两项服务端开关均默认为关闭。支持的尺寸与生成参数取决于所选模型。省略时采用服务商默认值。

## 输出与错误

成功时脚本在标准输出打印一张生成图片的绝对路径，退出码为 0。默认输出目录为当前工作目录下的 `./generation-image`，扩展名与图片的实际格式一致。

失败时脚本返回非零退出码，并在标准错误输出中报告错误。可在 `<output-dir>/generation.log` 中查看实际服务商、模型、失败阶段，以及服务商提供的请求 ID。

## 测试

安装三家 SDK 后运行 `python -m unittest discover -s tests -v`。测试使用本地服务和测试密钥。

## 许可证

MIT
