import type { ReactNode } from 'react'
import Navbar from './Navbar'
import PlayerBar from '../ui/PlayerBar'
import { usePlayerStore } from '../../store/playerStore'

interface AppLayoutProps {
  children: ReactNode
}

export default function AppLayout({ children }: AppLayoutProps) {
  const isPlayerVisible = usePlayerStore((s) => s.isPlayerVisible)

  return (
    <div className="flex h-screen flex-col bg-gray-950 text-gray-100">
      <Navbar />
      <main className={`flex-1 overflow-y-auto ${isPlayerVisible ? 'pb-16' : ''}`}>
        {children}
      </main>
      {isPlayerVisible && <PlayerBar />}
    </div>
  )
}
