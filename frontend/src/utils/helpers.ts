export function sortList(items: string[]): string[] {
  return [...items].sort((a, b) => a.localeCompare(b))
}

export function normalizeWeights(weights: number[]): number[] {
  const sum = weights.reduce((a, b) => a + b, 0)
  if (sum > 0) return weights.map((w) => w / sum)
  return weights.map(() => 1 / weights.length)
}

export function yearRange(start = 2000, end = new Date().getFullYear()): number[] {
  return Array.from({ length: end - start + 1 }, (_, i) => start + i)
}

export function getGenreForPlaylist(genres: string[], subgenres: string[]): string {
  if (!genres.length) return ''
  if (!subgenres.length) return `- ${genres.join(',')}`
  return `- ${subgenres.join(',')}`
}

export function getPublicationForPlaylist(publications: string[]): string {
  if (!publications.length) return ''
  return `- ${publications.join(',')}`
}

export function dedupeAlbums<T extends { album_key?: string; album_name?: string }>(
  tracks: T[],
): T[] {
  const seen = new Set<string>()
  return tracks.filter((t) => {
    const key = t.album_key ?? t.album_name ?? ''
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}
