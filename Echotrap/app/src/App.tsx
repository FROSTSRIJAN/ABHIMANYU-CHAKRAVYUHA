import { Routes, Route } from 'react-router'
import { Navbar } from '@/components/Navbar'
import { Footer } from '@/components/Footer'
import Home from './pages/Home'
import Analyzer from './pages/Analyzer'
import Processing from './pages/Processing'
import Results from './pages/Results'
import Safety from './pages/Safety'
import Diagnostics from './pages/Diagnostics'
import Docs from './pages/Docs'
import NotFound from './pages/NotFound'

export default function App() {
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/analyze" element={<Analyzer />} />
          <Route path="/processing" element={<Processing />} />
          <Route path="/results" element={<Results />} />
          <Route path="/results/:id" element={<Results />} />
          <Route path="/safety" element={<Safety />} />
          <Route path="/diagnostics" element={<Diagnostics />} />
          <Route path="/docs" element={<Docs />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <Footer />
    </div>
  )
}
