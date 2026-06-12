/* bookmark.js — drag-and-drop, AJAX actions, inline edit */
'use strict';

const BASE = window.location.pathname.replace(/\/(index|archive|category\/.*)$/, '');

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------

function postJSON(path, data) {
  return fetch(BASE + path, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest',
    },
    body: JSON.stringify(data),
  }).then(r => r.json());
}

function postForm(path, data) {
  const fd = new FormData();
  for (const [k, v] of Object.entries(data)) fd.append(k, v);
  return fetch(BASE + path, {
    method: 'POST',
    headers: { 'X-Requested-With': 'XMLHttpRequest' },
    body: fd,
  }).then(r => r.json());
}

// ---------------------------------------------------------------------------
// Hover actions: favorite, archive, edit
// ---------------------------------------------------------------------------

function initRowActions() {
  document.addEventListener('click', e => {
    const btn = e.target.closest('button');
    if (!btn) return;

    // ---- Favorite ----
    if (btn.classList.contains('bm-btn-fav')) {
      const bmId = btn.dataset.bmId;
      postJSON(`/favorite/post/${bmId}`, {}).then(res => {
        if (res.status !== 'ok') return;
        const row = btn.closest('.bm-row');
        btn.dataset.active = res.favorite ? '1' : '0';
        row.classList.toggle('bm-row--fav', res.favorite);
      });
    }

    // ---- Archive ----
    if (btn.classList.contains('bm-btn-archive')) {
      const bmId = btn.dataset.bmId;
      const row  = btn.closest('.bm-row');
      row.style.opacity = '0.4';
      postJSON(`/archive/post/${bmId}`, {}).then(res => {
        if (res.status !== 'ok') { row.style.opacity = ''; return; }
        if (res.archived) {
          row.remove();
        } else {
          row.style.opacity = '';
        }
      });
    }

    // ---- Unarchive (archive page) ----
    if (btn.classList.contains('bm-btn-unarchive')) {
      const bmId = btn.dataset.bmId;
      const row  = btn.closest('.bm-row');
      row.style.opacity = '0.4';
      postJSON(`/archive/post/${bmId}`, {}).then(res => {
        if (res.archived === false) row.remove();
        else row.style.opacity = '';
      });
    }

    // ---- Edit (open panel) ----
    if (btn.classList.contains('bm-btn-edit')) {
      const row   = btn.closest('.bm-row');
      const panel = row.querySelector('.bm-edit-row');
      if (panel) panel.hidden = !panel.hidden;
    }

    // ---- Edit save ----
    if (btn.classList.contains('bm-edit-save')) {
      const bmId  = btn.dataset.bmId;
      const row   = btn.closest('.bm-row');
      const title = row.querySelector('.bm-edit-title').value.trim();
      const tags  = row.querySelector('.bm-edit-tags').value.trim();
      const notes = row.querySelector('.bm-edit-notes').value.trim();
      postForm(`/update/post/${bmId}`, { title, tags, notes }).then(res => {
        if (res.status !== 'ok') return;
        const link = row.querySelector('.bm-link');
        if (link && res.title) link.textContent = res.title;
        row.querySelector('.bm-edit-row').hidden = true;
      });
    }

    // ---- Edit cancel ----
    if (btn.classList.contains('bm-edit-cancel')) {
      btn.closest('.bm-edit-row').hidden = true;
    }

    // ---- Remove from category (category detail page) ----
    if (btn.classList.contains('bm-btn-remove')) {
      const bmId  = btn.dataset.bmId;
      const catId = btn.dataset.catId;
      const row   = btn.closest('.bm-row');
      row.style.opacity = '0.4';
      fetch(`${BASE}/category/item/remove/post/${catId}/${bmId}`, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      }).then(r => r.json()).then(res => {
        if (res.status === 'ok') row.remove();
        else row.style.opacity = '';
      });
    }

    // ---- Category edit button ----
    if (btn.classList.contains('bm-card-edit-btn')) {
      const card  = btn.closest('.bm-card');
      const panel = card.querySelector('.bm-card-edit-panel');
      if (panel) panel.hidden = !panel.hidden;
    }

    // ---- Category edit cancel ----
    if (btn.classList.contains('bm-card-edit-cancel')) {
      btn.closest('.bm-card-edit-panel').hidden = true;
    }
  });
}

