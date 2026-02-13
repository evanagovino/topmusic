import { lazy, Suspense, useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import AppLayout from './components/layout/AppLayout'
import LoadingSpinner from './components/ui/LoadingSpinner'
import { useAuthStore } from './store/authStore'
import { usePlayerStore } from './store/playerStore'

const AboutPage = lazy(() => import('./pages/AboutPage'))
const TopAlbumsPage = lazy(() => import('./pages/TopAlbumsPage'))
const RadioPage = lazy(() => import('./pages/RadioPage'))
const NowPlayingPage = lazy(() => import('./pages/NowPlayingPage'))


export default function App() {
  const initialize = useAuthStore((s) => s.initialize)
  const bindEvents = usePlayerStore((s) => s.bindEvents)
  const unbindEvents = usePlayerStore((s) => s.unbindEvents)

  useEffect(() => {
    initialize().then(() => {
      bindEvents()
    })
    return () => {
      unbindEvents()
    }
  }, [initialize, bindEvents, unbindEvents])

  return (
    <AppLayout>
      <Suspense fallback={<LoadingSpinner />}>
        <Routes>
          <Route path="/" element={<Navigate to="/top-albums" replace />} />
          <Route path="/top-albums" element={<TopAlbumsPage />} />
          <Route path="/radio" element={<RadioPage />} />
          <Route path="/now-playing" element={<NowPlayingPage />} />
          <Route path="/about" element={<AboutPage />} />
        </Routes>
      </Suspense>
    </AppLayout>
  )
}
