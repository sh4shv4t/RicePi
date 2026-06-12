/**
 * Staggered module cascade on page load.
 */

const BootSequence = (() => {
  const DELAYS = {
    'clock-module': 0,
    'sysinfo-module': 200,
    'weather-module': 400,
    'calendar-module': 600,
    'animation-module': 800,
    'quote-module': 1000,
  };

  function init(config) {
    Object.entries(DELAYS).forEach(([id, delay]) => {
      const el = document.getElementById(id);
      if (!el) return;

      setTimeout(() => {
        if (id === 'animation-module') {
          el.classList.add('module--boot-visible');
        } else {
          el.classList.add('module--boot-visible');
        }
        el.dataset.bootComplete = 'true';
        el.dispatchEvent(new CustomEvent('ricepi:boot-visible'));
      }, delay);
    });
  }

  function onModuleVisible(moduleId, callback) {
    const el = document.getElementById(moduleId);
    if (!el) return;
    if (el.dataset.bootComplete === 'true') {
      callback();
    } else {
      el.addEventListener('ricepi:boot-visible', callback, { once: true });
    }
  }

  return { init, onModuleVisible, DELAYS };
})();

window.BootSequence = BootSequence;