// ---------------------------------------------------------------------------
// Drag-and-drop: category cards
// ---------------------------------------------------------------------------

function initCardDrag() {
  const grid = document.getElementById('bm-grid');
  if (!grid) return;

  let dragCard = null;

  grid.addEventListener('dragstart', e => {
    const card = e.target.closest('.bm-card[draggable]');
    if (!card || card.dataset.catId === '__uncat__') { e.preventDefault(); return; }
    if (e.target.closest('.bm-list')) { return; } // let row drag handle it
    dragCard = card;
    card.classList.add('bm-dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/card-id', card.dataset.catId);
  });

  grid.addEventListener('dragend', e => {
    if (dragCard) { dragCard.classList.remove('bm-dragging'); dragCard = null; }
    grid.querySelectorAll('.bm-drag-over').forEach(el => el.classList.remove('bm-drag-over'));
  });

  grid.addEventListener('dragover', e => {
    const card = e.target.closest('.bm-card');
    if (!card || !dragCard || card === dragCard) return;
    if (e.target.closest('.bm-list')) return;
    e.preventDefault();
    grid.querySelectorAll('.bm-card.bm-drag-over').forEach(c => c.classList.remove('bm-drag-over'));
    card.classList.add('bm-drag-over');
  });

  grid.addEventListener('drop', e => {
    const target = e.target.closest('.bm-card');
    if (!target || !dragCard || target === dragCard) return;
    if (e.target.closest('.bm-list')) return;
    e.preventDefault();
    target.classList.remove('bm-drag-over');

    // Insert before or after based on pointer position
    const rect = target.getBoundingClientRect();
    const after = e.clientX > rect.left + rect.width / 2;
    if (after) {
      target.after(dragCard);
    } else {
      target.before(dragCard);
    }

    saveCategoryOrder();
  });
}

function saveCategoryOrder() {
  const cards = document.querySelectorAll('#bm-grid .bm-card[data-cat-id]');
  const order = [];
  cards.forEach((card, i) => {
    if (card.dataset.catId !== '__uncat__') {
      order.push({ categoryID: card.dataset.catId, position: i });
    }
  });
  postJSON('/category/reorder/post', order);
}

// ---------------------------------------------------------------------------
// Drag-and-drop: bookmark rows within a card
// ---------------------------------------------------------------------------

function initRowDrag() {
  document.addEventListener('dragstart', e => {
    const row = e.target.closest('.bm-row[draggable]');
    if (!row) return;
    const list = row.closest('.bm-list[data-reorderable]');
    if (!list) { e.preventDefault(); return; }
    row.classList.add('bm-dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/bm-id', row.dataset.bmId);
    e.dataTransfer.setData('text/cat-id', list.dataset.catId);
  });

  document.addEventListener('dragend', e => {
    const row = e.target.closest('.bm-row');
    if (row) row.classList.remove('bm-dragging');
    document.querySelectorAll('.bm-drag-over-top, .bm-drag-over-bottom')
      .forEach(el => { el.classList.remove('bm-drag-over-top', 'bm-drag-over-bottom'); });
  });

  document.addEventListener('dragover', e => {
    const row = e.target.closest('.bm-row');
    if (!row || !row.closest('.bm-list[data-reorderable]')) return;
    if (row.classList.contains('bm-dragging')) return;
    e.preventDefault();
    document.querySelectorAll('.bm-drag-over-top, .bm-drag-over-bottom')
      .forEach(el => { el.classList.remove('bm-drag-over-top', 'bm-drag-over-bottom'); });
    const rect  = row.getBoundingClientRect();
    const after = e.clientY > rect.top + rect.height / 2;
    row.classList.add(after ? 'bm-drag-over-bottom' : 'bm-drag-over-top');
  });

  document.addEventListener('drop', e => {
    const targetRow = e.target.closest('.bm-row');
    if (!targetRow) return;
    const list = targetRow.closest('.bm-list[data-reorderable]');
    if (!list) return;
    e.preventDefault();

    const bmId  = e.dataTransfer.getData('text/bm-id');
    const catId = e.dataTransfer.getData('text/cat-id');
    if (!bmId || catId !== list.dataset.catId) return;

    const srcRow = list.querySelector(`.bm-row[data-bm-id="${bmId}"]`);
    if (!srcRow || srcRow === targetRow) return;

    const rect  = targetRow.getBoundingClientRect();
    const after = e.clientY > rect.top + targetRow.offsetHeight / 2;
    if (after) targetRow.after(srcRow);
    else targetRow.before(srcRow);

    targetRow.classList.remove('bm-drag-over-top', 'bm-drag-over-bottom');
    saveRowOrder(list);
  });
}

