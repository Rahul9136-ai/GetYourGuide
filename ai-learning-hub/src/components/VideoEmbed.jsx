// Responsive YouTube embed shown at the top of lessons that have a curated video.
// Uses the privacy-enhanced youtube-nocookie domain and lazy loading.

export default function VideoEmbed({ video }) {
  if (!video) return null
  const { id, src, title, author } = video
  const isLocal = Boolean(src) // a generated MP4 served from /public

  return (
    <div className="video-card">
      <div className="video-frame">
        {isLocal ? (
          <video src={src} controls playsInline preload="metadata" />
        ) : (
          <iframe
            src={`https://www.youtube-nocookie.com/embed/${id}`}
            title={title}
            loading="lazy"
            frameBorder="0"
            allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
            allowFullScreen
          />
        )}
      </div>
      <div className="video-meta">
        <span className="video-play">▶</span>
        <span><b>Watch:</b> {title}</span>
        {author && <span className="video-author">· {author}</span>}
        {isLocal ? (
          <span className="video-link" style={{ cursor: 'default' }}>✨ AI-generated</span>
        ) : (
          <a
            className="video-link"
            href={`https://www.youtube.com/watch?v=${id}`}
            target="_blank"
            rel="noopener noreferrer"
          >
            Open on YouTube ↗
          </a>
        )}
      </div>
    </div>
  )
}
