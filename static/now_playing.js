/**
 * Bottom-left now playing widget with album art.
 */

const NowPlaying = (() => {
  let config = {};
  let lastTrack = '';
  let pollTimer = null;

  function setVisible(show) {
    const module = document.getElementById('nowplaying-module');
    if (!module) return;
    module.classList.toggle('nowplaying-module--disabled', !show);
  }

  function render(data) {
    const module = document.getElementById('nowplaying-module');
    const art = document.getElementById('nowplaying-art');
    const titleEl = document.getElementById('nowplaying-title');
    const artistEl = document.getElementById('nowplaying-artist');
    const stateEl = document.getElementById('nowplaying-state');
    const artPlaceholder = document.getElementById('nowplaying-art-placeholder');

    if (!config.spotify?.enabled) {
      setVisible(false);
      return;
    }

    setVisible(true);

    if (data?.playing && data.title) {
      const trackKey = `${data.artist || ''}|${data.title}`;
      const trackChanged = trackKey !== lastTrack;
      lastTrack = trackKey;

      if (titleEl) titleEl.textContent = data.title;
      if (artistEl) artistEl.textContent = data.artist || 'Unknown artist';
      if (stateEl) stateEl.textContent = 'now playing';

      if (art && data.has_art && data.art_url) {
        if (artPlaceholder) artPlaceholder.classList.add('hidden');
        const artUrl = data.art_url.startsWith('/') ? data.art_url : `/${data.art_url}`;
        if (trackChanged || !art.src.includes('/api/spotify/art')) {
          art.classList.add('nowplaying__art--fade');
          art.onload = () => art.classList.remove('nowplaying__art--fade');
          art.src = artUrl;
        }
        art.classList.remove('hidden');
      } else {
        if (art) {
          art.classList.add('hidden');
          art.removeAttribute('src');
        }
        if (artPlaceholder) artPlaceholder.classList.remove('hidden');
      }

      module?.classList.add('nowplaying--live');
    } else {
      lastTrack = '';
      if (titleEl) titleEl.textContent = 'nothing playing';
      if (artistEl) artistEl.textContent = 'start spotify to begin';
      if (stateEl) stateEl.textContent = 'idle';
      if (art) {
        art.classList.add('hidden');
        art.removeAttribute('src');
      }
      if (artPlaceholder) artPlaceholder.classList.remove('hidden');
      module?.classList.remove('nowplaying--live');
    }
  }

  async function refresh() {
    try {
      const data = await fetchJson('/api/spotify');
      render(data);
    } catch (err) {
      console.warn('[nowplaying]', err);
    }
  }

  function init(cfg) {
    config = cfg;
    if (!config.spotify?.enabled) {
      setVisible(false);
      return;
    }
    refresh();
    const secs = config.spotify?.poll_secs || config.status?.poll_interval_secs || 5;
    pollTimer = setInterval(refresh, secs * 1000);
  }

  return { init, refresh };
})();

window.NowPlaying = NowPlaying;