function saveRowOrder(list) {
  const catId = list.dataset.catId;
  const rows  = list.querySelectorAll('.bm-row[data-bm-id]');
  const order = Array.from(rows).map((r, i) => ({ bookmarkID: r.dataset.bmId, position: i }));
  postJSON(`/category/item/reorder/post/${catId}`, order);
}

// ---------------------------------------------------------------------------
// Sort
// ---------------------------------------------------------------------------

function renderRow(bm, catId) {
  const reorderable = catId && catId !== '__favorites__' && catId !== '__uncat__';
  const li = document.createElement('li');
  li.className = 'bm-row' + (bm.favorite ? ' bm-row--fav' : '');
  li.dataset.bmId = bm.bookmarkID;
  if (reorderable) {
    li.draggable = true;
    li.dataset.position = '0';
  }

  const title = bm.title || bm.url;
  const favActive = bm.favorite ? '1' : '0';

  li.innerHTML =
    `<a href="${escHtml(bm.url)}" target="_blank" rel="noopener noreferrer" class="bm-link">${escHtml(title)}</a>` +
    `<span class="bm-actions">` +
      `<button class="bm-btn-fav" title="${bm.favorite ? 'Unfavorite' : 'Favorite'}" data-bm-id="${bm.bookmarkID}" data-active="${favActive}">★</button>` +
      `<button class="bm-btn-archive" title="Archive" data-bm-id="${bm.bookmarkID}">⊘</button>` +
      `<button class="bm-btn-edit"    title="Edit"    data-bm-id="${bm.bookmarkID}">✎</button>` +
      (catId && catId !== '__favorites__' && catId !== '__uncat__'
        ? `<button class="bm-btn-remove" title="Remove from category" data-cat-id="${catId}" data-bm-id="${bm.bookmarkID}">✕</button>`
        : '') +
    `</span>` +
    `<div class="bm-edit-row" hidden>` +
      `<input type="text" class="bm-edit-title" value="${escAttr(bm.title || '')}" placeholder="Title">` +
      `<input type="text" class="bm-edit-tags"  value="${escAttr(bm.tags  || '')}" placeholder="Tags">` +
      `<textarea class="bm-edit-notes" placeholder="Notes">${escHtml(bm.notes || '')}</textarea>` +
      `<span class="bm-edit-row-actions">` +
        `<button class="bm-edit-save" data-bm-id="${bm.bookmarkID}">Save</button>` +
        `<button class="bm-edit-cancel">Cancel</button>` +
      `</span>` +
    `</div>`;

  return li;
}

