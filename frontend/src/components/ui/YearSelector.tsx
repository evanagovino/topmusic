import { yearRange } from '../../utils/helpers'

interface YearSelectorProps {
  label: string
  value: number
  onChange: (y: number) => void
  reverse?: boolean
}

const years = yearRange()

export default function YearSelector({ label, value, onChange, reverse }: YearSelectorProps) {
  const opts = reverse ? [...years].reverse() : years
  return (
    <div>
      <label className="mb-1 block text-sm font-medium text-gray-300">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-base text-gray-200 outline-none focus:border-indigo-500 sm:text-sm"
      >
        {opts.map((y) => (
          <option key={y} value={y}>
            {y}
          </option>
        ))}
      </select>
    </div>
  )
}
