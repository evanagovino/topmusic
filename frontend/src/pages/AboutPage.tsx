export default function AboutPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-6 sm:px-6 sm:py-10">
      <h1 className="mb-2 text-3xl font-bold text-white">TopMusic</h1>
      <h2 className="mb-6 text-xl text-gray-400">A new way to discover music.</h2>

      <div className="space-y-6 text-gray-300 leading-relaxed">
        <p>
          TopMusic aggregates album rankings from dozens of music publications and
          critic lists to surface the most acclaimed albums of the 21st century. Use
          filters to explore by genre, year, publication, and mood. Connect your Apple
          Music account to play music directly in the browser and favorite songs to
          your library.
        </p>

        <h3 className="text-lg font-semibold text-white">Top Albums</h3>
        <p>
          Browse the highest-rated albums across all tracked publications. Filter by
          genre, subgenre, publication, list, mood, and year to find exactly what
          you're looking for. Authenticated users can play the full filtered list
          directly in the browser.
        </p>

        <h3 className="text-lg font-semibold text-white">Radio</h3>
        <p>
          Generate personalized playlists in three ways: by genre (pick a genre and
          year range), by artist (choose an artist to hear similar music), or by
          custom prompt (describe what you want and our AI builds a playlist).
        </p>

        <h3 className="text-lg font-semibold text-white">Now Playing</h3>
        <p>
          When a playlist is playing, the Now Playing page shows the current track and
          your full queue. You can skip to any song in the queue, favorite tracks to
          your Apple Music library with the heart button, and see what's coming up next.
        </p>

        <h3 className="text-lg font-semibold text-white">Data</h3>
        <p>
          Explore similarity scores between artists and albums. Select an artist to
          see which other artists are most similar based on genre overlap, publication
          co-occurrence, and audio feature analysis.
        </p>

        <h3 className="text-lg font-semibold text-white">Apple Music Integration</h3>
        <p>
          Connect your Apple Music account to play music directly in the browser and
          favorite songs to your Favorite Songs playlist. Click "Connect Apple Music"
          in the navigation bar to authenticate.
        </p>
      </div>
    </div>
  )
}
