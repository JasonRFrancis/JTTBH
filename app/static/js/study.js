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
        // Every N days (perDay is negative: -2 = every other day, -7 = weekly)
        const n = Math.abs(perDay);
        if (days % n !== 0) return [];
        const idx = Math.floor(days / n);
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

}());
