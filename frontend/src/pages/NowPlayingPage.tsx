import { usePlayerStore } from '../store/playerStore'
import { useAuthStore } from '../store/authStore'

export default function NowPlayingPage() {
  const queue = usePlayerStore((s) => s.queue)
  const queueName = usePlayerStore((s) => s.queueName)
  const currentIndex = usePlayerStore((s) => s.currentIndex)
  const currentTrack = usePlayerStore((s) => s.currentTrack)
  const isPlaying = usePlayerStore((s) => s.isPlaying)
  const isPlayerVisible = usePlayerStore((s) => s.isPlayerVisible)
  const togglePlayPause = usePlayerStore((s) => s.togglePlayPause)
  const playTrackAtIndex = usePlayerStore((s) => s.playTrackAtIndex)
  const lovedTrackIds = usePlayerStore((s) => s.lovedTrackIds)
  const pendingLoveIds = usePlayerStore((s) => s.pendingLoveIds)
  const toggleLove = usePlayerStore((s) => s.toggleLove)
  const isAuthorized = useAuthStore((s) => s.isAuthorized)
  const createPlaylist = useAuthStore((s) => s.createPlaylist)

  if (!isPlayerVisible || !currentTrack) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-gray-500">
          Nothing playing. Start a playlist from Top Albums or Radio.
        </p>
      </div>
    )
  }

  const upNext = queue.slice(currentIndex + 1)
  const currentIsLoved = lovedTrackIds.has(currentTrack.track_id)

  return (
    <div className="flex h-full flex-col overflow-y-auto">
      <div className="mx-auto w-full max-w-3xl px-4 py-6 sm:px-6 sm:py-8">
        {queueName && (
          <h1 className="mb-6 text-center text-lg font-semibold text-gray-300 sm:text-left">
            {queueName}
          </h1>
        )}

        {/* Now Playing */}
        <div className="flex flex-col items-center gap-4 sm:flex-row sm:items-start sm:gap-6">
          {currentTrack.image_url && (
            <img
              src={currentTrack.image_url}
              alt={`${currentTrack.artist} - ${currentTrack.album_name}`}
              className="h-48 w-48 flex-shrink-0 rounded-lg object-cover shadow-lg sm:h-52 sm:w-52"
            />
          )}
          <div className="flex flex-col items-center gap-2 sm:items-start sm:pt-2">
            <span className="text-xs font-medium uppercase tracking-wider text-indigo-400">
              Now Playing
            </span>
            <h2 className="text-center text-2xl font-bold text-white sm:text-left">
              {currentTrack.track_name}
            </h2>
            <p className="text-lg text-gray-200">{currentTrack.artist}</p>
            <p className="text-sm text-gray-400">{currentTrack.album_name}</p>
            {currentTrack.year && (
              <p className="text-sm text-gray-500">
                {currentTrack.subgenre ?? currentTrack.genre} &middot; {currentTrack.year}
              </p>
            )}
            <div className="mt-2 flex items-center gap-3">
              <button
                type="button"
                onClick={togglePlayPause}
                className="flex items-center gap-2 rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-indigo-500"
              >
                {isPlaying ? (
                  <>
                    <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
                    </svg>
                    Pause
                  </>
                ) : (
                  <>
                    <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M8 5v14l11-7z" />
                    </svg>
                    Play
                  </>
                )}
              </button>
              {isAuthorized && (
                <button
                  type="button"
                  onClick={() => toggleLove(currentTrack.track_id)}
                  className="rounded-lg p-2.5 transition-colors hover:bg-gray-800"
                  aria-label={currentIsLoved ? 'Remove from favorites' : 'Add to favorites'}
                  title={currentIsLoved ? 'Remove from favorites' : 'Add to favorites'}
                >
                  <svg
                    className={`h-6 w-6 ${currentIsLoved ? 'text-pink-500' : 'text-gray-400'}`}
                    fill={currentIsLoved ? 'currentColor' : 'none'}
                    stroke="currentColor"
                    strokeWidth={currentIsLoved ? 0 : 2}
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
              {isAuthorized && (
                <button
                  type="button"
                  onClick={async () => {
                    const trackIds = queue.map((t) => t.track_id)
                    const success = await createPlaylist(queueName ?? 'Now Playing', trackIds)
                    if (success) {
                      alert('Playlist created! Check your Apple Music library.')
                    } else {
                      alert('Failed to create playlist. Please try again.')
                    }
                  }}
                  className="rounded-lg bg-pink-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-pink-500"
                >
                  Create Apple Music Playlist
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Up Next */}
        {upNext.length > 0 && (
          <div className="mt-10">
            <h3 className="mb-4 text-sm font-medium uppercase tracking-wider text-gray-400">
              Up Next ({upNext.length})
            </h3>
            <div className="flex flex-col gap-1">
              {upNext.map((track, i) => {
                const queueIndex = currentIndex + 1 + i
                const isLoved = lovedTrackIds.has(track.track_id)
                const isPendingLove = pendingLoveIds.has(track.track_id)
                return (
                  <div
                    key={track.track_id + queueIndex}
                    className="flex items-center gap-3 rounded-lg px-3 py-2 transition-colors hover:bg-gray-800"
                  >
                    <button
                      type="button"
                      onClick={() => playTrackAtIndex(queue, queueIndex)}
                      className="flex min-w-0 flex-1 items-center gap-3 text-left"
                    >
                      {track.image_url ? (
                        <img
                          src={track.image_url}
                          alt={track.album_name}
                          className="h-12 w-12 flex-shrink-0 rounded object-cover"
                          loading="lazy"
                        />
                      ) : (
                        <div className="h-12 w-12 flex-shrink-0 rounded bg-gray-800" />
                      )}
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium text-white">
                          {track.track_name}
                        </p>
                        <p className="truncate text-xs text-gray-400">
                          {track.artist}{track.album_name ? ` — ${track.album_name}` : ''}
                        </p>
                      </div>
                    </button>
                    {isAuthorized && (
                      <button
                        type="button"
                        onClick={() => toggleLove(track.track_id)}
                        disabled={isPendingLove}
                        className="flex-shrink-0 rounded p-2 transition-colors hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        aria-label={isLoved ? 'Remove from favorites' : 'Add to favorites'}
                      >
                        <svg
                          className={`h-4 w-4 ${isPendingLove ? 'animate-pulse text-gray-500' : isLoved ? 'text-pink-500' : 'text-gray-500'}`}
                          fill={isLoved && !isPendingLove ? 'currentColor' : 'none'}
                          stroke="currentColor"
                          strokeWidth={isLoved && !isPendingLove ? 0 : 2}
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
                )
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
