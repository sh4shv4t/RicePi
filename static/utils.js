/**
 * Shared utilities for RicePi dashboard.
 */

function randomInterval(callback, minMs, maxMs) {
  const schedule = () => {
    const delay = minMs + Math.random() * (maxMs - minMs);
    return setTimeout(() => {
      callback();
      timerId = schedule();
    }, delay);
  };
  let timerId = schedule();
  return () => clearTimeout(timerId);
}

function pad2(n) {
  return String(n).padStart(2, '0');
}

function fetchJson(url) {
  return fetch(url).then((r) => {
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  });
}

window.randomInterval = randomInterval;
window.pad2 = pad2;
window.fetchJson = fetchJson;
