import { getMoodColor } from '../../utils/moodColors'

interface MoodBadgeProps {
  mood: string
}

export default function MoodBadge({ mood }: MoodBadgeProps) {
  return (
    <span
      className={`${getMoodColor(mood)} inline-block rounded-full px-2.5 py-0.5 text-xs font-medium text-white`}
    >
      {mood}
    </span>
  )
}
