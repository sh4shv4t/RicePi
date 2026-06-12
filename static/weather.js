/**
 * Weather fetch + Meteocons-style animated SVG icons.
 */

const Weather = (() => {
  let config = {};
  let stopLightning = null;
  let lastCondition = null;

  const ICONS = {
    sunny: `
      <svg class="weather-icon weather-icon--sunny" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
        <g class="weather-icon__ray" stroke="var(--color-accent)" stroke-width="2">
          <line x1="32" y1="6" x2="32" y2="14"/>
          <line x1="32" y1="50" x2="32" y2="58"/>
          <line x1="6" y1="32" x2="14" y2="32"/>
          <line x1="50" y1="32" x2="58" y2="32"/>
          <line x1="13.5" y1="13.5" x2="19" y2="19"/>
          <line x1="45" y1="45" x2="50.5" y2="50.5"/>
          <line x1="13.5" y1="50.5" x2="19" y2="45"/>
          <line x1="45" y1="19" x2="50.5" y2="13.5"/>
        </g>
        <circle class="weather-icon__sun" cx="32" cy="32" r="12" fill="var(--color-secondary)"/>
      </svg>`,

    partly_cloudy: `
      <svg class="weather-icon weather-icon--partly_cloudy" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
        <circle class="weather-icon__sun" cx="22" cy="22" r="10" fill="var(--color-secondary)"/>
        <g class="weather-icon__cloud weather-icon__cloud--primary" fill="var(--color-text-dim)">
          <ellipse cx="38" cy="38" rx="18" ry="10"/>
          <ellipse cx="26" cy="40" rx="12" ry="8"/>
          <ellipse cx="48" cy="40" rx="10" ry="7"/>
        </g>
        <g class="weather-icon__cloud weather-icon__cloud--secondary" fill="color-mix(in srgb, var(--color-text) 60%, transparent)">
          <ellipse cx="42" cy="48" rx="14" ry="7"/>
          <ellipse cx="30" cy="50" rx="10" ry="6"/>
        </g>
      </svg>`,

    cloudy: `
      <svg class="weather-icon weather-icon--cloudy" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
        <g class="weather-icon__cloud" fill="var(--color-text-dim)">
          <ellipse cx="32" cy="36" rx="22" ry="12"/>
          <ellipse cx="18" cy="38" rx="14" ry="9"/>
          <ellipse cx="46" cy="38" rx="14" ry="9"/>
        </g>
      </svg>`,

    rain: `
      <div class="weather-icon weather-icon--rain">
        <svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
          <g class="weather-icon__cloud" fill="var(--color-text-dim)">
            <ellipse cx="32" cy="28" rx="20" ry="11"/>
            <ellipse cx="18" cy="30" rx="12" ry="8"/>
            <ellipse cx="46" cy="30" rx="12" ry="8"/>
          </g>
        </svg>
        <span class="weather-icon__raindrop"></span>
        <span class="weather-icon__raindrop"></span>
        <span class="weather-icon__raindrop"></span>
        <span class="weather-icon__raindrop"></span>
        <span class="weather-icon__raindrop"></span>
        <span class="weather-icon__raindrop"></span>
      </div>`,

    thunderstorm: `
      <div class="weather-icon weather-icon--thunderstorm">
        <svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
          <g class="weather-icon__cloud" fill="var(--color-text-dim)">
            <ellipse cx="32" cy="24" rx="20" ry="11"/>
            <ellipse cx="18" cy="26" rx="12" ry="8"/>
            <ellipse cx="46" cy="26" rx="12" ry="8"/>
          </g>
          <polygon class="weather-icon__lightning" points="34,30 28,42 32,42 28,54 38,38 33,38" fill="var(--color-accent)"/>
        </svg>
        <span class="weather-icon__raindrop"></span>
        <span class="weather-icon__raindrop"></span>
        <span class="weather-icon__raindrop"></span>
        <span class="weather-icon__raindrop"></span>
        <span class="weather-icon__raindrop"></span>
        <span class="weather-icon__raindrop"></span>
      </div>`,

    snow: `
      <div class="weather-icon weather-icon--snow">
        <svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
          <g class="weather-icon__cloud" fill="var(--color-text-dim)">
            <ellipse cx="32" cy="22" rx="20" ry="11"/>
            <ellipse cx="18" cy="24" rx="12" ry="8"/>
            <ellipse cx="46" cy="24" rx="12" ry="8"/>
          </g>
        </svg>
        <span class="weather-icon__snowflake">*</span>
        <span class="weather-icon__snowflake">*</span>
        <span class="weather-icon__snowflake">*</span>
        <span class="weather-icon__snowflake">*</span>
      </div>`,

    fog: `
      <svg class="weather-icon weather-icon--fog" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
        <line x1="10" y1="24" x2="54" y2="24" stroke="var(--color-text-dim)" stroke-width="2"/>
        <line x1="14" y1="34" x2="50" y2="34" stroke="var(--color-text-dim)" stroke-width="2" opacity="0.7"/>
        <line x1="18" y1="44" x2="46" y2="44" stroke="var(--color-text-dim)" stroke-width="2" opacity="0.5"/>
      </svg>`,

    windy: `
      <div class="weather-icon weather-icon--windy">
        <span class="weather-icon__wind-streak"></span>
        <span class="weather-icon__wind-streak"></span>
        <span class="weather-icon__wind-streak"></span>
        <span class="weather-icon__wind-streak"></span>
      </div>`,

    night_clear: `
      <div class="weather-icon weather-icon--night_clear">
        <svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
          <path d="M44 12 A16 16 0 1 0 52 36 A12 12 0 1 1 44 12" fill="var(--color-secondary)"/>
        </svg>
        <span class="weather-icon__star"></span>
        <span class="weather-icon__star"></span>
        <span class="weather-icon__star"></span>
        <span class="weather-icon__star"></span>
      </div>`,
  };

  function unitSymbol() {
    return config.weather?.units === 'imperial' ? '°F' : '°C';
  }

  function windLabel(speed) {
    const unit = config.weather?.units === 'imperial' ? 'mph' : 'km/h';
    return `${Math.round(speed)} ${unit} wind`;
  }

  function setIcon(condition) {
    const container = document.getElementById('weather-icon');
    if (!container) return;

    if (lastCondition && lastCondition !== condition) {
      container.classList.add('weather-icon--fade-out');
      setTimeout(() => {
        container.innerHTML = ICONS[condition] || ICONS.cloudy;
        container.classList.remove('weather-icon--fade-out');
        container.classList.add('weather-icon--fade-in');
        setupConditionEffects(condition);
        setTimeout(() => container.classList.remove('weather-icon--fade-in'), 400);
      }, 200);
    } else {
      container.innerHTML = ICONS[condition] || ICONS.cloudy;
      setupConditionEffects(condition);
    }

    lastCondition = condition;
  }

  function setupConditionEffects(condition) {
    if (stopLightning) {
      stopLightning();
      stopLightning = null;
    }

    if (condition === 'thunderstorm') {
      stopLightning = randomInterval(() => {
        const bolt = document.querySelector('.weather-icon__lightning');
        if (!bolt) return;
        bolt.classList.add('flash');
        setTimeout(() => bolt.classList.remove('flash'), 80);
      }, 1500, 4000);
    }
  }

  function render(data) {
    const current = data.current || {};
    const tempEl = document.getElementById('weather-temp');
    const cityEl = document.getElementById('weather-city');
    const windEl = document.getElementById('weather-wind');
    const forecastEl = document.getElementById('weather-forecast');

    if (tempEl && current.temperature != null) {
      tempEl.textContent = `${Math.round(current.temperature)}${unitSymbol()}`;
    }

    if (cityEl) cityEl.textContent = data.city || config.location?.city || '';
    if (windEl && current.windspeed != null) windEl.textContent = windLabel(current.windspeed);

    setIcon(current.condition || 'cloudy');

    if (forecastEl && data.today?.length) {
      const day = data.today[0];
      forecastEl.innerHTML = `
        <div class="weather__forecast-item">
          today <span>${day.min != null ? Math.round(day.min) : '--'}°</span> – <span>${day.max != null ? Math.round(day.max) : '--'}°</span>
        </div>`;
    }

    const sunEl = document.getElementById('weather-sun');
    if (sunEl) {
      const sunrise = data.sunrise || data.today?.[0]?.sunrise;
      const sunset = data.sunset || data.today?.[0]?.sunset;
      if (sunrise && sunset) {
        sunEl.textContent = `↑ ${sunrise}  ↓ ${sunset}`;
      } else {
        sunEl.textContent = '';
      }
    }
  }

  async function refresh() {
    try {
      const data = await fetchJson('/api/weather');
      render(data);
    } catch (err) {
      console.warn('[weather]', err);
    }
  }

  function init(cfg) {
    config = cfg;
    refresh();
    const mins = config.weather?.update_interval_mins || 15;
    setInterval(refresh, mins * 60 * 1000);
  }

  return { init, refresh };
})();

window.Weather = Weather;
