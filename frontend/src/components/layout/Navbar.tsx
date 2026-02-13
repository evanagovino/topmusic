import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'

const links = [
  { to: '/top-albums', label: 'Top Albums' },
  { to: '/radio', label: 'Radio' },
  { to: '/now-playing', label: 'Now Playing' },
  { to: '/about', label: 'About' },
]

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false)
  const isAuthorized = useAuthStore((s) => s.isAuthorized)
  const isConfiguring = useAuthStore((s) => s.isConfiguring)
  const authorize = useAuthStore((s) => s.authorize)
  const unauthorize = useAuthStore((s) => s.unauthorize)

  return (
    <nav className="border-b border-gray-800 bg-gray-900 px-4 py-3 md:px-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">TopMusic</h1>

        {/* Desktop nav links */}
        <div className="hidden md:flex md:items-center md:gap-6">
          <div className="flex gap-1">
            {links.map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                className={({ isActive }) =>
                  `rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-indigo-600 text-white'
                      : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
                  }`
                }
              >
                {l.label}
              </NavLink>
            ))}
          </div>
        </div>

        {/* Desktop auth */}
        <div className="hidden md:flex md:items-center md:gap-3 md:text-sm">
          {isAuthorized ? (
            <>
              <span className="text-green-400">Connected to Apple Music</span>
              <button
                type="button"
                onClick={unauthorize}
                className="text-gray-400 hover:text-gray-200"
              >
                Disconnect
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={authorize}
              disabled={isConfiguring}
              className="rounded-lg bg-pink-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-pink-500 disabled:opacity-50"
            >
              {isConfiguring ? 'Loading...' : 'Connect Apple Music'}
            </button>
          )}
        </div>

        {/* Hamburger button — mobile only */}
        <button
          type="button"
          onClick={() => setMenuOpen(!menuOpen)}
          className="rounded p-2 text-gray-400 hover:bg-gray-800 hover:text-white md:hidden"
          aria-label="Toggle menu"
        >
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            {menuOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </div>

      {/* Mobile dropdown */}
      {menuOpen && (
        <div className="mt-2 flex flex-col gap-2 border-t border-gray-800 pt-3 md:hidden">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              onClick={() => setMenuOpen(false)}
              className={({ isActive }) =>
                `rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-indigo-600 text-white'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
                }`
              }
            >
              {l.label}
            </NavLink>
          ))}
          <div className="flex items-center gap-3 border-t border-gray-800 pt-2 text-sm">
            {isAuthorized ? (
              <>
                <span className="text-green-400">Connected to Apple Music</span>
                <button
                  type="button"
                  onClick={unauthorize}
                  className="text-gray-400 hover:text-gray-200"
                >
                  Disconnect
                </button>
              </>
            ) : (
              <button
                type="button"
                onClick={authorize}
                disabled={isConfiguring}
                className="rounded-lg bg-pink-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-pink-500 disabled:opacity-50"
              >
                {isConfiguring ? 'Loading...' : 'Connect Apple Music'}
              </button>
            )}
          </div>
        </div>
      )}
    </nav>
  )
}
