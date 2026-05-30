'use strict';

// TMDB search autocomplete on the Add Media form.
// Only fires for show/movie kinds; books and podcasts skip it.

(function () {
  const form         = document.querySelector('.media-add-form');
  const searchBase   = form ? form.dataset.searchUrl : '';
  const kindSel      = document.getElementById('add-kind');
  const titleInput   = document.getElementById('add-title');
  const creatorInput = document.getElementById('add-creator');
  const extIdInput   = document.getElementById('add-external-id');
  const coverInput   = document.getElementById('add-cover-url');
  const feedField    = document.querySelector('.field--podcast');
  const feedInput    = document.getElementById('add-feed');
  const suggestions  = document.querySelector('.search-suggestions');

  if (!kindSel || !titleInput) return;

  function searchableKind() {
    return kindSel.value === 'show' || kindSel.value === 'movie';
  }

  function updateFeedVisibility() {
    if (feedField) feedField.hidden = kindSel.value !== 'podcast';
    // podcast uses the feed URL input as external_id instead of hidden field
    if (feedInput && extIdInput) {
      extIdInput.disabled = kindSel.value === 'podcast';
    }
  }

  kindSel.addEventListener('change', () => {
    clearSuggestions();
    extIdInput.value = '';
    coverInput.value = '';
    updateFeedVisibility();
  });
  updateFeedVisibility();

  function clearSuggestions() {
    suggestions.innerHTML = '';
    suggestions.hidden = true;
  }

  function showSuggestions(results) {
    suggestions.innerHTML = '';
    if (!results.length) { suggestions.hidden = true; return; }
    results.forEach(r => {
      const li = document.createElement('li');
      li.textContent = r.title + (r.year ? ` (${r.year})` : '');
      li.addEventListener('mousedown', e => {
        e.preventDefault();
        titleInput.value   = r.title;
        extIdInput.value   = r.id;
        coverInput.value   = r.cover_url;
        if (r.kind === 'show' || r.kind === 'movie') kindSel.value = r.kind;
        if (creatorInput && r.creator) creatorInput.value = r.creator;
        clearSuggestions();
      });
      suggestions.appendChild(li);
    });
    suggestions.hidden = false;
  }

  let timer = null;
  titleInput.addEventListener('input', () => {
    if (!searchableKind()) { clearSuggestions(); return; }
    clearTimeout(timer);
    const q = titleInput.value.trim();
    if (q.length < 2) { clearSuggestions(); return; }
    timer = setTimeout(() => {
      const kind = kindSel.value === 'show' ? 'show' : kindSel.value === 'movie' ? 'movie' : 'any';
      const url = `${searchBase}?q=${encodeURIComponent(q)}&kind=${kind}`;
      fetch(url)
        .then(r => r.json())
        .then(showSuggestions)
        .catch(() => clearSuggestions());
    }, 300);
  });

  titleInput.addEventListener('blur', () => setTimeout(clearSuggestions, 150));
}());
