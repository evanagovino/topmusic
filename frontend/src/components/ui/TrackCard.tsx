import { useState } from 'react'
import type { Track } from '../../api/types'
import { useAuthStore } from '../../store/authStore'
import { usePlayerStore } from '../../store/playerStore'

interface TrackCardProps {
  track: Track
  position?: number
  allTracks?: Track[]
  trackIndex?: number
}

export default function TrackCard({ track, position, allTracks, trackIndex }: TrackCardProps) {
  const [listenOpen, setListenOpen] = useState(false)
  const isAuthorized = useAuthStore((s) => s.isAuthorized)
  const playTrackAtIndex = usePlayerStore((s) => s.playTrackAtIndex)
  const currentTrack = usePlayerStore((s) => s.currentTrack)
  const isPlaying = usePlayerStore((s) => s.isPlaying)

  const lovedTrackIds = usePlayerStore((s) => s.lovedTrackIds)
  const toggleLove = usePlayerStore((s) => s.toggleLove)

  const isCurrentTrack = currentTrack?.track_id === track.track_id
  const isLoved = lovedTrackIds.has(track.track_id)
  const canPlay = isAuthorized && allTracks && trackIndex !== undefined

  function handlePlay() {
    if (canPlay) {
      playTrackAtIndex(allTracks, trackIndex)
    }
  }

  return (
    <div className={`flex gap-3 rounded-xl p-3 sm:gap-4 sm:p-4 ${isCurrentTrack ? 'bg-gray-800 ring-1 ring-indigo-500' : 'bg-gray-900'}`}>
      {track.image_url && (
        <div className="relative flex-shrink-0">
          <img
            src={track.image_url}
            alt={`${track.artist} - ${track.album_name}`}
            className="h-28 w-28 rounded-lg object-cover sm:h-40 sm:w-40 md:h-48 md:w-48"
            loading="lazy"
          />
          {canPlay && (
            <button
              type="button"
              onClick={handlePlay}
              className="absolute inset-0 flex items-center justify-center rounded-lg bg-black/40 opacity-0 transition-opacity hover:opacity-100"
              aria-label={`Play ${track.track_name}`}
            >
              {isCurrentTrack && isPlaying ? (
                <svg className="h-12 w-12 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
                </svg>
              ) : (
                <svg className="h-12 w-12 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z" />
                </svg>
              )}
            </button>
          )}
        </div>
      )}
      <div className="flex min-w-0 flex-1 flex-col justify-center gap-1">
        {position !== undefined && (
          <span className="text-lg font-bold text-indigo-400">#{position + 1}</span>
        )}
        <h3 className="truncate text-lg font-semibold text-white">{track.track_name}</h3>
        <h4 className="truncate text-base text-gray-200">{track.artist}</h4>
        <p className="truncate text-sm text-gray-300">{track.album_name}</p>
        <p className="text-sm text-gray-400">
          {track.subgenre ?? track.genre}
        </p>
        {track.year && <p className="text-sm text-gray-500">{track.year}</p>}

        {isAuthorized && (
          <button
            type="button"
            onClick={() => toggleLove(track.track_id)}
            className="mt-1 flex items-center gap-1.5 py-1 text-left text-xs font-medium text-gray-400 hover:text-gray-200"
            aria-label={isLoved ? 'Remove from favorites' : 'Add to favorites'}
          >
            <svg
              className={`h-4 w-4 ${isLoved ? 'text-pink-500' : 'text-gray-400'}`}
              fill={isLoved ? 'currentColor' : 'none'}
              stroke="currentColor"
              strokeWidth={isLoved ? 0 : 2}
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"
              />
            </svg>
            {isLoved ? 'Loved' : 'Love'}
          </button>
        )}

        <button
          type="button"
          onClick={() => setListenOpen(!listenOpen)}
          className="mt-2 py-1 text-left text-xs font-medium text-gray-400 hover:text-gray-200"
        >
          {listenOpen ? '- Listen' : '+ Listen'}
        </button>
        {listenOpen && (
          <div className="mt-1">
            {track.album_url ? (
              <a
                href={track.album_url}
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
