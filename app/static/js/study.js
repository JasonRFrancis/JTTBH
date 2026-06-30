/* study.js — subscription edit (live preview + start-item dropdown) + schedule search */

(function () {

  /* ════════════════════════════════════════════════════════════
     SUBSCRIPTION EDIT PAGE
     Requires: <script id="study-sub-data" type="application/json">
  ════════════════════════════════════════════════════════════ */

  const dataEl = document.getElementById('study-sub-data');
  if (dataEl) {
    const data       = JSON.parse(dataEl.textContent);
    const ALL        = data.sources;   // [{sourceID, title, author, category, order_by}]
    const TODAY      = data.today;     // 'YYYY-MM-DD'
    const INIT_OFF   = data.startOffset;

    let selectedSourceId = '';        // sourceID of the chosen start item ('' = beginning)

    /* ── Helpers ─────────────────────────────────────────────── */

    function esc(str) {
      return String(str)
        .replace(/&/g,'&amp;').replace(/</g,'&lt;')
        .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }

    function fmtDate(iso) {
      const d = new Date(iso + 'T00:00:00');
      return d.toLocaleDateString('en-US', {weekday:'short', month:'short', day:'numeric'});
    }

    function addDays(iso, n) {
      const d = new Date(iso + 'T00:00:00');
      d.setDate(d.getDate() + n);
      return d.toISOString().slice(0, 10);
    }

    function daysDiff(isoA, isoB) {
      return Math.round((new Date(isoB + 'T00:00:00') - new Date(isoA + 'T00:00:00')) / 86400000);
    }

    function getSelected(cbClass) {
      return new Set(
        Array.from(document.querySelectorAll('.' + cbClass + ':checked'))
          .map(cb => cb.value.toLowerCase())
      );
    }

    function syncHidden(cbClass, hiddenId) {
      const vals = Array.from(document.querySelectorAll('.' + cbClass + ':checked'))
        .map(cb => cb.value);
      const h = document.getElementById(hiddenId);
      if (h) h.value = vals.join(', ');
    }

    /* ── Filtering (mirrors Python get_filtered_sources) ─────── */

    function getBaseFiltered() {
      let r = [...ALL];

      const authors = getSelected('author-cb');
      if (authors.size) r = r.filter(s => s.author && authors.has(s.author.toLowerCase()));

      const cats = getSelected('category-cb');
      if (cats.size) r = r.filter(s => s.category && cats.has(s.category.toLowerCase()));

      if ((document.getElementById('filter_has_audio') || {}).checked) {
        r = r.filter(s => s.has_audio);
      }

      const titleQ = ((document.getElementById('filter_title') || {}).value || '').toLowerCase().trim();
      if (titleQ) r = r.filter(s => s.title && s.title.toLowerCase().includes(titleQ));

      const authorQ = ((document.getElementById('filter_author_text') || {}).value || '').toLowerCase().trim();
      if (authorQ) r = r.filter(s => s.author && s.author.toLowerCase().includes(authorQ));

      const categoryQ = ((document.getElementById('filter_category_text') || {}).value || '').toLowerCase().trim();
      if (categoryQ) r = r.filter(s => s.category && s.category.toLowerCase().includes(categoryQ));

      const subtitleQ = ((document.getElementById('filter_subtitle_text') || {}).value || '').toLowerCase().trim();
      if (subtitleQ) r = r.filter(s => s.subtitle && s.subtitle.toLowerCase().includes(subtitleQ));

      const sort = (document.querySelector('input[name="sort_order"]:checked') || {}).value || 'natural';
      if (sort === 'newest') r.sort((a, b) => b.order_by - a.order_by);
      else if (sort === 'oldest') r.sort((a, b) => a.order_by - b.order_by);

      const lim = parseInt((document.getElementById('limit_count') || {}).value);
      if (lim > 0) r = r.slice(0, lim);

      return r;
    }

    /* ── Rate-mode cycling (mirrors Python sources_for_date) ─── */

    function sourcesForDate(filtered, perDay, startIso, repeatOn, targetIso) {
      if (!filtered.length || !startIso) return [];
      const days = daysDiff(startIso, targetIso);
      if (days < 0) return [];

      if (perDay > 0) {
        // N items per day
        if (!repeatOn) {
          const si = days * perDay;
          if (si >= filtered.length) return [];
          return filtered.slice(si, si + perDay);
        }
        const si = (days * perDay) % filtered.length;
        const out = [];
        for (let i = 0; i < perDay; i++) out.push(filtered[(si + i) % filtered.length]);
        return out;
      } else {
        // Alternating days
        // -2 = even days: item on days 0, 2, 4… (starts on start_date)
        // -1 = odd days:  item on days 1, 3, 5… (starts one day after start_date)
        let idx;
        if (perDay === -2) {
          if (days % 2 !== 0) return [];
          idx = Math.floor(days / 2);
        } else if (perDay === -1) {
          if (days % 2 !== 1) return [];
          idx = Math.floor((days - 1) / 2);
        } else if (perDay === -7) {
          if (days % 7 !== 0) return [];
          idx = Math.floor(days / 7);
        } else {
          return [];
        }
        if (!repeatOn) {
          if (idx >= filtered.length) return [];
          return [filtered[idx]];
        }
        return [filtered[idx % filtered.length]];
      }
    }

    /* ── Start-item dropdown ─────────────────────────────────── */

    const searchInput   = document.getElementById('start-item-search');
    const dropdownList  = document.getElementById('start-item-list');
    const offsetHidden  = document.getElementById('start_offset_hidden');
    const selectedLabel = document.getElementById('start-item-label');
    const clearBtn      = document.getElementById('start-item-clear');

    function labelFor(idx, s) {
      return s ? `#${idx + 1} — ${esc(s.title)}${s.author ? ' · ' + esc(s.author) : ''}` : 'Beginning (item 1)';
    }

    function applySelection(sourceId, offset) {
      selectedSourceId = sourceId;
      if (offsetHidden)  offsetHidden.value = offset;
      if (selectedLabel) selectedLabel.innerHTML = offset === 0
        ? 'Beginning (item 1)'
        : (() => { const b = getBaseFiltered(); const s = b[offset]; return s ? labelFor(offset, s) : 'Beginning (item 1)'; })();
      hideDropdown();
      if (searchInput) searchInput.value = '';
      updatePreview();
    }

    function hideDropdown() { if (dropdownList) dropdownList.classList.add('hidden'); }
    function showDropdown() { if (dropdownList) dropdownList.classList.remove('hidden'); }

    function populateDropdown(q) {
      if (!dropdownList) return;
      const base = getBaseFiltered();
      const lq = q.toLowerCase();
      const matches = lq
        ? base.filter(s => (s.title + ' ' + s.author).toLowerCase().includes(lq)).slice(0, 80)
        : base.slice(0, 80);

      dropdownList.innerHTML = '';

      if (!lq || 'beginning'.startsWith(lq)) {
        const li = document.createElement('li');
        li.className = 'start-item-option' + (!selectedSourceId ? ' start-item-option--selected' : '');
        li.setAttribute('role', 'option');
        li.textContent = 'Beginning (item 1)';
        li.addEventListener('mousedown', e => { e.preventDefault(); applySelection('', 0); });
        dropdownList.appendChild(li);
      }

      matches.forEach(s => {
        const idx = base.indexOf(s);
        const li = document.createElement('li');
        li.className = 'start-item-option' + (s.sourceID === selectedSourceId ? ' start-item-option--selected' : '');
        li.setAttribute('role', 'option');
        li.innerHTML = `<span class="si-num">#${idx + 1}</span> ${esc(s.title)}${s.author ? '<span class="si-author"> · ' + esc(s.author) + '</span>' : ''}`;
        li.addEventListener('mousedown', e => { e.preventDefault(); applySelection(s.sourceID, idx); });
        dropdownList.appendChild(li);
      });

      if (matches.length === 80) {
        const li = document.createElement('li');
        li.className = 'start-item-more';
        li.textContent = 'Type to narrow results…';
        dropdownList.appendChild(li);
      }

      showDropdown();
    }

    if (searchInput) {
      searchInput.addEventListener('focus', () => populateDropdown(''));
      searchInput.addEventListener('input', () => populateDropdown(searchInput.value));
      searchInput.addEventListener('blur',  () => setTimeout(hideDropdown, 150));
    }

    if (clearBtn) clearBtn.addEventListener('click', () => applySelection('', 0));

    /* ── Preview ─────────────────────────────────────────────── */

    function updatePreview() {
      const out = document.getElementById('preview-output');
      if (!out) return;

      if ((document.getElementById('use_personal_schedule') || {}).checked) {
        out.innerHTML = '<p class="preview-notice">Preview not available in personal schedule mode — use the Schedule page to assign specific dates.</p>';
        return;
      }

      const base       = getBaseFiltered();
      const offset     = parseInt((offsetHidden || {}).value) || 0;
      const filtered   = offset > 0 ? base.slice(offset) : base;

      // Update filter count display
      const countEl = document.getElementById('filter-count');
      if (countEl) countEl.textContent = `Showing ${base.length} of ${ALL.length}`;

      if (!filtered.length) {
        out.innerHTML = '<p class="preview-notice">No items match the current filters.</p>';
        return;
      }

      const perDay    = parseInt((document.getElementById('per_day') || {}).value) || 1;
      const startIso  = (document.getElementById('start_date') || {}).value || TODAY;
      const repeatOn  = (document.getElementById('repeat') || {}).checked ? 1 : 0;

      const rows = [];
      for (let i = 0; i < 30; i++) {
        const dateIso = addDays(TODAY, i);
        const items   = sourcesForDate(filtered, perDay, startIso, repeatOn, dateIso);
        items.forEach(s => {
          rows.push(
            `<li class="preview-row">` +
            `<span class="preview-date">${fmtDate(dateIso)}</span>` +
            `<span class="preview-item-title">${esc(s.title)}` +
            (s.author ? `<span class="preview-author"> — ${esc(s.author)}</span>` : '') +
            `</span></li>`
          );
        });
      }

      if (!rows.length) {
        out.innerHTML = '<p class="preview-notice">Nothing in the next 30 days — check the start date.</p>';
        return;
      }

      out.innerHTML =
        `<p class="preview-meta">${filtered.length} item${filtered.length === 1 ? '' : 's'} in rotation</p>` +
        `<ul class="preview-list-live" role="list">${rows.join('')}</ul>`;
    }

    /* ── Wire all controls ───────────────────────────────────── */

    function onFilterChange() {
      syncHidden('author-cb', 'filter_author_hidden');
      syncHidden('category-cb', 'filter_category_hidden');

      // Re-resolve selected item position after filter change
      const base = getBaseFiltered();
      if (!selectedSourceId) {
        if (offsetHidden) offsetHidden.value = 0;
        if (selectedLabel) selectedLabel.textContent = 'Beginning (item 1)';
      } else {
        const idx = base.findIndex(s => s.sourceID === selectedSourceId);
        if (idx === -1) {
          applySelection('', 0);
          return;
        }
        if (offsetHidden)  offsetHidden.value = idx;
        if (selectedLabel) selectedLabel.innerHTML = labelFor(idx, base[idx]);
      }
      updatePreview();
    }

    // Checklist wiring (search filter + clear + change → onFilterChange)
    function wireChecklist(cbClass, hiddenId, searchId, clearTarget) {
      const items = document.querySelectorAll('.' + cbClass);
      if (!items.length) return;
      items.forEach(cb => cb.addEventListener('change', onFilterChange));
      syncHidden(cbClass, hiddenId);

      const srch = document.getElementById(searchId);
      if (srch) {
        srch.addEventListener('input', function () {
          const q = this.value.toLowerCase();
          items.forEach(cb => {
            const li = cb.closest('li');
            if (li) li.style.display = cb.value.toLowerCase().includes(q) ? '' : 'none';
          });
        });
      }
      const clr = document.querySelector('[data-target="' + clearTarget + '"]');
      if (clr) clr.addEventListener('click', () => {
        items.forEach(cb => { cb.checked = false; });
        onFilterChange();
      });
    }

    wireChecklist('author-cb',   'filter_author_hidden',   'author-search',   'author');
    wireChecklist('category-cb', 'filter_category_hidden', 'category-search', 'category');

    ['per_day', 'start_date', 'limit_count'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.addEventListener('change', onFilterChange);
    });

    const hasAudioCb = document.getElementById('filter_has_audio');
    if (hasAudioCb) hasAudioCb.addEventListener('change', onFilterChange);

    const titleInput = document.getElementById('filter_title');
    if (titleInput) titleInput.addEventListener('input', onFilterChange);

    const authorTextInput = document.getElementById('filter_author_text');
    if (authorTextInput) authorTextInput.addEventListener('input', onFilterChange);

    const categoryTextInput = document.getElementById('filter_category_text');
    if (categoryTextInput) categoryTextInput.addEventListener('input', onFilterChange);

    const subtitleTextInput = document.getElementById('filter_subtitle_text');
    if (subtitleTextInput) subtitleTextInput.addEventListener('input', onFilterChange);
    document.querySelectorAll('input[name="sort_order"]').forEach(r => r.addEventListener('change', onFilterChange));
    const repeatCb = document.getElementById('repeat');
    if (repeatCb) repeatCb.addEventListener('change', updatePreview);
    const schedCb = document.getElementById('use_personal_schedule');
    if (schedCb) schedCb.addEventListener('change', updatePreview);

    // Initialise start-item selection from server-provided offset
    (function () {
      const base = getBaseFiltered();
      if (INIT_OFF > 0 && INIT_OFF < base.length) {
        const s = base[INIT_OFF];
        selectedSourceId       = s.sourceID;
        if (offsetHidden)  offsetHidden.value        = INIT_OFF;
        if (selectedLabel) selectedLabel.innerHTML    = labelFor(INIT_OFF, s);
      } else {
        if (selectedLabel) selectedLabel.textContent  = 'Beginning (item 1)';
      }
    }());

    updatePreview();
  }

  /* ════════════════════════════════════════════════════════════
     SCHEDULE PAGE
  ════════════════════════════════════════════════════════════ */

  const scheduleSearch = document.getElementById('schedule-search');
  const showScheduled  = document.getElementById('show-scheduled-only');
  const scheduleItems  = document.querySelectorAll('.schedule-item');

  function filterSchedule() {
    const q = scheduleSearch ? scheduleSearch.value.toLowerCase() : '';
    const onlyScheduled = showScheduled ? showScheduled.checked : false;
    scheduleItems.forEach(item => {
      const ok = (!q || (item.dataset.title + ' ' + item.dataset.author).includes(q))
              && (!onlyScheduled || item.dataset.scheduled === '1');
      item.style.display = ok ? '' : 'none';
    });
  }

  if (scheduleSearch) scheduleSearch.addEventListener('input', filterSchedule);
  if (showScheduled)  showScheduled.addEventListener('change', filterSchedule);

  /* ── Study index: AJAX completion toggle ─────────────────── */
  (function() {
    document.addEventListener('click', function(e) {
      const btn = e.target.closest('.complete-btn[data-source-id]');
      if (!btn) return;
      e.preventDefault();

      const body = new URLSearchParams({ date: btn.dataset.date });
      fetch(btn.dataset.url, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest', 'Content-Type': 'application/x-www-form-urlencoded' },
        body: body.toString()
      })
      .then(r => r.json())
      .then(data => {
        if (data.status !== 'ok') return;
        const done = data.done;
        const li = btn.closest('.source-item');
        btn.classList.toggle('complete-btn--done', done);
        btn.setAttribute('aria-label', done ? 'Mark incomplete' : 'Mark complete');
        btn.innerHTML = done ? '&#10003;' : '&#9675;';
        if (li) li.classList.toggle('source-item--done', done);
      })
      .catch(() => {});
    });
  }());

  /* ── Study index: subscription drag-to-reorder ────────────── */
  (function() {
    const sections = [...document.querySelectorAll('.study-collection-section[data-sub-id]')];
    if (sections.length < 2) return;
    const container = sections[0].parentElement;
    let dragging = null;

    sections.forEach(sec => {
      sec.addEventListener('dragstart', e => {
        dragging = sec;
        sec.classList.add('study-collection-section--dragging');
        e.dataTransfer.effectAllowed = 'move';
      });
      sec.addEventListener('dragend', () => {
        sec.classList.remove('study-collection-section--dragging');
        document.querySelectorAll('.study-collection-section--drag-over').forEach(el => el.classList.remove('study-collection-section--drag-over'));
        dragging = null;
      });
      sec.addEventListener('dragover', e => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        document.querySelectorAll('.study-collection-section--drag-over').forEach(el => el.classList.remove('study-collection-section--drag-over'));
        if (sec !== dragging) sec.classList.add('study-collection-section--drag-over');
      });
      sec.addEventListener('drop', e => {
        e.preventDefault();
        sec.classList.remove('study-collection-section--drag-over');
        if (!dragging || dragging === sec) return;
        const all = [...container.querySelectorAll('.study-collection-section[data-sub-id]')];
        const fromIdx = all.indexOf(dragging), toIdx = all.indexOf(sec);
        if (fromIdx < toIdx) sec.after(dragging); else sec.before(dragging);
        const updated = [...container.querySelectorAll('.study-collection-section[data-sub-id]')];
        const payload = updated.map((el, i) => ({ subscriptionID: el.dataset.subId, position: i }));
        const username = window.location.pathname.split('/')[1];
        fetch('/' + username + '/study/subscription/reorder/post', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
          body: JSON.stringify(payload)
        }).catch(() => {});
      });
    });
  }());

}());
