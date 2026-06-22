# 🧠 AI Learning Hub

A structured, hands-on learning platform covering the full modern AI stack — built with **React + Vite** and ready to deploy to **Vercel**.

## The 7-module learning path

| # | Module | Status | Capstone project |
|---|--------|--------|------------------|
| 1 | 🐍 Python for AI | ✅ Full | CSV Data-Quality CLI |
| 2 | 📈 Machine Learning | ✅ Full | Customer Churn Prediction Service (FastAPI + Docker) |
| 3 | 🧠 Deep Learning | 🚧 Scaffolded | Image Classifier + Web Demo |
| 4 | ✨ Generative AI | ✅ Full | "Chat With Your Docs" RAG Assistant |
| 5 | 🤖 AI Agents | 🚧 Scaffolded | Research & Reporting Agent |
| 6 | 🕸️ Agentic AI | 🚧 Scaffolded | Autonomous Content Studio |
| 7 | ☁️ Cloud Platforms | 🚧 Scaffolded | Deploy the full stack (AWS/Azure/GCP) |

Each **Full** module has 5 lessons + 1 production project written in a "read the concept, then build the real thing" format. Scaffolded modules ship with a complete curriculum outline and project brief.

## Run locally

```bash
cd ai-learning-hub
npm install
npm run dev          # http://localhost:5173
```

## Build & preview

```bash
npm run build        # outputs to dist/
npm run preview
```

## Deploy to Vercel

```bash
npm i -g vercel
vercel               # follow prompts, framework auto-detected as Vite
```

`vercel.json` already rewrites all routes to `index.html` so client-side routing works on refresh.

## Project structure

```
src/
├── data/            # the curriculum — one file per module
│   ├── python.js  ml.js  genai.js     (full)
│   ├── outlines.js                    (scaffolded modules)
│   └── index.js                       (registry + stats)
├── components/      # Sidebar, Markdown renderer
├── pages/           # Home, Module
├── App.jsx          # router
└── styles.css       # design system
```

## Adding / promoting a module

1. Open the module file in `src/data/` (or add a new one).
2. Add lesson objects: `{ id, tag, title, body }` where `body` is Markdown.
3. Mark a lesson as a project with `project: true` and a `stack: [...]` array.
4. Register it in `src/data/index.js`.

That's it — the UI, navigation, and stats update automatically.
