import type { Accolade } from '../../api/types'

interface AccoladesPanelProps {
  accolades?: Accolade[]
}

export default function AccoladesPanel({ accolades }: AccoladesPanelProps) {
  if (!accolades || accolades.length === 0) {
    return <p className="text-sm text-gray-500">No accolades found</p>
  }
  return (
    <ul className="space-y-1 text-sm text-gray-300">
      {accolades.map((a, i) => (
        <li key={i}>
          {a.publication} ({a.list}): {a.rank}
        </li>
      ))}
    </ul>
  )
}
