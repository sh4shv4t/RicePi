/**
 * Calendar grid, event slide-ins, midnight today transition.
 */

const Calendar = (() => {
  let config = {};
  let events = [];
  let todayCell = null;
  let midnightTimer = null;

  const DAY_NAMES = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'];

  function parseDate(str) {
    const [y, m, d] = str.split('-').map(Number);
    return new Date(y, m - 1, d);
  }

  function dateKey(date) {
    return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}`;
  }

  function isSameDay(a, b) {
    return a.getFullYear() === b.getFullYear()
      && a.getMonth() === b.getMonth()
      && a.getDate() === b.getDate();
  }

  function buildGrid(referenceDate) {
    const grid = document.getElementById('calendar-grid');
    const monthEl = document.getElementById('calendar-month');
    if (!grid) return;

    const year = referenceDate.getFullYear();
    const month = referenceDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const startOffset = firstDay.getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const daysInPrev = new Date(year, month, 0).getDate();

    grid.innerHTML = '';
    todayCell = null;

    if (monthEl) {
      monthEl.textContent = referenceDate.toLocaleDateString(undefined, {
        month: 'long',
        year: 'numeric',
      }).toLowerCase();
    }

    DAY_NAMES.forEach((name) => {
      const label = document.createElement('div');
      label.className = 'calendar-grid__day-name';
      label.textContent = name;
      grid.appendChild(label);
    });

    const today = new Date();

    for (let i = 0; i < startOffset; i += 1) {
      const cell = document.createElement('div');
      cell.className = 'calendar-grid__cell calendar-grid__cell--other-month';
      cell.textContent = daysInPrev - startOffset + i + 1;
      grid.appendChild(cell);
    }

    for (let day = 1; day <= daysInMonth; day += 1) {
      const cellDate = new Date(year, month, day);
      const cell = document.createElement('div');
      cell.className = 'calendar-grid__cell';
      cell.textContent = day;
      cell.dataset.date = dateKey(cellDate);

      if (isSameDay(cellDate, today)) {
        cell.classList.add('calendar-grid__cell--today');
        todayCell = cell;
      }

      grid.appendChild(cell);
    }

    const totalCells = startOffset + daysInMonth;
    const trailing = totalCells % 7 === 0 ? 0 : 7 - (totalCells % 7);
    for (let i = 1; i <= trailing; i += 1) {
      const cell = document.createElement('div');
      cell.className = 'calendar-grid__cell calendar-grid__cell--other-month';
      cell.textContent = i;
      grid.appendChild(cell);
    }
  }

  function renderEvents() {
    const list = document.getElementById('calendar-events');
    if (!list) return;

    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const count = config.calendar?.show_upcoming_count || 3;

    const upcoming = events
      .map((e) => ({ ...e, dateObj: parseDate(e.date) }))
      .filter((e) => e.dateObj >= today)
      .sort((a, b) => a.dateObj - b.dateObj)
      .slice(0, count);

    list.innerHTML = '';
    upcoming.forEach((event, index) => {
      const li = document.createElement('li');
      li.className = 'calendar-events__item';
      li.innerHTML = `<span class="calendar-events__time">${event.time || ''}</span>${event.title}`;
      list.appendChild(li);
      setTimeout(() => li.classList.add('animate-in'), index * 100);
    });
  }

  function transitionTodayHighlight() {
    const prev = todayCell;
    buildGrid(new Date());

    if (prev) {
      prev.classList.remove('calendar-grid__cell--today');
      prev.classList.add('calendar-grid__cell--today-fade-out');
    }

    if (todayCell) {
      todayCell.classList.remove('calendar-grid__cell--today');
      todayCell.classList.add('calendar-grid__cell--today-fade-in');
      setTimeout(() => {
        todayCell.classList.remove('calendar-grid__cell--today-fade-in');
        todayCell.classList.add('calendar-grid__cell--today');
      }, 500);
    }

    renderEvents();
    scheduleMidnight();
  }

  function msUntilMidnight() {
    const now = new Date();
    const midnight = new Date(now);
    midnight.setHours(24, 0, 0, 0);
    return midnight - now;
  }

  function scheduleMidnight() {
    if (midnightTimer) clearTimeout(midnightTimer);
    midnightTimer = setTimeout(transitionTodayHighlight, msUntilMidnight());
  }

  async function loadEvents() {
    try {
      events = await fetchJson('/api/events');
      if (!Array.isArray(events)) events = [];
    } catch {
      events = [];
    }
  }

  async function init(cfg) {
    config = cfg;
    await loadEvents();
    buildGrid(new Date());
    renderEvents();
    scheduleMidnight();
  }

  return { init };
})();

window.Calendar = Calendar;
