import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar.jsx'
import Home from './pages/Home.jsx'
import Module from './pages/Module.jsx'

export default function App() {
  return (
    <div className="app">
      <Sidebar />
      <main className="main">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/m/:id" element={<Module />} />
          <Route path="*" element={<Home />} />
        </Routes>
      </main>
    </div>
  )
}
