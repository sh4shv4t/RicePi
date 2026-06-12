/**
 * Clock — colon pulse, minute flip, glitch effect.
 */

const Clock = (() => {
  let config = {};
  let lastMinute = -1;
  let stopGlitch = null;

  function formatTime(date) {
    let hours = date.getHours();
    const minutes = date.getMinutes();
    const seconds = date.getSeconds();

    if (config.clock?.format === '12h') {
      const ampm = hours >= 12 ? 'PM' : 'AM';
      hours = hours % 12 || 12;
      return { hours: pad2(hours), minutes: pad2(minutes), seconds: pad2(seconds), ampm };
    }

    return { hours: pad2(hours), minutes: pad2(minutes), seconds: pad2(seconds), ampm: null };
  }

  function formatDate(date) {
    return date.toLocaleDateString(undefined, {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  }

  function animateDigit(el, newValue) {
    if (el.textContent === newValue) return;

    el.classList.remove('clock__digit-animate-in');
    el.classList.add('clock__digit-animate-out');

    setTimeout(() => {
      el.textContent = newValue;
      el.classList.remove('clock__digit-animate-out');
      el.classList.add('clock__digit-animate-in');
      setTimeout(() => el.classList.remove('clock__digit-animate-in'), 150);
    }, 150);
  }

  function pulseColon() {
    const colon = document.querySelector('.clock__colon');
    if (!colon) return;
    colon.classList.remove('pulse');
    void colon.offsetWidth;
    colon.classList.add('pulse');
  }

  function triggerGlitch() {
    const clock = document.getElementById('clock');
    if (!clock || !config.theme?.glitch_clock) return;
    clock.classList.add('glitch');
    setTimeout(() => clock.classList.remove('glitch'), 200);
  }

  function scheduleGlitch() {
    if (stopGlitch) stopGlitch();
    if (!config.theme?.glitch_clock) return;

    const minMs = config.theme.glitch_interval_min_ms || 30000;
    const maxMs = config.theme.glitch_interval_max_ms || 90000;
    stopGlitch = randomInterval(triggerGlitch, minMs, maxMs);
  }

  function tick() {
    const now = new Date();
    const t = formatTime(now);
    const hoursEl = document.querySelector('.clock__hours');
    const minutesEl = document.querySelector('.clock__minutes');
    const secondsEl = document.getElementById('clock-seconds');
    const dateEl = document.getElementById('date');

    if (now.getMinutes() !== lastMinute) {
      animateDigit(hoursEl, t.hours);
      animateDigit(minutesEl, t.minutes);
      lastMinute = now.getMinutes();
    } else {
      if (hoursEl.textContent !== t.hours) hoursEl.textContent = t.hours;
      if (minutesEl.textContent !== t.minutes) minutesEl.textContent = t.minutes;
    }

    if (config.clock?.show_seconds && secondsEl) {
      secondsEl.classList.remove('hidden');
      secondsEl.textContent = `:${t.seconds}`;
    }

    if (dateEl) dateEl.textContent = formatDate(now);

    pulseColon();
  }

  function init(cfg) {
    config = cfg;
    lastMinute = -1;
    tick();
    setInterval(tick, 1000);
    scheduleGlitch();
  }

  return { init };
})();

window.Clock = Clock;
