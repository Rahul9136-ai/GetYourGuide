# 🎬 Generate your own AI videos

Generate short, cinematic **intro clips** for each module using a text-to-video model
(Google **Veo**, OpenAI **Sora**, or **Runway**), then the app plays them automatically.

> **What this is good for:** stylish 5–10s intro "bumpers" at the top of a lesson.
> **What it is *not*:** full, technically-accurate explainer videos — today's text-to-video
> models can't reliably render correct code, math, or labelled diagrams. For the teaching
> itself, the curated YouTube videos and the in-lesson diagrams do the heavy lifting; the
> generated clip is the eye-catching opener.

## 1. Pick a provider & get an API key

| Provider | Env var | Install | Notes |
|----------|---------|---------|-------|
| **Veo** (default) | `GEMINI_API_KEY` | `pip install google-genai` | Google AI Studio key. ~$0.40–0.75 / sec. Includes audio. |
| **Sora** | `OPENAI_API_KEY` | `pip install openai` | OpenAI Videos API. Priced per second. |
| **Runway** | `RUNWAYML_API_SECRET` | `pip install runwayml requests` | Runway dev portal → Settings → API. 2–10s clips. |

These are **paid** APIs billed to *your* account. Generate a couple of clips first to gauge cost.

## 2. Install

```bash
cd ai-learning-hub/video-gen
pip install -r requirements.txt        # or just the one line for your provider
```

## 3. Set your key

```bash
# Windows (PowerShell)
$env:GEMINI_API_KEY = "your-key"
# macOS / Linux
export GEMINI_API_KEY="your-key"
```

## 4. Generate

```bash
# all modules, with Veo (default)
python generate.py

# just two lessons, to test cost first
python generate.py --provider veo --only dl/what --only genai/llms

# use a different provider
python generate.py --provider sora   --only python/intro
python generate.py --provider runway --only cloud/basics
```

Each clip is saved to `../public/videos/<moduleId>-<lessonId>.mp4`, and the script
rewrites `../src/data/generatedVideos.js`. That's it — no manual wiring.

## 5. See them

```bash
cd ..
npm run dev
```

Open a module whose clip you generated: the AI video appears at the top of the lesson,
labelled **✨ AI-generated**, and replaces the curated YouTube video for that lesson.
Lessons without a generated clip keep their YouTube video.

## Customise

- **Prompts** live in [`prompts.json`](./prompts.json) — edit the text, aspect ratio, or add
  new keys (`"<moduleId>/<lessonId>"`) for any lesson you want a clip for.
- **Model / size** are flags: `--veo-model`, `--sora-size`, `--runway-ratio`, `--duration`, etc.
  Run `python generate.py --help`.

## Notes

- Generated `.mp4` files are **gitignored** (they're large) — regenerate them anywhere with this tool.
- For Vercel: either commit the clips (remove the gitignore line) or host them on a CDN /
  object storage and point the manifest at those URLs.
- The Veo path is the reference implementation. The Sora and Runway SDKs evolve quickly —
  if a field name has changed, check the provider's current docs and adjust the matching
  function in `generate.py`.
