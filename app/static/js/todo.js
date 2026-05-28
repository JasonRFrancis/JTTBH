/**
 * todo.js
 * =======
 * Progressive-enhancement JavaScript for the Todo feature.
 *
 * All functionality degrades gracefully: the page works without JS using
 * plain HTML forms and standard HTTP navigation.
 *
 * Sections
 * --------
 * 1.  Constants & helpers
 * 2.  AJAX form submission with fallback
 * 3.  Markdown rendering (via marked.js CDN)
 * 4.  Inline title editing (click-to-edit, blur/enter to save)
 * 5.  Auto-submit new-todo form on Enter / blur with content
 * 6.  Auto-grow: add a blank slot when the last input is filled
 * 7.  Drag-and-drop reordering within a list
 * 8.  Date navigation: date-picker form auto-submit
 * 9.  Detail panel: close when clicking outside
 * 10. Initialisation
 */

/* =========================================================================
   1. Constants & helpers
   ========================================================================= */

const USERNAME = (() => {
  // Extract from the current path: /<username>/todo/...
  const parts = window.location.pathname.split('/');
  return parts[1] || '';
})();

/**
 * Build a route URL for the todo blueprint.
 *
 * @param {string} action  e.g. 'toggle/post', 'create/post'
 * @param {string} [id]    Optional resource ID segment.
 * @returns {string}
 */
function todoUrl(action, id) {
  const base = `/${USERNAME}/todo/${action}`;
  return id ? `${base}/${id}` : base;
}

/**
 * Shallow-debounce: return a function that delays invocation.
 *
 * @param {Function} fn
 * @param {number}   ms
 * @returns {Function}
 */
function debounce(fn, ms) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}


/* =========================================================================
   2. AJAX form submission with fallback
   ========================================================================= */

/**
 * Submit a form via fetch with XMLHttpRequest header so Flask can detect
 * AJAX.  Falls back to native form.submit() on network error.
 *
 * @param {HTMLFormElement} form
 * @param {Function}        [onSuccess]  Called when server responds 2xx.
 * @param {Function}        [onError]    Called on non-redirect error.
 */
function submitForm(form, onSuccess, onError) {
  const formData = new FormData(form);

  fetch(form.action, {
    method: form.method || 'POST',
    body: formData,
    headers: { 'X-Requested-With': 'XMLHttpRequest' },
    redirect: 'follow',
  })
    .then((r) => {
      if (r.redirected) {
        window.location.href = r.url;
      } else if (r.ok) {
        onSuccess && onSuccess(r);
      } else {
        onError ? onError(r) : form.submit();
      }
    })
    .catch(() => {
      // Network failure — degrade to synchronous submit
      form.submit();
    });
}


/* =========================================================================
   3. Markdown rendering
   ========================================================================= */

/**
 * Render Markdown in all .todo-item__title elements that have a
 * data-raw attribute (set in the template as the raw text value).
 *
 * Uses marked.js if available, otherwise leaves text as-is.
 * Sanitises output to block scripts and raw HTML (per spec).
 */
function renderMarkdown() {
  if (typeof marked === 'undefined') return;

  // Configure marked: breaks = true, no HTML pass-through
  marked.setOptions({
    breaks: true,
    gfm: true,
    headerIds: false,
    mangle: false,
  });

  document.querySelectorAll('.todo-item__title[data-raw]').forEach((el) => {
    const raw = el.dataset.raw || el.textContent;
    // Render then strip any remaining HTML tags for safety
    const html = marked.parseInline(raw);
    el.innerHTML = html;
  });

  // Also render content panels
  document.querySelectorAll('.todo-item__content').forEach((el) => {
    const raw = el.textContent.trim();
    if (raw) {
      el.innerHTML = marked.parse(raw);
    }
  });
}


/* =========================================================================
   4. Inline title editing
   ========================================================================= */

/**
 * Enable click-to-edit on all todo item titles.
 * On blur or Enter, submit the hidden update form via AJAX.
 */
