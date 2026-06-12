/**
 * GIF/WebM animation player with crossfade cycling.
 */

const AnimationPlayer = (() => {
  let config = {};
  let files = [];
  let currentIndex = 0;
  let activeLayer = 'a';
  let cycleTimer = null;

  function layers() {
    return {
      a: document.querySelector('.animation-player__layer--a'),
      b: document.querySelector('.animation-player__layer--b'),
    };
  }

  function showPlaceholder() {
    const placeholder = document.getElementById('animation-placeholder');
    const { a, b } = layers();
    placeholder?.classList.remove('hidden');
    if (a) a.innerHTML = '';
    if (b) b.innerHTML = '';
    a?.classList.remove('active');
    b?.classList.remove('active');
  }

  function hidePlaceholder() {
    document.getElementById('animation-placeholder')?.classList.add('hidden');
  }

  function mediaElement(filename) {
    const folder = (config.animation?.folder || 'static/animations/').replace(/^\//, '');
    const src = `/${folder}${filename}`;
    const ext = filename.split('.').pop().toLowerCase();

    if (ext === 'gif') {
      const img = document.createElement('img');
      img.src = src;
      img.alt = '';
      return img;
    }

    const video = document.createElement('video');
    video.src = src;
    video.autoplay = true;
    video.loop = true;
    video.muted = true;
    video.playsInline = true;
    return video;
  }

  function resolveFiles() {
    const available = config.animation?.available || [];
    const current = config.animation?.current;

    if (current && available.includes(current)) {
      return [current];
    }

    if (available.length) return available;
    return [];
  }

  function loadIntoLayer(layerEl, filename, withCrossfade) {
    if (!layerEl) return;
    const el = mediaElement(filename);
    layerEl.innerHTML = '';
    layerEl.appendChild(el);

    if (withCrossfade) {
      layerEl.classList.add('animation-player__layer--crossfade-in');
      setTimeout(() => layerEl.classList.remove('animation-player__layer--crossfade-in'), 800);
    } else {
      layerEl.classList.add('active');
    }
  }

  function playFile(filename, crossfade = false) {
    hidePlaceholder();
    const { a, b } = layers();
    const incoming = activeLayer === 'a' ? b : a;
    const outgoing = activeLayer === 'a' ? a : b;

    if (crossfade && outgoing?.classList.contains('active')) {
      outgoing.classList.add('animation-player__layer--crossfade-out');
      loadIntoLayer(incoming, filename, true);
      incoming.classList.add('active');

      setTimeout(() => {
        outgoing.classList.remove('active', 'animation-player__layer--crossfade-out');
        outgoing.innerHTML = '';
      }, 800);

      activeLayer = activeLayer === 'a' ? 'b' : 'a';
    } else {
      loadIntoLayer(incoming, filename, false);
      if (outgoing) {
        outgoing.classList.remove('active');
        outgoing.innerHTML = '';
      }
      activeLayer = activeLayer === 'a' ? 'b' : 'a';
    }
  }

  function cycleNext() {
    if (files.length <= 1) return;
    currentIndex = (currentIndex + 1) % files.length;
    playFile(files[currentIndex], true);
  }

  function scheduleCycle() {
    if (cycleTimer) clearInterval(cycleTimer);
    const mins = config.animation?.cycle_every_mins || 0;
    const mode = config.animation?.mode || 'loop_single';

    if (mode === 'cycle' && mins > 0 && files.length > 1) {
      cycleTimer = setInterval(cycleNext, mins * 60 * 1000);
    }
  }

  function init(cfg) {
    config = cfg;
    files = resolveFiles();

    BootSequence.onModuleVisible('animation-module', () => {
      if (!files.length) {
        showPlaceholder();
        return;
      }

      currentIndex = 0;
      playFile(files[0], false);
      scheduleCycle();
    });
  }

  return { init };
})();

window.AnimationPlayer = AnimationPlayer;
