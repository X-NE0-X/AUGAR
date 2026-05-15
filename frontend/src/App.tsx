import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { ToastProvider } from './components/Toast'
import { Layout } from './components/Layout'
import { ConfigProvider } from './context/ConfigContext'
import Ask from './views/Ask'
import ReadingsIndex from './views/ReadingsIndex'
import ReadingOverview from './views/ReadingOverview'
import EngineDetail from './views/EngineDetail'
import Almanac from './views/Almanac'

function App() {
  return (
    <ConfigProvider>
      <ToastProvider>
        <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <Layout>
            <Routes>
              <Route path="/" element={<Ask />} />
              <Route path="/readings" element={<ReadingsIndex />} />
              <Route path="/readings/:period/:ticker" element={<ReadingOverview />} />
              <Route path="/readings/:period/:ticker/:engine" element={<EngineDetail />} />
              <Route path="/almanac" element={<Almanac />} />
            </Routes>
          </Layout>
        </Router>
      </ToastProvider>
    </ConfigProvider>
  )
}

export default App
