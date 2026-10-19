import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { ToastProvider } from './context/ToastContext'
import { AlarmsPage } from './pages/AlarmsPage'
import { MachineDetailPage } from './pages/MachineDetailPage'
import { MachinesPage } from './pages/MachinesPage'
import { OverviewPage } from './pages/OverviewPage'
import { ProductionPage } from './pages/ProductionPage'
import { ReportsPage } from './pages/ReportsPage'
import { SettingsPage } from './pages/SettingsPage'

export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<OverviewPage />} />
            <Route path="/machines" element={<MachinesPage />} />
            <Route path="/machines/:machineId" element={<MachineDetailPage />} />
            <Route path="/alarms" element={<AlarmsPage />} />
            <Route path="/production" element={<ProductionPage />} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<p className="text-slate-300">That page does not exist.</p>} />
          </Route>
        </Routes>
      </ToastProvider>
    </BrowserRouter>
  )
}
