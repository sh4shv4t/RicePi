/**
 * Sysinfo widget — typewriter lines and bar animations.
 */

const Sysinfo = (() => {
  let config = {};
  let previousData = null;

  function buildLines(data) {
    const items = config.sysinfo?.items || [];
    const lines = [];

    items.forEach((key) => {
      switch (key) {
        case 'os':
          lines.push({ label: 'os', value: data.os || 'unknown' });
          break;
        case 'kernel':
          lines.push({ label: 'kernel', value: data.kernel || 'unknown' });
          break;
        case 'uptime':
          lines.push({ label: 'uptime', value: data.uptime || 'unknown' });
          break;
        case 'ram': {
          const ram = data.ram || {};
          lines.push({
            label: 'ram',
            value: `${ram.used_mb || 0}/${ram.total_mb || 0} MB`,
            bar: ram.percent || 0,
          });
          break;
        }
        case 'cpu_temp':
          lines.push({
            label: 'cpu',
            value: data.cpu_temp != null ? `${data.cpu_temp}°C` : 'n/a',
          });
          break;
        default:
          break;
      }
    });

    return lines;
  }

  function renderLines(lines, animate) {
    const container = document.getElementById('sysinfo-content');
    if (!container) return;

    container.innerHTML = lines.map((line, i) => {
      const barHtml = line.bar != null
        ? `<span class="sysinfo__bar-wrap"><span class="sysinfo__bar" data-width="${line.bar}"></span></span>`
        : '';
      return `<div class="sysinfo__line" data-index="${i}"><span class="sysinfo__label">${line.label}</span> <span class="sysinfo__value">${line.value}</span>${barHtml}</div>`;
    }).join('');

    if (animate) {
      BootSequence.onModuleVisible('sysinfo-module', () => {
        setTimeout(() => {
          lines.forEach((_, i) => {
            setTimeout(() => {
              const el = container.querySelector(`.sysinfo__line[data-index="${i}"]`);
              if (el) el.classList.add('typewriter-in');
            }, i * 80);
          });

          setTimeout(() => {
            container.querySelectorAll('.sysinfo__bar').forEach((bar) => {
              bar.style.width = `${bar.dataset.width}%`;
            });
          }, lines.length * 80 + 100);
        }, 600);
      });
    } else {
      container.querySelectorAll('.sysinfo__line').forEach((el) => el.classList.add('typewriter-in'));
      container.querySelectorAll('.sysinfo__bar').forEach((bar) => {
        bar.style.width = `${bar.dataset.width}%`;
      });
    }
  }

  function flashUpdates(data) {
    const container = document.getElementById('sysinfo-content');
    if (!container || !previousData) return;

    const lines = buildLines(data);
    const prevLines = buildLines(previousData);

    lines.forEach((line, i) => {
      const prev = prevLines[i];
      if (!prev || prev.value !== line.value) {
        const valueEl = container.querySelector(`.sysinfo__line[data-index="${i}"] .sysinfo__value`);
        if (valueEl) {
          valueEl.classList.add('flash');
          setTimeout(() => valueEl.classList.remove('flash'), 300);
        }
      }
    });
  }

  async function refresh(animate = false) {
    if (!config.sysinfo?.show) {
      document.getElementById('sysinfo-module')?.classList.add('hidden');
      return;
    }

    try {
      const data = await fetchJson('/api/sysinfo');
      const lines = buildLines(data);
      if (!previousData) {
        renderLines(lines, animate);
      } else {
        flashUpdates(data);
        const container = document.getElementById('sysinfo-content');
        lines.forEach((line, i) => {
          const valueEl = container?.querySelector(`.sysinfo__line[data-index="${i}"] .sysinfo__value`);
          if (valueEl) valueEl.textContent = line.value;
          if (line.bar != null) {
            const bar = container?.querySelector(`.sysinfo__line[data-index="${i}"] .sysinfo__bar`);
            if (bar) bar.style.width = `${line.bar}%`;
          }
        });
      }
      previousData = data;
    } catch (err) {
      console.warn('[sysinfo]', err);
    }
  }

  function init(cfg) {
    config = cfg;
    refresh(true);
    setInterval(() => refresh(false), 30000);
  }

  return { init };
})();

window.Sysinfo = Sysinfo;
