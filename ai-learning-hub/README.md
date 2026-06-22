# 🧠 AI Learning Hub

A structured, hands-on learning platform covering the full modern AI stack — built with **React + Vite** and ready to deploy to **Vercel**.

## The 7-module learning path

| # | Module | Status | Capstone project |
|---|--------|--------|------------------|
| 1 | 🐍 Python for AI | ✅ Full | CSV Data-Quality CLI |
| 2 | 📈 Machine Learning | ✅ Full | Customer Churn Prediction Service (FastAPI + Docker) |
| 3 | 🧠 Deep Learning | ✅ Full | Image Classifier + Web Demo |
| 4 | ✨ Generative AI | ✅ Full | "Chat With Your Docs" RAG Assistant |
| 5 | 🤖 AI Agents | ✅ Full | Research & Reporting Agent |
| 6 | 🕸️ Agentic AI | ✅ Full | Autonomous Content Studio |
| 7 | ☁️ Cloud Platforms | ✅ Full | Deploy the full stack (AWS/Azure/GCP) |

All 7 modules are complete: **42 lessons + 7 production projects**. Each lesson is written theory-first — a plain-English **"In plain English"** explanation with analogies before any code — then a buildable production project. The later projects deliberately reuse earlier ones (the ML churn API and GenAI RAG app get containerized and deployed in the Cloud module).

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
│   ├── python.js  ml.js  dl.js  genai.js
│   ├── agents.js  agentic.js  cloud.js
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
