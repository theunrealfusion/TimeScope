
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Forecast from './pages/Forecast'
import Layout from './components/Layout'

const queryClient = new QueryClient()

const DashboardPlaceholder = () => (
  <div className="p-8">
    <h2 className="text-2xl font-bold mb-4">Dashboard</h2>
    <p className="text-gray-600">Overview metrics, system health, and recent backtests will appear here.</p>
  </div>
)

const SettingsPlaceholder = () => (
  <div className="p-8">
    <h2 className="text-2xl font-bold mb-4">Settings</h2>
    <p className="text-gray-600">Model configurations, database paths, and API keys will be managed here.</p>
  </div>
)

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Navigate to="/forecast" replace />} />
            <Route path="/forecast" element={<Forecast />} />
            <Route path="/dashboard" element={<DashboardPlaceholder />} />
            <Route path="/settings" element={<SettingsPlaceholder />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