function initInlineEditing() {
  document.querySelectorAll('.todo-item__title').forEach((titleEl) => {
    const item = titleEl.closest('todo-item');
    if (!item) return;
    const updateForm = item.querySelector('.todo-item__update-form');
    if (!updateForm) return;

    titleEl.addEventListener('click', () => {
      if (titleEl.contentEditable === 'true') return; // already editing
      titleEl.contentEditable = 'true';
      titleEl.focus();

      // Place cursor at end
      const range = document.createRange();
      range.selectNodeContents(titleEl);
      range.collapse(false);
      const sel = window.getSelection();
      sel.removeAllRanges();
      sel.addRange(range);
    });

    const saveTitle = debounce(() => {
      const newTitle = titleEl.textContent.trim();
      if (!newTitle) {
        // Restore original if emptied
        titleEl.textContent = titleEl.dataset.raw || titleEl.textContent;
        titleEl.contentEditable = 'false';
        return;
      }
      titleEl.contentEditable = 'false';
      titleEl.dataset.raw = newTitle;

      const titleInput = updateForm.querySelector('input[name="title"]');
      if (titleInput) titleInput.value = newTitle;

      submitForm(updateForm, () => {
        // Re-render markdown after save
        titleEl.innerHTML = (typeof marked !== 'undefined')
          ? marked.parseInline(newTitle)
          : newTitle;
      });
    }, 300);

    titleEl.addEventListener('blur', saveTitle);

    titleEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        titleEl.blur();
      }
      if (e.key === 'Escape') {
        titleEl.textContent = titleEl.dataset.raw || '';
        titleEl.contentEditable = 'false';
      }
    });
  });
}


/* =========================================================================
   5. Auto-submit new-todo form on Enter / blur with content
   ========================================================================= */

/**
 * Wire up all .todo-new forms:
 * - Pressing Enter submits immediately via AJAX then adds a new blank slot.
 * - Blurring with non-empty text also submits.
 *
 * @param {HTMLElement} [scope]  Scope to search within (defaults to document).
 */
function initNewTodoForms(scope) {
  const root = scope || document;
  root.querySelectorAll('.todo-new').forEach((form) => {
    if (form.dataset.wired) return;
    form.dataset.wired = '1';

    const input = form.querySelector('input[name="title"]');
    if (!input) return;

    const handleSubmit = () => {
      const title = input.value.trim();
      if (!title) return;

      const listEl = form.closest('todo-list');

      submitForm(form, () => {
        // Clear the input and let auto-grow add a new slot if needed
        input.value = '';
        // After AJAX success, reload the list section to show new item
        // For simplicity: reload the page (full PRG cycle)
        window.location.reload();
      });
    };

    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        handleSubmit();
      }
    });

    input.addEventListener('blur', () => {
      if (input.value.trim()) handleSubmit();
    });
  });
}


/* =========================================================================
   6. Auto-grow: add blank slot when last input is filled
   ========================================================================= */

/**
 * For each todo-list, watch the last blank input.  When it receives a
 * non-empty value, append a fresh blank slot so the list always has room.
 */
function initAutoGrow() {
  document.querySelectorAll('todo-list').forEach((listEl) => {
    observeLastSlot(listEl);
  });
}

function observeLastSlot(listEl) {
  const blanks = listEl.querySelectorAll('todo-item.todo-item--blank');
  if (!blanks.length) return;

  const lastBlank = blanks[blanks.length - 1];
  const input = lastBlank.querySelector('input[name="title"]');
  if (!input || input.dataset.growWired) return;
  input.dataset.growWired = '1';

  input.addEventListener('input', () => {
    if (input.value.trim()) {
      addBlankSlot(listEl, lastBlank);
    }
  });
}

/**
 * Clone the last blank slot's form structure and append a new empty one.
 *
 * @param {Element} listEl      The todo-list element.
 * @param {Element} lastBlank   The current last blank todo-item.
 */
function addBlankSlot(listEl, lastBlank) {
  const newSlot = document.createElement('todo-item');
  newSlot.className = 'todo-item--blank';
  newSlot.setAttribute('role', 'listitem');

  const sourceForm = lastBlank.querySelector('form.todo-new');
  if (!sourceForm) return;

  const newForm = document.createElement('form');
  newForm.className = 'todo-new';
  newForm.method = 'post';
  newForm.action = sourceForm.action;

  // Copy hidden inputs
  sourceForm.querySelectorAll('input[type="hidden"]').forEach((hidden) => {
    const copy = document.createElement('input');
    copy.type = 'hidden';
    copy.name = hidden.name;
    copy.value = hidden.value;
    newForm.appendChild(copy);
  });

  const textInput = document.createElement('input');
  textInput.type = 'text';
  textInput.name = 'title';
  textInput.placeholder = 'Add item…';
  textInput.autocomplete = 'off';
  newForm.appendChild(textInput);

  newSlot.appendChild(newForm);
  listEl.appendChild(newSlot);

  // Wire up the new form and observe it for further growth
  initNewTodoForms(newSlot);
  observeLastSlot(listEl);
}


/* =========================================================================
   7. Drag-and-drop reordering
   ========================================================================= */

