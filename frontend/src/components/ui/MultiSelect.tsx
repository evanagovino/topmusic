import { useState, useRef, useEffect } from 'react'

interface MultiSelectProps {
  label: string
  options: string[]
  selected: string[]
  onChange: (selected: string[]) => void
  disabled?: boolean
}

export default function MultiSelect({
  label,
  options,
  selected,
  onChange,
  disabled,
}: MultiSelectProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [search, setSearch] = useState('')
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const filtered = options.filter((o) =>
    o.toLowerCase().includes(search.toLowerCase()),
  )

  function toggle(item: string) {
    if (selected.includes(item)) {
      onChange(selected.filter((s) => s !== item))
    } else {
      onChange([...selected, item])
    }
  }

  return (
    <div ref={ref} className="relative">
      <label className="mb-1 block text-sm font-medium text-gray-300">{label}</label>
      <button
        type="button"
        disabled={disabled}
        onClick={() => setIsOpen(!isOpen)}
        className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-left text-base text-gray-200 hover:border-gray-500 disabled:opacity-50 sm:text-sm"
      >
        {selected.length === 0 ? (
          <span className="text-gray-500">All</span>
        ) : (
          <span>{selected.join(', ')}</span>
        )}
      </button>
      {isOpen && (
        <div className="absolute z-50 mt-1 max-h-60 w-full overflow-auto rounded-lg border border-gray-700 bg-gray-800 shadow-xl">
          <div className="sticky top-0 bg-gray-800 p-2">
            <input
              type="text"
              placeholder="Search..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full rounded border border-gray-600 bg-gray-900 px-2 py-1 text-base text-gray-200 outline-none focus:border-indigo-500 sm:text-sm"
            />
          </div>
          {selected.length > 0 && (
            <button
              type="button"
              onClick={() => onChange([])}
              className="w-full px-3 py-1.5 text-left text-xs text-indigo-400 hover:bg-gray-700"
            >
              Clear all
            </button>
          )}
          {filtered.map((opt) => (
            <label
              key={opt}
              className="flex cursor-pointer items-center gap-2 px-3 py-2 text-base hover:bg-gray-700 sm:py-1.5 sm:text-sm"
            >
              <input
                type="checkbox"
                checked={selected.includes(opt)}
                onChange={() => toggle(opt)}
                className="rounded border-gray-600 bg-gray-900 text-indigo-500 focus:ring-indigo-500"
              />
              <span className="text-gray-200">{opt}</span>
            </label>
          ))}
          {filtered.length === 0 && (
            <p className="px-3 py-2 text-sm text-gray-500">No results</p>
          )}
        </div>
      )}
    </div>
  )
}
