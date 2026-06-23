import { useNavigate, useLocation } from 'react-router-dom'
import { modules } from '../data/index.js'

export default function Sidebar() {
  const nav = useNavigate()
  const { pathname } = useLocation()

  return (
    <aside className="sidebar">
      <div className="brand" onClick={() => nav('/')} style={{ cursor: 'pointer' }}>
        <img src="/purvi-mark.svg" alt="Purvi Technologies logo" />
        <div>
          <b className="brand-name">Purvi Technologies</b>
          <span>AI Learning Hub</span>
        </div>
      </div>

      <div
        className={`nav-item ${pathname === '/' ? 'active' : ''}`}
        onClick={() => nav('/')}
      >
        <span className="ico">🏠</span> Home
      </div>

      <div className="nav-section">Learning Path</div>
      {modules.map((m, i) => (
        <div
          key={m.id}
          className={`nav-item ${pathname.startsWith(`/m/${m.id}`) ? 'active' : ''}`}
          onClick={() => nav(`/m/${m.id}`)}
        >
          <span className="ico">{m.icon}</span>
          <span style={{ flex: 1 }}>{m.title}</span>
          <span className="lvl">{m.status === 'ready' ? `0${i + 1}` : '··'}</span>
        </div>
      ))}
    </aside>
  )
}
