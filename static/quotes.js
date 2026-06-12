/**
 * Quote rotation with fade/slide transitions and blinking cursor.
 */

const Quotes = (() => {
  let config = {};
  let quotes = [];
  let index = 0;
  function showQuote(quote, animate) {
    const textEl = document.getElementById('quote-text');
    const authorEl = document.getElementById('quote-author');
    if (!textEl || !authorEl) return;

    const cursor = config.quote?.show_cursor_blink !== false
      ? '<span class="quote__cursor">|</span>'
      : '';

    const apply = () => {
      textEl.innerHTML = `"${quote.text}"${cursor}`;
      authorEl.textContent = quote.author ? `— ${quote.author}` : '';
      authorEl.classList.remove('visible');
      setTimeout(() => authorEl.classList.add('visible'), 200);
    };

    if (!animate) {
      apply();
      return;
    }

    textEl.classList.add('quote__text--out');
    setTimeout(() => {
      textEl.classList.remove('quote__text--out');
      apply();
      textEl.classList.add('quote__text--in');
      setTimeout(() => textEl.classList.remove('quote__text--in'), 400);
    }, 400);
  }

  function nextQuote() {
    if (!quotes.length) return;
    index = (index + 1) % quotes.length;
    showQuote(quotes[index], true);
  }

  async function loadQuotes() {
    try {
      const data = await fetchJson('/api/quotes');
      quotes = Array.isArray(data) ? data : [];
    } catch {
      quotes = [];
    }
  }

  function init(cfg) {
    config = cfg;
    loadQuotes().then(() => {
      if (quotes.length) {
        index = Math.floor(Math.random() * quotes.length);
        showQuote(quotes[index], false);
      }

      const mins = config.quote?.rotate_every_mins || 10;
      if (mins > 0) {
        setInterval(nextQuote, mins * 60 * 1000);
      }
    });
  }

  return { init };
})();

window.Quotes = Quotes;