function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function escAttr(s) {
  return String(s).replace(/&/g,'&amp;').replace(/"/g,'&quot;');
}

function initSort() {
  document.addEventListener('change', e => {
    const sel = e.target.closest('.bm-sort');
    if (!sel) return;
    const catId = sel.dataset.catId;
    const sort  = sel.value;
    const card  = sel.closest('.bm-card');
    const list  = card && card.querySelector('.bm-list');
    if (!list) return;

    fetch(`${BASE}/items/json?cat=${encodeURIComponent(catId)}&sort=${encodeURIComponent(sort)}`, {
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
    })
      .then(r => r.json())
      .then(data => {
        if (!data.items) return;
        list.innerHTML = '';
        if (data.items.length === 0) {
          const li = document.createElement('li');
          li.className = 'bm-empty';
          li.textContent = 'No bookmarks.';
          list.appendChild(li);
        } else {
          data.items.forEach(bm => list.appendChild(renderRow(bm, catId)));
        }
        // Disable drag-reorder while a non-manual sort is active
        if (catId !== '__favorites__' && catId !== '__uncat__') {
          list.dataset.reorderable = sort === 'manual' ? '1' : '0';
        }
      });
  });
}

// ---------------------------------------------------------------------------
// Archive page: select all
// ---------------------------------------------------------------------------

function initSelectAll() {
  const selectAll = document.getElementById('select-all');
  if (!selectAll) return;
  selectAll.addEventListener('change', () => {
    document.querySelectorAll('input[name="bookmark_id"]')
      .forEach(cb => { cb.checked = selectAll.checked; });
  });
}

// ---------------------------------------------------------------------------
// Tag chips
// ---------------------------------------------------------------------------

function initTagChips() {
  document.querySelectorAll('.bm-tag-chips-field').forEach(field => {
    const hidden = field.querySelector('input[type="hidden"].bm-tags-hidden');
    const input = field.querySelector('.bm-tag-chips-input');
    const chipList = field.querySelector('.bm-tag-chips-list');
    if (!hidden || !input || !chipList) return;

    function renderChips(tags) {
      chipList.innerHTML = '';
      tags.forEach(tag => {
        if (!tag.trim()) return;
        const chip = document.createElement('span');
        chip.className = 'bm-tag-chip-item';
        chip.textContent = tag.trim();
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'bm-tag-chip-remove';
        btn.textContent = '×';
        btn.addEventListener('click', () => {
          const current = getTags();
          updateTags(current.filter(t => t !== tag.trim()));
        });
        chip.appendChild(btn);
        chipList.appendChild(chip);
      });
    }

    function getTags() {
      return hidden.value ? hidden.value.split(',').map(t => t.trim()).filter(Boolean) : [];
    }

    function updateTags(tags) {
      const unique = [...new Set(tags.map(t => t.replace(/\s+/g, '').trim()).filter(Boolean))];
      hidden.value = unique.join(',');
      renderChips(unique);
    }

    updateTags(getTags());

    input.addEventListener('keydown', e => {
      if (e.key === ',' || e.key === ' ' || e.key === 'Enter') {
        e.preventDefault();
        const val = input.value.replace(/[, ]+/g, '').trim();
        if (val) {
          const tags = getTags();
          if (!tags.includes(val)) tags.push(val);
          updateTags(tags);
          input.value = '';
        }
      }
      if (e.key === 'Backspace' && !input.value) {
        const tags = getTags();
        if (tags.length) updateTags(tags.slice(0, -1));
      }
    });

    input.addEventListener('blur', () => {
      const val = input.value.replace(/[, ]+/g, '').trim();
      if (val) {
        const tags = getTags();
        if (!tags.includes(val)) tags.push(val);
        updateTags(tags);
        input.value = '';
      }
    });
  });
}

// ---------------------------------------------------------------------------
// Summarize
// ---------------------------------------------------------------------------

function initSummarize() {
  document.addEventListener('click', e => {
    const btn = e.target.closest('.btn-summarize');
    if (!btn) return;
    const url = btn.dataset.url;
    const id = btn.dataset.bookmarkId;
    const output = document.getElementById('summary-' + id);
    if (!output) return;
    btn.disabled = true;
    btn.textContent = 'Summarizing…';
    fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(r => r.json())
      .then(data => {
        if (data.error) {
          output.textContent = 'Error: ' + data.error;
        } else {
          const s = data.summary;
          output.innerHTML =
            '<div class="bm-summary-section"><strong>In brief:</strong> ' + s.one + '</div>' +
            '<div class="bm-summary-section"><strong>Summary:</strong> ' + s.three + '</div>' +
            '<details class="bm-summary-long"><summary>Full summary</summary>' + s.long + '</details>';
        }
        output.hidden = false;
        btn.textContent = '✨ Summarize';
        btn.disabled = false;
      })
      .catch(() => {
        output.textContent = 'Failed to load summary.';
        output.hidden = false;
        btn.textContent = '✨ Summarize';
        btn.disabled = false;
      });
  });
}

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------

initRowActions();
initCardDrag();
initRowDrag();
initSelectAll();
initSort();
initTagChips();
initSummarize();
