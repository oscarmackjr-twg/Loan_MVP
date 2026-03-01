import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Runs from './pages/Runs'
import RunDetail from './pages/RunDetail'
import Exceptions from './pages/Exceptions'
import RejectedLoans from './pages/RejectedLoans'
import FileManager from './pages/FileManager'
import ProgramRuns from './pages/ProgramRuns'
import HolidayMaintenance from './pages/HolidayMaintenance'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="runs" element={<Runs />} />
          <Route path="runs/:runId" element={<RunDetail />} />
          <Route path="exceptions" element={<Exceptions />} />
          <Route path="rejected-loans" element={<RejectedLoans />} />
          <Route path="files" element={<FileManager />} />
          <Route path="program-runs" element={<ProgramRuns />} />
          <Route path="holidays" element={<HolidayMaintenance />} />
        </Route>
      </Routes>
    </AuthProvider>
  )
}

export default App
