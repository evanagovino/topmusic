interface AlbumCardCompactProps {
  artist: string
  album: string
  year: number
  imageUrl: string
  appleMusicUrl?: string
}

export default function AlbumCardCompact({
  artist,
  album,
  year,
  imageUrl,
  appleMusicUrl,
}: AlbumCardCompactProps) {
  const content = (
    <div className="flex w-56 flex-shrink-0 flex-col gap-1.5">
      <img
        src={imageUrl}
        alt={`${artist} - ${album}`}
        className="h-56 w-56 rounded-lg object-cover"
        loading="lazy"
      />
      <div className="flex flex-col gap-0.5 px-0.5">
        <p className="truncate text-sm font-semibold text-white">{artist}</p>
        <p className="truncate text-xs text-gray-400">{album}</p>
        <p className="text-xs text-gray-600">{year}</p>
      </div>
    </div>
  )

  if (appleMusicUrl) {
    return (
      <a href={appleMusicUrl} target="_blank" rel="noopener noreferrer">
        {content}
      </a>
    )
  }

  return content
}
