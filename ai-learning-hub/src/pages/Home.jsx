import { useNavigate } from 'react-router-dom'
import { modules, stats } from '../data/index.js'

export default function Home() {
  const nav = useNavigate()

  return (
    <>
      <div className="topbar">
        <div className="crumbs">
          <b>Home</b> · Your AI learning path
        </div>
        <div className="spacer" />
        <span className="pill">{stats.ready} of {stats.modules} modules ready</span>
      </div>

      <div className="content">
        <section className="hero">
          <div className="hero-badge">
            <img src="/purvi-mark.svg" alt="Purvi Technologies" />
            by <b>Purvi Technologies</b>
          </div>
          <h1>
            Master AI, end to end.<br />
            From <span className="grad">Python</span> to <span className="grad">Agentic AI</span> & the Cloud.
          </h1>
          <p>
            One structured path through every layer of modern AI — Python foundations, classical
            machine learning, deep learning, generative AI, autonomous agents, multi-agent systems,
            and cloud deployment. Every module ends with a <strong>real production project</strong> you can ship.
          </p>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 28 }}>
            <button className="btn primary" onClick={() => nav('/m/python')}>
              Start with Python →
            </button>
            <button className="btn" onClick={() => nav('/m/genai')}>
              Jump to Generative AI ✨
            </button>
          </div>
          <div className="hero-stats">
            <div className="s"><b>{stats.modules}</b><span>MODULES</span></div>
            <div className="s"><b>{stats.lessons}</b><span>LESSONS</span></div>
            <div className="s"><b>{stats.projects}</b><span>PRODUCTION PROJECTS</span></div>
            <div className="s"><b>∞</b><span>HANDS-ON CODE</span></div>
          </div>
        </section>

        <h2 className="section-title">The 7-Module Path</h2>
        <p className="section-sub">
          Built to be followed in order — each module assumes the one before it and feeds the one after.
        </p>

        <div className="grid">
          {modules.map((m) => {
            const lessons = m.lessons.length
            const ready = m.status === 'ready'
            return (
              <div key={m.id} className="card" onClick={() => nav(`/m/${m.id}`)}>
                <span className={`badge ${ready ? 'ready' : 'soon'}`}>
                  {ready ? 'Ready' : 'Scaffolded'}
                </span>
                <div className="mico" style={{ boxShadow: `inset 0 0 0 1px ${m.color}40` }}>
                  {m.icon}
                </div>
                <h3>{m.title}</h3>
                <p>{m.tagline}</p>
                <div className="meta">
                  <span>📦 {m.level}</span>
                  <span>📖 {lessons} {lessons === 1 ? 'section' : 'lessons'}</span>
                </div>
                <div className="bar">
                  <i style={{ width: ready ? '100%' : '15%' }} />
                </div>
              </div>
            )
          })}
        </div>

        <h2 className="section-title">Why this hub is different</h2>
        <p className="section-sub">Not just theory — every track is engineered to produce a portfolio.</p>
        <div className="grid">
          <div className="card" style={{ cursor: 'default' }}>
            <div className="mico">🛠️</div>
            <h3>Production projects, not toy demos</h3>
            <p>A churn API, a RAG assistant, a data-quality CLI — each is deployable and resume-ready.</p>
          </div>
          <div className="card" style={{ cursor: 'default' }}>
            <div className="mico">🔗</div>
            <h3>Everything connects</h3>
            <p>The ML model you train gets served as an API, then deployed in the Cloud module. One system, many skills.</p>
          </div>
          <div className="card" style={{ cursor: 'default' }}>
            <div className="mico">🚀</div>
            <h3>Built to deploy</h3>
            <p>This very app is a React + Vite build that ships to Vercel — a working example of what you'll create.</p>
          </div>
        </div>

        <div className="foot">
          © {new Date().getFullYear()} Purvi Technologies · AI Learning Hub · Built with React + Vite
        </div>
      </div>
    </>
  )
}
