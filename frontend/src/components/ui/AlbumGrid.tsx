import AlbumCard from './AlbumCard'
import type { Accolade } from '../../api/types'

interface AlbumItem {
  album_key: string
  artist: string
  album: string
  genre: string
  subgenre?: string
  year: number
  image_url: string
  moods?: string[]
  apple_music_album_url?: string
  album_url?: string
}

interface AlbumGridProps {
  albums: AlbumItem[]
  accolades?: Record<string, Accolade[]>
  columns?: 1 | 2
  showPositions?: boolean
  showSubgenres?: boolean
  startIndex?: number
  endIndex?: number
}

export default function AlbumGrid({
  albums,
  accolades,
  columns = 1,
  showPositions = true,
  showSubgenres = false,
  startIndex = 0,
  endIndex,
}: AlbumGridProps) {
  const sliced = albums.slice(startIndex, endIndex ?? albums.length)

  return (
    <div
      className={
        columns === 2
          ? 'grid grid-cols-1 gap-4 lg:grid-cols-2'
          : 'flex flex-col gap-4'
      }
    >
      {sliced.map((a, i) => (
        <AlbumCard
          key={a.album_key + i}
          position={showPositions ? startIndex + i : undefined}
          artist={a.artist}
          album={a.album}
          genre={a.genre}
          subgenre={a.subgenre}
          year={a.year}
          imageUrl={a.image_url}
          moods={a.moods}
          appleMusicUrl={a.apple_music_album_url ?? a.album_url}
          accolades={accolades?.[a.album_key]}
          showSubgenres={showSubgenres}
        />
      ))}
    </div>
  )
}
