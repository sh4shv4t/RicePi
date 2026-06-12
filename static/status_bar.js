/**
 * Status bar — ping, network spark, spotify now playing.
 */

const StatusBar = (() => {
  let config = {};
  let pollTimer = null;

  function formatKbps(value) {
    if (value == null || Number.isNaN(value)) return '--';
    if (value >= 1024) return `${(value / 1024).toFixed(1)}M`;
    return `${Math.round(value)}`;
  }

  function renderSpark(container, rx, tx) {
    if (!container) return;
    container.innerHTML = '';

    const wrap = document.createElement('div');
    wrap.className = 'net-spark';

    const txRow = document.createElement('div');
    txRow.className = 'net-spark__row';
    const rxRow = document.createElement('div');
    rxRow.className = 'net-spark__row';

    const txMax = Math.max(...tx, 1);
    const rxMax = Math.max(...rx, 1);

    (tx.length ? tx : [0]).forEach((val) => {
      const bar = document.createElement('span');
      bar.className = 'net-spark__bar net-spark__bar--tx';
      bar.style.height = `${Math.max((val / txMax) * 100, 12)}%`;
      txRow.appendChild(bar);
    });

    (rx.length ? rx : [0]).forEach((val) => {
      const bar = document.createElement('span');
      bar.className = 'net-spark__bar net-spark__bar--rx';
      bar.style.height = `${Math.max((val / rxMax) * 100, 12)}%`;
      rxRow.appendChild(bar);
    });

    wrap.appendChild(txRow);
    wrap.appendChild(rxRow);
    container.appendChild(wrap);
  }

  function renderSpotify(spotify) {
    const el = document.getElementById('status-spotify');
    const sep = document.querySelector('.status-bar__sep--spotify');
    if (!el) return;

    if (!config.spotify?.enabled) {
      el.classList.add('hidden');
      sep?.classList.add('hidden');
      return;
    }

    el.classList.remove('hidden');
    sep?.classList.remove('hidden');

    if (spotify?.playing && spotify.title) {
      const artist = spotify.artist ? `${spotify.artist} — ` : '';
      const text = `${artist}${spotify.title}`;
      el.textContent = `♪ ${text.length > 38 ? `${text.slice(0, 35)}...` : text}`;
      el.classList.add('status-bar__spotify--live');
    } else if (spotify?.error) {
      el.textContent = '♪ no media';
      el.classList.remove('status-bar__spotify--live');
    } else {
      el.textContent = '♪ idle';
      el.classList.remove('status-bar__spotify--live');
    }
  }

  function render(data) {
    const pingEl = document.getElementById('status-ping');
    const netEl = document.getElementById('status-net');
    const sparkEl = document.getElementById('status-net-spark');

    const ping = data.ping || {};
    if (pingEl) {
      const host = ping.host || config.status?.ping_host || '8.8.8.8';
      if (ping.ok && ping.ms != null) {
        pingEl.textContent = `ping ${host} ${ping.ms}ms`;
        pingEl.classList.toggle('status-bar__meta--warn', ping.ms > 100);
      } else {
        pingEl.textContent = `ping ${host} --`;
        pingEl.classList.remove('status-bar__meta--warn');
      }
    }

    const net = data.network || {};
    if (netEl) {
      if (net.available !== false) {
        const up = formatKbps(net.tx_kbps);
        const down = formatKbps(net.rx_kbps);
        netEl.textContent = `↑${up} ↓${down} KB/s`;
      } else {
        netEl.textContent = 'net n/a';
      }
    }

    renderSpark(sparkEl, net.spark_rx || [], net.spark_tx || []);
    renderSpotify(data.spotify);
  }

  async function refresh() {
    try {
      const data = await fetchJson('/api/status');
      render(data);
    } catch (err) {
      console.warn('[status]', err);
    }
  }

  function init(cfg) {
    config = cfg;
    refresh();
    const secs = config.status?.poll_interval_secs || 5;
    pollTimer = setInterval(refresh, secs * 1000);
  }

  return { init };
})();

window.StatusBar = StatusBar;
