import { useState, useEffect } from 'react'
import MoodBadge from './MoodBadge'
import AccoladesPanel from './AccoladesPanel'
import type { Accolade } from '../../api/types'
import { useTracksFromAlbums } from '../../api/hooks/useTracksFromAlbums'
import { usePlayerStore } from '../../store/playerStore'
import { useAuthStore } from '../../store/authStore'

interface AlbumCardProps {
  position?: number
  albumKey?: string
  artist: string
  album: string
  genre: string
  subgenre?: string
  year: number
  imageUrl: string
  moods?: string[]
  appleMusicUrl?: string
  accolades?: Accolade[]
  showSubgenres?: boolean
}

export default function AlbumCard({
  position,
  albumKey,
  artist,
  album,
  genre,
  subgenre,
  year,
  imageUrl,
  moods,
  appleMusicUrl,
  accolades,
  showSubgenres,
}: AlbumCardProps) {
  const [accoladesOpen, setAccoladesOpen] = useState(false)
  const [listenOpen, setListenOpen] = useState(false)
  const [fetchEnabled, setFetchEnabled] = useState(false)
  const [pendingPlay, setPendingPlay] = useState(false)

  const isAuthorized = useAuthStore((s) => s.isAuthorized)
  const playTracks = usePlayerStore((s) => s.playTracks)

  const { data: tracks, isFetching } = useTracksFromAlbums(
    albumKey ? [albumKey] : [],
    500,
    fetchEnabled && !!albumKey,
    { weightTracks: false, shuffleTracks: false },
  )

  useEffect(() => {
    if (pendingPlay && tracks && tracks.length > 0 && !isFetching) {
      playTracks(tracks, `${artist} - ${album}`)
      setPendingPlay(false)
    }
  }, [pendingPlay, tracks, isFetching, playTracks, artist, album])

  return (
    <div className="flex gap-3 rounded-xl bg-gray-900 p-3 sm:gap-4 sm:p-4">
      <img
        src={imageUrl}
        alt={`${artist} - ${album}`}
        className="h-28 w-28 flex-shrink-0 rounded-lg object-cover sm:h-40 sm:w-40 md:h-48 md:w-48"
        loading="lazy"
      />
      <div className="flex min-w-0 flex-1 flex-col justify-center gap-1">
        {position !== undefined && (
          <span className="text-lg font-bold text-indigo-400">#{position + 1}</span>
        )}
        <h3 className="truncate text-lg font-semibold text-white">{artist}</h3>
        <h4 className="truncate text-base text-gray-200">{album}</h4>
        <p className="text-sm text-gray-400">
          {showSubgenres && subgenre ? subgenre : genre}
        </p>
        <p className="text-sm text-gray-500">{year}</p>

        {moods && moods.length > 0 && (
          <div className="mt-1 flex flex-wrap gap-1">
            {[...moods].sort().map((m) => (
              <MoodBadge key={m} mood={m} />
            ))}
          </div>
        )}

        {/* Accolades expander */}
        <button
          type="button"
          onClick={() => setAccoladesOpen(!accoladesOpen)}
          className="mt-2 py-1 text-left text-xs font-medium text-gray-400 hover:text-gray-200"
        >
          {accoladesOpen ? '- Accolades' : '+ Accolades'}
        </button>
        {accoladesOpen && (
          <div className="mt-1">
            <AccoladesPanel accolades={accolades} />
          </div>
        )}

        {/* Listen expander */}
        <button
          type="button"
          onClick={() => setListenOpen(!listenOpen)}
          className="py-1 text-left text-xs font-medium text-gray-400 hover:text-gray-200"
        >
          {listenOpen ? '- Listen' : '+ Listen'}
        </button>
        {listenOpen && (
          <div className="mt-1 flex flex-wrap gap-2">
            {isAuthorized && albumKey && appleMusicUrl && (
              <button
                type="button"
                onClick={() => {
                  setFetchEnabled(true)
                  setPendingPlay(true)
                }}
                disabled={isFetching && pendingPlay}
                className="inline-block rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-500 disabled:opacity-60"
              >
                {isFetching && pendingPlay ? 'Loading…' : 'Listen'}
              </button>
            )}
            {appleMusicUrl ? (
              <a
                href={appleMusicUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block rounded-lg bg-pink-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-pink-500"
              >
                Listen on Apple Music
              </a>
            ) : (
              <p className="text-sm text-gray-500">Not available on Apple Music</p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
