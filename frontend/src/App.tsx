import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import ProjectView from './pages/ProjectView'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-background font-sans text-foreground">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/project/:id" element={<ProjectView />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
