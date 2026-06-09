(function () {
  'use strict';

  const BASE = window.location.pathname.replace(/\/(index|detail\/[^/]+|add|edit\/[^/]+|search|archive)$/, '');

  function postJSON(path, data) {
    return fetch(BASE + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
      body: JSON.stringify(data),
    }).then(r => r.json());
  }

  function postForm(path, formData) {
    return fetch(BASE + path, {
      method: 'POST',
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      body: formData,
    }).then(r => r.json());
  }

  // ----------------------------------------------------------------
  // Index: PDF selection toggle
  // ----------------------------------------------------------------
  const pdfSelectBtn = document.getElementById('pdf-select-btn');
  const pdfToolbar = document.getElementById('pdf-toolbar');
  const pdfCancel = document.getElementById('pdf-cancel');
  const pdfCount = document.getElementById('pdf-count');

  if (pdfSelectBtn) {
    const checkboxLabels = document.querySelectorAll('.recipe-checkbox');
    const checkboxes = document.querySelectorAll('.pdf-checkbox');

    function updateCount() {
      const n = document.querySelectorAll('.pdf-checkbox:checked').length;
      pdfCount.textContent = n === 1 ? '1 selected' : `${n} selected`;
    }

    pdfSelectBtn.addEventListener('click', () => {
      checkboxLabels.forEach(l => l.hidden = false);
      pdfToolbar.hidden = false;
      pdfSelectBtn.closest('.pdf-select-toggle').hidden = true;
    });

    if (pdfCancel) {
      pdfCancel.addEventListener('click', () => {
        checkboxes.forEach(cb => { cb.checked = false; });
        checkboxLabels.forEach(l => l.hidden = true);
        pdfToolbar.hidden = true;
        pdfSelectBtn.closest('.pdf-select-toggle').hidden = false;
        updateCount();
      });
    }

    checkboxes.forEach(cb => cb.addEventListener('change', updateCount));
  }

  // ----------------------------------------------------------------
  // Drag-and-drop reordering for ingredient and direction rows
  // ----------------------------------------------------------------
  function _initDragSort(list) {
    if (!list) return;
    let dragRow = null;

    list.addEventListener('dragstart', e => {
      if (!e.target.classList.contains('drag-handle')) { e.preventDefault(); return; }
      dragRow = e.target.closest('[data-drag-row]');
      if (!dragRow) return;
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', '');
      setTimeout(() => { if (dragRow) dragRow.classList.add('dragging'); }, 0);
    });

    list.addEventListener('dragover', e => {
      if (!dragRow) return;
      e.preventDefault();
      const target = e.target.closest('[data-drag-row]');
      if (!target || target === dragRow) return;
      const mid = target.getBoundingClientRect().top + target.getBoundingClientRect().height / 2;
      if (e.clientY < mid) target.before(dragRow);
      else target.after(dragRow);
    });

    list.addEventListener('dragend', () => {
      if (dragRow) dragRow.classList.remove('dragging');
      dragRow = null;
    });
  }

  _initDragSort(document.getElementById('ingredients-list'));
  _initDragSort(document.getElementById('directions-list'));

  // ----------------------------------------------------------------
  // Form: extract from URL
  // ----------------------------------------------------------------
  const extractBtn = document.getElementById('extract-btn');
  const extractStatus = document.getElementById('extract-status');

  if (extractBtn) {
    extractBtn.addEventListener('click', async () => {
      const url = document.getElementById('extract-url').value.trim();
      if (!url) return;
      extractBtn.disabled = true;
      extractBtn.textContent = 'Extracting…';
      extractStatus.hidden = false;
      extractStatus.textContent = 'Fetching recipe data…';

      try {
        const res = await postJSON('/extract/post', { url });
        if (res.status !== 'ok') {
          extractStatus.textContent = res.message || 'Extraction failed.';
          return;
        }
        const d = res.data;
        _fillField('title', d.title);
        _fillField('type', d.type);
        _fillField('servings', d.servings);
        _fillField('prep_time', d.prep_time);
        _fillField('cook_time', d.cook_time);
        if (!document.getElementById('source').value && url) {
          document.getElementById('source').value = url;
        }
        if (d.ingredients && d.ingredients.length) {
          _fillIngredients(d.ingredients);
        }
        if (d.directions && d.directions.length) {
          _fillDirections(d.directions);
        }
        // Queue images for adding after form save — inform user
        if (d.images && d.images.length) {
          extractStatus.textContent = `Extracted. ${d.images.length} image(s) found — they can be added after saving.`;
          _storeExtractedImages(d.images);
        } else {
          extractStatus.textContent = 'Extracted successfully.';
        }
      } catch (e) {
        extractStatus.textContent = 'Network error during extraction.';
      } finally {
        extractBtn.disabled = false;
        extractBtn.textContent = 'Extract';
      }
    });
  }

  function _fillField(id, val) {
    if (!val) return;
    const el = document.getElementById(id);
    if (el && !el.value) el.value = val;
  }

  function _fillIngredients(ings) {
    const list = document.getElementById('ingredients-list');
    if (!list) return;
    const tmpl = document.getElementById('ingredient-row-template');
    const subTmpl = document.getElementById('ingredient-subtitle-row-template');
    if (!tmpl) return;
    // Clear existing empty rows
    list.querySelectorAll('.ingredient-row').forEach(row => {
      const itemEl = row.querySelector('.ing-item, .ing-subtitle-text');
      if (itemEl && !itemEl.value) row.remove();
    });
    ings.forEach(ing => {
      if (ing.subtitle !== undefined && subTmpl) {
        const clone = subTmpl.content.cloneNode(true);
        clone.querySelector('.ing-subtitle-text').value = ing.subtitle || '';
        list.appendChild(clone);
      } else {
        const clone = tmpl.content.cloneNode(true);
        clone.querySelector('.ing-amount').value = ing.amount || '';
        clone.querySelector('.ing-unit').value = ing.unit || '';
        clone.querySelector('.ing-item').value = ing.item || '';
        clone.querySelector('.ing-note').value = ing.note || '';
        list.appendChild(clone);
      }
    });
    _bindRemoveRows();
  }

  function _fillDirections(steps) {
    const list = document.getElementById('directions-list');
    if (!list) return;
    const tmpl = document.getElementById('direction-row-template');
    if (!tmpl) return;
    list.querySelectorAll('.direction-row').forEach(row => {
      if (!row.querySelector('textarea').value) row.remove();
    });
    steps.forEach(step => {
      const clone = tmpl.content.cloneNode(true);
      clone.querySelector('textarea').value = step;
      list.appendChild(clone);
    });
    _bindRemoveRows();
  }

  // Store extracted image URLs in sessionStorage so detail page can prompt
  function _storeExtractedImages(images) {
    try { sessionStorage.setItem('recipe_extracted_images', JSON.stringify(images)); } catch (_) {}
  }

  // ----------------------------------------------------------------
  // Form: add/remove ingredient and direction rows
  // ----------------------------------------------------------------
  function _bindRemoveRows() {
    document.querySelectorAll('.remove-row').forEach(btn => {
      btn.onclick = () => {
        const parent = btn.closest('.ingredient-row, .direction-row');
        if (parent) parent.remove();
      };
    });
  }
  _bindRemoveRows();

  const addIngredient = document.getElementById('add-ingredient');
  if (addIngredient) {
    addIngredient.addEventListener('click', () => {
      const tmpl = document.getElementById('ingredient-row-template');
      const clone = tmpl.content.cloneNode(true);
      document.getElementById('ingredients-list').appendChild(clone);
      _bindRemoveRows();
    });
  }

  const addSubtitle = document.getElementById('add-subtitle');
  if (addSubtitle) {
    addSubtitle.addEventListener('click', () => {
      const tmpl = document.getElementById('ingredient-subtitle-row-template');
      if (!tmpl) return;
      const clone = tmpl.content.cloneNode(true);
      document.getElementById('ingredients-list').appendChild(clone);
      _bindRemoveRows();
    });
  }

  const addDirection = document.getElementById('add-direction');
  if (addDirection) {
    addDirection.addEventListener('click', () => {
      const tmpl = document.getElementById('direction-row-template');
      const clone = tmpl.content.cloneNode(true);
      document.getElementById('directions-list').appendChild(clone);
      _bindRemoveRows();
    });
  }

  // ----------------------------------------------------------------
  // Detail/Form: image management
  // ----------------------------------------------------------------
  const recipeId = (function () {
    const m = window.location.pathname.match(/\/detail\/([^/]+)/);
    return m ? m[1] : null;
  })();

  function _bindImageDeletes() {
    document.querySelectorAll('.image-thumb-delete').forEach(btn => {
      btn.onclick = async () => {
        const imageId = btn.dataset.imageId;
        if (!confirm('Remove this image?')) return;
        const res = await postJSON(`/image/delete/post/${imageId}`, {});
        if (res.status === 'ok') {
          btn.closest('.image-thumb').remove();
        } else {
          alert(res.message || 'Failed to remove image.');
        }
      };
    });
  }
  _bindImageDeletes();

  function _appendImageThumb(imageId, url, caption) {
    const thumbs = document.getElementById('image-thumbs');
    if (!thumbs) return;
    const div = document.createElement('div');
    div.className = 'image-thumb';
    div.dataset.imageId = imageId;
    div.innerHTML = `<img src="${url}" alt="${caption || ''}"><button type="button" class="image-thumb-delete" data-image-id="${imageId}" title="Remove image">×</button>`;
    thumbs.appendChild(div);
    _bindImageDeletes();
  }

  async function _addImageByUrl(url, caption) {
    if (!recipeId && !_editRecipeId()) return;
    const rid = recipeId || _editRecipeId();
    const fd = new FormData();
    fd.append('image_url', url);
    fd.append('caption', caption || '');
    const res = await postForm(`/image/add/post/${rid}`, fd);
    if (res.status === 'ok') {
      _appendImageThumb(res.imageID, res.url, res.caption);
    } else {
      alert(res.message || 'Failed to add image.');
    }
  }

  function _editRecipeId() {
    const m = window.location.pathname.match(/\/edit\/([^/]+)/);
    return m ? m[1] : null;
  }

  const imageUrlBtn = document.getElementById('image-url-btn');
  if (imageUrlBtn) {
    imageUrlBtn.addEventListener('click', async () => {
      const url = document.getElementById('image-url-input').value.trim();
      const caption = document.getElementById('image-url-caption').value.trim();
      if (!url) return;
      await _addImageByUrl(url, caption);
      document.getElementById('image-url-input').value = '';
      document.getElementById('image-url-caption').value = '';
    });
  }

  const imageUploadBtn = document.getElementById('image-upload-btn');
  if (imageUploadBtn) {
    imageUploadBtn.addEventListener('click', async () => {
      const rid = recipeId || _editRecipeId();
      if (!rid) return;
      const fileInput = document.getElementById('image-file-input');
      const caption = document.getElementById('image-file-caption').value.trim();
      if (!fileInput.files.length) return;
      const fd = new FormData();
      fd.append('image_file', fileInput.files[0]);
      fd.append('caption', caption);
      imageUploadBtn.disabled = true;
      const res = await postForm(`/image/add/post/${rid}`, fd);
      imageUploadBtn.disabled = false;
      if (res.status === 'ok') {
        _appendImageThumb(res.imageID, res.url, res.caption);
        fileInput.value = '';
        document.getElementById('image-file-caption').value = '';
      } else {
        alert(res.message || 'Upload failed.');
      }
    });
  }

  // ----------------------------------------------------------------
  // Flag toggles: ★ favorite and Try want-to-try
  // ----------------------------------------------------------------
  document.querySelectorAll('.recipe-flag').forEach(btn => {
    btn.addEventListener('click', async () => {
      const recipeId = btn.dataset.recipe;
      const flag = btn.dataset.flag;
      if (!recipeId || !flag) return;
      btn.disabled = true;
      try {
        const res = await postJSON(`/${flag}/toggle/post/${recipeId}`, {});
        if (res.status !== 'ok') return;
        const active = flag === 'favorite' ? res.favorite : res.want_to_try;
        btn.classList.toggle('active', active);
        if (flag === 'favorite') {
          btn.title = active ? 'Unfavorite' : 'Favorite';
        } else {
          btn.title = active ? 'Remove from want-to-try' : 'Mark as want to try';
        }
        // Update text label on detail page buttons
        const label = btn.querySelector('.flag-label');
        if (label) {
          if (flag === 'favorite') {
            label.textContent = active ? (btn.dataset.labelOn || 'Favorited') : (btn.dataset.labelOff || 'Favorite');
          } else {
            label.textContent = active ? '✓ ' + (btn.dataset.labelOn || 'Want to Try') : (btn.dataset.labelOff || 'Want to Try');
          }
        }
        // Update want-to-try row class
        if (flag === 'want_to_try') {
          const row = btn.closest('.recipe-row');
          if (row) row.classList.toggle('recipe-row-try', active);
        }
      } catch (_) {
      } finally {
        btn.disabled = false;
      }
    });
  });

  // ----------------------------------------------------------------
  // Archive toggle
  // ----------------------------------------------------------------
  document.querySelectorAll('.recipe-archive-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const recipeId = btn.dataset.recipe;
      if (!recipeId) return;
      btn.disabled = true;
      try {
        const res = await postJSON(`/archive/toggle/post/${recipeId}`, {});
        if (res.status !== 'ok') return;
        const isArchived = res.archived;
        if (isArchived) {
          // Archived: remove row from index list, or update detail button
          const row = btn.closest('.recipe-row');
          if (row) {
            row.remove();
          } else {
            // Detail page: update button label and redirect
            btn.textContent = btn.dataset.labelOn || 'Restore';
            btn.classList.add('active');
            window.location.href = BASE + '/index';
          }
        } else {
          // Restored: remove row from archive list, or update detail button
          const row = btn.closest('.recipe-row');
          if (row) {
            row.remove();
          } else {
            btn.textContent = btn.dataset.labelOff || 'Archive';
            btn.classList.remove('active');
          }
        }
      } catch (_) {
      } finally {
        btn.disabled = false;
      }
    });
  });

  // ----------------------------------------------------------------
  // Show more / See all within a recipe category
  // ----------------------------------------------------------------
  document.querySelectorAll('.recipe-more-controls').forEach(controls => {
    const list = document.getElementById(controls.dataset.listId);
    const showMoreBtn = controls.querySelector('.btn-show-more');
    const showAllBtn = controls.querySelector('.btn-show-all');

    function hiddenRows() {
      return list ? Array.from(list.querySelectorAll('.recipe-row-hidden')) : [];
    }

    if (showMoreBtn) {
      showMoreBtn.addEventListener('click', () => {
        hiddenRows().slice(0, 10).forEach(r => r.classList.remove('recipe-row-hidden'));
        const remaining = hiddenRows().length;
        if (remaining === 0) {
          controls.remove();
        } else {
          const span = showMoreBtn.querySelector('.remaining');
          if (span) span.textContent = `(${remaining} remaining)`;
        }
      });
    }

    if (showAllBtn) {
      showAllBtn.addEventListener('click', () => {
        hiddenRows().forEach(r => r.classList.remove('recipe-row-hidden'));
        controls.remove();
      });
    }
  });

})();
