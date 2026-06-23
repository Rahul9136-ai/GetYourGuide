import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { moduleById } from '../data/index.js'
import generatedVideos from '../data/generatedVideos.js'
import Markdown from '../components/Markdown.jsx'
import VideoEmbed from '../components/VideoEmbed.jsx'

export default function Module() {
  const { id } = useParams()
  const nav = useNavigate()
  const mod = moduleById[id]
  const [active, setActive] = useState(0)

  // Reset to first lesson whenever the module changes.
  useEffect(() => {
    setActive(0)
    window.scrollTo(0, 0)
  }, [id])

  if (!mod) {
    return (
      <div className="content">
        <h1>Module not found</h1>
        <button className="btn" onClick={() => nav('/')}>← Back home</button>
      </div>
    )
  }

  const lesson = mod.lessons[active]
  // Prefer a generated AI clip if one exists for this lesson; else the curated video.
  const genSrc = generatedVideos[`${mod.id}/${lesson.id}`]
  const videoToShow = genSrc
    ? { src: genSrc, title: `${lesson.title} — intro`, author: 'AI-generated' }
    : lesson.video
  const goTo = (i) => {
    setActive(i)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <>
      <div className="topbar">
        <div className="crumbs">
          <span style={{ cursor: 'pointer' }} onClick={() => nav('/')}>Home</span>
          {' · '}
          <b>{mod.title}</b>
        </div>
        <div className="spacer" />
        <span className="pill">{mod.status === 'ready' ? 'Full module' : 'Scaffolded'}</span>
      </div>

      <div className="content">
        <div className="mod-head">
          <div className="mico">{mod.icon}</div>
          <div>
            <h1>{mod.title}</h1>
            <p>{mod.tagline}</p>
          </div>
        </div>

        <div className="layout-2">
          <nav className="lesson-list">
            <div className="ll-title">{mod.lessons.length} sections</div>
            {mod.lessons.map((l, i) => (
              <div
                key={l.id}
                className={`ll-item ${i === active ? 'active' : ''} ${l.project ? 'project' : ''}`}
                onClick={() => goTo(i)}
              >
                <span className="num">{l.project ? '★' : i + 1}</span>
                <span>{l.title}</span>
              </div>
            ))}
          </nav>

          <article className="lesson">
            <span className="tag">{lesson.tag}</span>

            {lesson.project && lesson.stack && (
              <div className="proj-banner">
                <div className="tag">🚀 Production Project</div>
                <div className="stack">
                  {lesson.stack.map((s) => (
                    <span key={s} className="chip">{s}</span>
                  ))}
                </div>
              </div>
            )}

            {videoToShow && <VideoEmbed video={videoToShow} />}

            <Markdown>{lesson.body}</Markdown>

            <div className="lesson-foot">
              <button
                className="btn"
                disabled={active === 0}
                style={{ opacity: active === 0 ? 0.4 : 1 }}
                onClick={() => active > 0 && goTo(active - 1)}
              >
                ← Previous
              </button>
              {active < mod.lessons.length - 1 ? (
                <button className="btn primary" onClick={() => goTo(active + 1)}>
                  Next: {mod.lessons[active + 1].title} →
                </button>
              ) : (
                <button className="btn primary" onClick={() => nav('/')}>
                  Finish module ✓
                </button>
              )}
            </div>
          </article>
        </div>

        <div className="foot">
          © {new Date().getFullYear()} Purvi Technologies · {mod.title} · AI Learning Hub
        </div>
      </div>
    </>
  )
}
