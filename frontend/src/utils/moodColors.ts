const moodColorMap: Record<string, string> = {
  Frenetic: 'bg-red-600',
  Weird: 'bg-red-500',
  Gritty: 'bg-gray-500',
  Cathartic: 'bg-blue-600',
  Wistful: 'bg-blue-400',
  Sultry: 'bg-violet-600',
  Intimate: 'bg-violet-400',
  Groovy: 'bg-green-600',
  Upbeat: 'bg-green-400',
  Visceral: 'bg-yellow-500',
  Lush: 'bg-orange-500',
  Sprawling: 'bg-orange-400',
  Ethereal: 'bg-orange-300',
}

export function getMoodColor(mood: string): string {
  return moodColorMap[mood] ?? 'bg-gray-600'
}
