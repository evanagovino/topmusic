import { type ReactNode, useState } from 'react'

interface SidebarProps {
  children: ReactNode
  label?: string
}

export default function Sidebar({ children, label = 'Filters' }: SidebarProps) {
  const [open, setOpen] = useState(true)

  return (
    <div className="border-b border-gray-800 bg-gray-900">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-4 py-3 text-sm font-medium text-gray-300 hover:text-white md:px-6"
      >
        <span>{label}</span>
        <svg
          className={`h-4 w-4 transition-transform ${open ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && (
        <div className="px-4 pb-4 md:px-6">
          <div className="grid grid-cols-[repeat(auto-fit,minmax(8rem,1fr))] gap-3 sm:grid-cols-[repeat(auto-fit,minmax(10rem,1fr))] sm:gap-4">{children}</div>
        </div>
      )}
    </div>
  )
}
