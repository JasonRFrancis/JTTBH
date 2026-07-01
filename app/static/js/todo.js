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
    const updateForm = item.querySelector('.todo-item__form');
    if (!updateForm) return;

    titleEl.addEventListener('dblclick', () => {
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

  const onInput = () => {
    if (input.value.trim()) {
      input.removeEventListener('input', onInput);
      addBlankSlot(listEl, lastBlank);
    }
  };
  input.addEventListener('input', onInput);
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
   7. Drag-and-drop reordering (within-list) + cross-list move
   ========================================================================= */

let _globalDragging = null;
let _dragSourceList = null;

/**
 * Enable HTML5 drag-and-drop reordering within each todo-list,
 * and cross-list moves between lists.
 */
function initDragDrop() {
  document.querySelectorAll('todo-list').forEach((listEl) => {
    initListDragDrop(listEl);
  });
}

function initListDragDrop(listEl) {
  listEl.addEventListener('dragstart', (e) => {
    const item = e.target.closest('todo-item[data-id]');
    if (!item) return;
    _globalDragging = item;
    _dragSourceList = listEl;
    item.classList.add('todo-item--dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', item.dataset.id);
  });

  listEl.addEventListener('dragend', () => {
    if (_globalDragging) {
      _globalDragging.classList.remove('todo-item--dragging');
      _globalDragging = null;
      _dragSourceList = null;
    }
    document.querySelectorAll('.todo-item--drag-over').forEach((el) => {
      el.classList.remove('todo-item--drag-over');
    });
    document.querySelectorAll('todo-list.todo-list--drag-target').forEach((el) => {
      el.classList.remove('todo-list--drag-target');
    });
  });

  listEl.addEventListener('dragover', (e) => {
    if (!_globalDragging) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    const target = e.target.closest('todo-item[data-id]');
    document.querySelectorAll('.todo-item--drag-over').forEach((el) => {
      el.classList.remove('todo-item--drag-over');
    });
    document.querySelectorAll('todo-list.todo-list--drag-target').forEach((el) => {
      el.classList.remove('todo-list--drag-target');
    });
    if (target && target !== _globalDragging) {
      target.classList.add('todo-item--drag-over');
    } else if (!target) {
      listEl.classList.add('todo-list--drag-target');
    }
  });

  listEl.addEventListener('drop', (e) => {
    e.preventDefault();
    document.querySelectorAll('.todo-item--drag-over, todo-list.todo-list--drag-target').forEach((el) => {
      el.classList.remove('todo-item--drag-over');
      el.classList.remove('todo-list--drag-target');
    });
    if (!_globalDragging) return;

    const target = e.target.closest('todo-item[data-id]');
    const isSameList = listEl === _dragSourceList;

    if (isSameList) {
      // Within-list reorder
      if (!target || _globalDragging === target) return;
      const allItems = [...listEl.querySelectorAll('todo-item[data-id]')];
      const fromIdx = allItems.indexOf(_globalDragging);
      const toIdx   = allItems.indexOf(target);
      if (fromIdx < toIdx) target.after(_globalDragging);
      else target.before(_globalDragging);

      const updatedItems = [...listEl.querySelectorAll('todo-item[data-id]')];
      const payload = {
        todos: updatedItems.map((el, idx) => ({ todoID: el.dataset.id, position: idx })),
      };
      fetch(todoUrl('reorder/post'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
        body: JSON.stringify(payload),
      }).catch(() => {});
    } else {
      // Cross-list move
      const todoId = _globalDragging.dataset.id;
      const listType = listEl.dataset.type || 'daily';
      // data-name may be url-encoded (custom lists); decode it for the POST
      const listName = listEl.dataset.name ? decodeURIComponent(listEl.dataset.name) : '';
      const listDate = listEl.dataset.date || '';

      // Append to target list (before blank slots)
      const firstBlank = listEl.querySelector('todo-item.todo-item--blank');
      if (firstBlank) firstBlank.before(_globalDragging);
      else listEl.appendChild(_globalDragging);

      // POST to move endpoint using field names the route expects
      const form = document.createElement('form');
      const params = { new_list_type: listType, new_list_name: listName, new_due: listDate };
      Object.entries(params).forEach(([k, v]) => {
        if (v) {
          const i = document.createElement('input');
          i.name = k;
          i.value = v;
          form.appendChild(i);
        }
      });
      const fd = new FormData(form);
      fetch(todoUrl('move/post', todoId), {
        method: 'POST',
        body: fd,
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        redirect: 'follow',
      }).catch(() => {});
    }
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
   9. Click-to-toggle: single click on a todo item toggles completion
   ========================================================================= */

/**
 * Single click anywhere on a todo-item (except links, buttons, inputs, and
 * the details panel) toggles completion via the hidden checkbox.
 * Optimistically flips the completed class for instant visual feedback.
 */
function initClickToToggle() {
  document.addEventListener('click', (e) => {
    // Ignore clicks on interactive elements and links
    if (e.target.tagName === 'A' || e.target.closest('a')) return;
    if (e.target.tagName === 'BUTTON' || e.target.closest('button')) return;
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    if (e.target.closest('details')) return;

    const item = e.target.closest('todo-item[data-id]');
    if (!item) return;

    // Don't toggle while the title is in edit mode
    const title = item.querySelector('.todo-item__title');
    if (title && title.contentEditable === 'true') return;

    const checkbox = item.querySelector('.todo-item__checkbox');
    if (!checkbox) return;

    // Optimistic UI: flip completed class immediately
    checkbox.checked = !checkbox.checked;
    item.classList.toggle('todo-item--completed', checkbox.checked);

    checkbox.dispatchEvent(new Event('change', { bubbles: true }));
  });
}


/* =========================================================================
   10. Checkbox toggle: auto-submit on change
   ========================================================================= */

/**
 * Submit the toggle form when a completion checkbox changes state.
 * Uses event delegation so it works for dynamically-added items.
 * Hides the no-JS toggle buttons since the checkbox handles interaction.
 */
function initCheckboxToggle() {
  document.querySelectorAll('.todo-item__toggle-btn').forEach((btn) => {
    btn.hidden = true;
  });

  document.addEventListener('change', (e) => {
    if (!e.target.matches('.todo-item__checkbox')) return;
    const form = e.target.closest('form');
    if (!form) return;
    const toggleBtn = form.querySelector('.todo-item__toggle-btn');
    if (!toggleBtn) return;
    // requestSubmit(submitter) respects the button's formaction attribute
    if (form.requestSubmit) {
      form.requestSubmit(toggleBtn);
    } else {
      const orig = form.action;
      form.action = toggleBtn.getAttribute('formaction') || orig;
      form.submit();
      form.action = orig;
    }
  });
}


/* =========================================================================
   11. Detail panel: close when clicking outside
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
   12. Initialisation
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
    initClickToToggle,
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
