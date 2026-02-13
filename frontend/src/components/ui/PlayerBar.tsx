import { usePlayerStore } from '../../store/playerStore'
import { useAuthStore } from '../../store/authStore'

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

export default function PlayerBar() {
  const {
    isPlaying,
    currentTrack,
    currentTime,
    duration,
    togglePlayPause,
    next,
    previous,
    seekTo,
    close,
    lovedTrackIds,
    toggleLove,
  } = usePlayerStore()
  const isAuthorized = useAuthStore((s) => s.isAuthorized)

  if (!currentTrack) return null

  const isLoved = lovedTrackIds.has(currentTrack.track_id)

  const progressPct = duration > 0 ? (currentTime / duration) * 100 : 0

  function handleProgressClick(e: React.MouseEvent<HTMLDivElement>) {
    if (duration <= 0) return
    const rect = e.currentTarget.getBoundingClientRect()
    const pct = (e.clientX - rect.left) / rect.width
    seekTo(pct * duration)
  }

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 border-t border-gray-700 bg-gray-900">
      {/* Progress bar (thin, clickable) */}
      <div
        className="h-1 w-full cursor-pointer bg-gray-700"
        onClick={handleProgressClick}
      >
        <div
          className="h-full bg-indigo-500 transition-[width] duration-200"
          style={{ width: `${progressPct}%` }}
        />
      </div>

      <div className="flex items-center gap-2 px-2 py-2 sm:gap-4 sm:px-4">
        {/* Left: track info */}
        <div className="flex min-w-0 flex-1 items-center gap-3">
          {currentTrack.image_url && (
            <img
              src={currentTrack.image_url}
              alt=""
              className="h-10 w-10 flex-shrink-0 rounded"
            />
          )}
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-white">
              {currentTrack.track_name}
            </p>
            <p className="truncate text-xs text-gray-400">
              {currentTrack.artist}
            </p>
          </div>
        </div>

        {/* Center: controls */}
        <div className="flex items-center gap-1 sm:gap-3">
          <button
            type="button"
            onClick={previous}
            className="rounded p-2 text-gray-400 hover:text-white"
            aria-label="Previous track"
          >
            <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M6 6h2v12H6zm3.5 6 8.5 6V6z" />
            </svg>
          </button>

          <button
            type="button"
            onClick={togglePlayPause}
            className="flex h-8 w-8 items-center justify-center rounded-full bg-white text-gray-900 hover:bg-gray-200"
            aria-label={isPlaying ? 'Pause' : 'Play'}
          >
            {isPlaying ? (
              <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
              </svg>
            ) : (
              <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z" />
              </svg>
            )}
          </button>

          <button
            type="button"
            onClick={next}
            className="rounded p-2 text-gray-400 hover:text-white"
            aria-label="Next track"
          >
            <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z" />
            </svg>
          </button>

          <span className="ml-2 hidden text-xs text-gray-500 sm:inline">
            {formatTime(currentTime)} / {formatTime(duration)}
          </span>

          {isAuthorized && (
            <button
              type="button"
              onClick={() => toggleLove(currentTrack.track_id)}
              className="ml-2 hidden rounded p-1 transition-colors hover:bg-gray-800 sm:block"
              aria-label={isLoved ? 'Remove from favorites' : 'Add to favorites'}
            >
              <svg
                className={`h-4 w-4 ${isLoved ? 'text-pink-500' : 'text-gray-500'}`}
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
            </button>
          )}
        </div>

        {/* Right: close */}
        <div className="flex flex-1 justify-end">
          <button
            type="button"
            onClick={close}
            className="rounded p-2 text-gray-400 hover:text-white"
            aria-label="Close player"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}