/**
 * Enable HTML5 drag-and-drop reordering within each todo-list.
 * On a successful drop, POST the new order to the reorder endpoint.
 */
function initDragDrop() {
  document.querySelectorAll('todo-list').forEach((listEl) => {
    initListDragDrop(listEl);
  });
}

function initListDragDrop(listEl) {
  let dragging = null;

  listEl.addEventListener('dragstart', (e) => {
    const item = e.target.closest('todo-item[data-id]');
    if (!item) return;
    dragging = item;
    item.classList.add('todo-item--dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', item.dataset.id);
  });

  listEl.addEventListener('dragend', () => {
    if (dragging) {
      dragging.classList.remove('todo-item--dragging');
      dragging = null;
    }
    listEl.querySelectorAll('.todo-item--drag-over').forEach((el) => {
      el.classList.remove('todo-item--drag-over');
    });
  });

  listEl.addEventListener('dragover', (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    const target = e.target.closest('todo-item[data-id]');
    listEl.querySelectorAll('.todo-item--drag-over').forEach((el) => {
      el.classList.remove('todo-item--drag-over');
    });
    if (target && target !== dragging) {
      target.classList.add('todo-item--drag-over');
    }
  });

  listEl.addEventListener('drop', (e) => {
    e.preventDefault();
    const target = e.target.closest('todo-item[data-id]');
    if (!dragging || !target || dragging === target) return;

    target.classList.remove('todo-item--drag-over');

    // Re-order in the DOM
    const allItems = [...listEl.querySelectorAll('todo-item[data-id]')];
    const fromIdx = allItems.indexOf(dragging);
    const toIdx   = allItems.indexOf(target);

    if (fromIdx < toIdx) {
      target.after(dragging);
    } else {
      target.before(dragging);
    }

    // Calculate new positions and POST to reorder endpoint
    const updatedItems = [...listEl.querySelectorAll('todo-item[data-id]')];
    const payload = {
      todos: updatedItems.map((el, idx) => ({
        todoID:   el.dataset.id,
        position: idx,
      })),
    };

    fetch(todoUrl('reorder/post'), {
      method: 'POST',
      headers: {
        'Content-Type':    'application/json',
        'X-Requested-With': 'XMLHttpRequest',
      },
      body: JSON.stringify(payload),
    }).catch(() => {
      // Reorder failed silently; page reload would restore DB order
    });
  });
}


/* =========================================================================
   8. Date navigation: date-picker auto-submit
   ========================================================================= */

/**
 * Auto-submit the date picker form when the user selects a date, so they
 * don't need to press a separate Go button.
 */
function initDatePicker() {
  const input = document.getElementById('date-picker');
  if (!input) return;

  input.addEventListener('change', () => {
    const form = document.getElementById('date-picker-form');
    if (!form) return;

    const dateStr = input.value;
    if (!dateStr) return;

    // Navigate to the correct dated URL
    const newUrl = `/${USERNAME}/todo/index/${dateStr}`;
    window.location.href = newUrl;
  });
}


/* =========================================================================
   9. Checkbox toggle: auto-submit on change
   ========================================================================= */

/**
 * Submit the toggle form when a completion checkbox changes state.
 * Uses event delegation so it works for dynamically-added items.
 */
function initCheckboxToggle() {
  document.addEventListener('change', (e) => {
    if (!e.target.matches('.todo-item__checkbox')) return;
    const form = e.target.closest('form');
    if (form) form.submit();
  });
}


/* =========================================================================
   10. Detail panel: close when clicking outside
   ========================================================================= */

/**
 * Close any open <details class="todo-item__details"> when a click lands
 * outside of it, so only one panel is open at a time.
 */
function initDetailPanels() {
  document.addEventListener('click', (e) => {
    document.querySelectorAll('details.todo-item__details[open]').forEach((det) => {
      if (!det.contains(e.target)) {
        det.open = false;
      }
    });
  });
}


/* =========================================================================
   10. Initialisation
   ========================================================================= */

/**
 * Boot all enhancements once the DOM is ready.
 * Each init function is wrapped so a failure in one doesn't break others.
 */
function init() {
  const fns = [
    renderMarkdown,
    initInlineEditing,
    initNewTodoForms,
    initAutoGrow,
    initDragDrop,
    initDatePicker,
    initCheckboxToggle,
    initDetailPanels,
  ];

  fns.forEach((fn) => {
    try {
      fn();
    } catch (err) {
      console.warn(`[todo.js] ${fn.name} failed:`, err);
    }
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
