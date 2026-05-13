/**
 * JTTBH Habit Tracker – Client-side JavaScript
 * =============================================
 *
 * Features
 * --------
 * 1. AJAX toggle for habit cells on the calendar view.
 *    - Clicks the button, POSTs to the toggle endpoint.
 *    - Updates visual state optimistically; reverts on error.
 *    - Falls back to a plain form POST if fetch is unavailable.
 *
 * 2. Icon preview on the settings page.
 *    - Fetches SVG from the <option> dataset when available,
 *      or hides the preview when "None" is selected.
 *
 * 3. Drag-to-reorder grid positions on the settings page.
 *    - Drag a habit cell to a new grid position.
 *    - Saves all positions in a single batch AJAX request.
 *    - Shows a "Save Positions" button after any drag.
 *
 * Dependencies
 * ------------
 * - `username` constant must be defined before this script loads:
 *     <script>const username = {{ username | tojson }};</script>
 */

(function () {
  'use strict';

  /* -------------------------------------------------------------------------
     1. Habit cell toggle (calendar & grid cells)
     ------------------------------------------------------------------------- */

  /**
   * Wire up all toggleable habit cells on the page.
   * Cells with [disabled] or class "empty" are skipped.
   */
  function initToggleCells() {
    const cells = document.querySelectorAll('.habit-cell:not([disabled]):not(.empty)');
    cells.forEach(function (btn) {
      btn.addEventListener('click', handleToggleClick);
    });
  }

  /**
   * Handle a click on a habit cell.
   * Optimistically updates the UI, then sends the toggle request.
   */
  function handleToggleClick(event) {
    const btn     = event.currentTarget;
    const habitId = btn.dataset.habitId;
    const datStr  = btn.dataset.date;

    if (!habitId || !datStr || !username) return;

    // Prevent rapid double-clicks while the request is in-flight
    if (btn.dataset.pending === '1') return;
    btn.dataset.pending = '1';

    const url = '/' + username + '/habit/toggle/post/' + habitId + '/' + datStr;

    // Optimistic UI update
    const wasCompleted = btn.classList.contains('completed');
    setCompleted(btn, !wasCompleted);

    // Send AJAX toggle
    if (typeof fetch === 'function') {
      fetch(url, {
        method:  'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        credentials: 'same-origin',
      })
      .then(function (response) {
        if (!response.ok) {
          throw new Error('HTTP ' + response.status);
        }
        return response.json();
      })
      .then(function (data) {
        // Reconcile with server state
        setCompleted(btn, data.completed === 1 || data.completed === true);
      })
      .catch(function () {
        // Revert optimistic update on failure
        setCompleted(btn, wasCompleted);
      })
      .finally(function () {
        btn.dataset.pending = '0';
      });
    } else {
      // No fetch available – fall back to a plain form POST
      btn.dataset.pending = '0';
      var form = document.createElement('form');
      form.method = 'POST';
      form.action = url;
      document.body.appendChild(form);
      form.submit();
    }
  }

  /**
   * Update a habit cell's visual and ARIA state.
   *
   * @param {HTMLElement} btn
   * @param {boolean} completed
   */
  function setCompleted(btn, completed) {
    btn.classList.toggle('completed', completed);
    btn.setAttribute('aria-pressed', completed ? 'true' : 'false');
    const name = btn.title || btn.getAttribute('aria-label') || 'Habit';
    btn.setAttribute(
      'aria-label',
      name.split(':')[0] + ': ' + (completed ? 'completed' : 'not completed')
    );
  }


  /* -------------------------------------------------------------------------
     2. Icon preview on settings page
     ------------------------------------------------------------------------- */

  /**
   * Wire up all icon <select> elements to show a preview of the chosen icon.
   * Each select must have a `data-preview` attribute naming the ID of the
   * preview container, OR be followed by a `.icon-preview` sibling.
   */
  function initIconPreviews() {
    // Build a name->svg map from the select options that carry data-svg
    // (a future enhancement could store svg in data attributes; for now
    //  we use a lightweight AJAX lookup)
    document.querySelectorAll('select.icon-select').forEach(function (sel) {
      sel.addEventListener('change', function () {
        handleIconChange(sel);
      });
      // Trigger immediately so pre-selected values show on page load
      handleIconChange(sel);
    });
  }

  /**
   * Update the icon preview area for a given <select>.
   */
  function handleIconChange(sel) {
    var previewId = sel.dataset.preview;
    var preview;
    if (previewId) {
      preview = document.getElementById(previewId);
    } else {
      // Walk forward to find the next .icon-preview sibling
      var sibling = sel.nextElementSibling;
      while (sibling) {
        if (sibling.classList.contains('icon-preview')) {
          preview = sibling;
          break;
        }
        sibling = sibling.nextElementSibling;
      }
      if (!preview) {
        // Try the parent's next sibling
        var parent = sel.closest('.form-row');
        if (parent) {
          var next = parent.nextElementSibling;
          if (next && next.classList.contains('icon-preview')) {
            preview = next;
          }
        }
      }
    }

    if (!preview) return;

    var selected = sel.options[sel.selectedIndex];
    if (!selected || !selected.value) {
      preview.innerHTML = '';
      return;
    }

    var iconName = selected.value;
    preview.innerHTML = '<span style="color:#6b7280;font-size:0.75rem;">Loading\u2026</span>';

    // Fetch icon SVG from server (the svg table)
    fetch('/api/icon/' + encodeURIComponent(iconName), {
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      credentials: 'same-origin',
    })
    .then(function (r) {
      if (!r.ok) throw new Error('Not found');
      return r.json();
    })
    .then(function (data) {
      if (data.svg) {
        preview.innerHTML = data.svg;
      } else {
        preview.innerHTML = '<span style="color:#6b7280;font-size:0.75rem;">' + iconName + '</span>';
      }
    })
    .catch(function () {
      // API not available: just show the name
      preview.innerHTML = '<span style="color:#6b7280;font-size:0.75rem;">' + iconName + '</span>';
    });
  }


  /* -------------------------------------------------------------------------
     3. Drag-to-reorder grid positions (settings page)
     ------------------------------------------------------------------------- */

  var _draggedCell     = null;
  var _pendingPositions = {};   // habitID -> new position

  function initGridDrag() {
    var grid = document.getElementById('grid-preview');
    if (!grid) return;

    var saveBtn = document.getElementById('save-positions');

    // Attach drag handlers to all occupied cells
    grid.querySelectorAll('.grid-preview-cell.occupied').forEach(function (cell) {
      cell.addEventListener('dragstart', onDragStart);
      cell.addEventListener('dragend',   onDragEnd);
    });

    // Attach drop handlers to all cells (occupied and empty)
    grid.querySelectorAll('.grid-preview-cell').forEach(function (cell) {
      cell.addEventListener('dragover',  onDragOver);
      cell.addEventListener('dragleave', onDragLeave);
      cell.addEventListener('drop',      onDrop);
    });

    if (saveBtn) {
      saveBtn.addEventListener('click', function () {
        savePendingPositions(saveBtn);
      });
    }
  }

  function onDragStart(event) {
    _draggedCell = event.currentTarget;
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('text/plain', _draggedCell.dataset.habitId || '');
    setTimeout(function () {
      if (_draggedCell) _draggedCell.style.opacity = '0.4';
    }, 0);
  }

  function onDragEnd() {
    if (_draggedCell) {
      _draggedCell.style.opacity = '';
    }
    _draggedCell = null;
    document.querySelectorAll('.grid-preview-cell.drag-over').forEach(function (c) {
      c.classList.remove('drag-over');
    });
  }

  function onDragOver(event) {
    if (!_draggedCell) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
    event.currentTarget.classList.add('drag-over');
  }

  function onDragLeave(event) {
    event.currentTarget.classList.remove('drag-over');
  }

  function onDrop(event) {
    event.preventDefault();
    var target = event.currentTarget;
    target.classList.remove('drag-over');

    if (!_draggedCell || _draggedCell === target) return;

    var habitId      = _draggedCell.dataset.habitId;
    var newPosition  = parseInt(target.dataset.position, 10);
    var oldPosition  = parseInt(_draggedCell.dataset.position, 10);

    if (isNaN(newPosition) || !habitId) return;

    // Swap content in DOM
    var draggedName  = _draggedCell.querySelector('.grid-habit-name');
    var draggedPos   = _draggedCell.querySelector('.grid-pos-num');
    var targetName   = target.querySelector('.grid-habit-name');
    var targetHabitId = target.dataset.habitId;

    // Update _draggedCell to look like target
    if (targetHabitId) {
      // Swap: target gets dragged's habit, dragged gets target's habit
      var targetNameText = targetName ? targetName.textContent : '';
      var targetColor    = target.style.backgroundColor;

      if (draggedName) draggedName.textContent = targetNameText;
      _draggedCell.style.backgroundColor = targetColor;
      _draggedCell.dataset.habitId        = targetHabitId;
      _draggedCell.dataset.position       = oldPosition;
      _draggedCell.title                  = targetNameText + ' (pos ' + oldPosition + ')';
      _draggedCell.classList.toggle('occupied', !!targetHabitId);
      _draggedCell.classList.toggle('empty',    !targetHabitId);

      _pendingPositions[targetHabitId] = oldPosition;
    } else {
      // Target is empty: just move the habit there
      if (draggedName) draggedName.textContent = '';
      _draggedCell.classList.remove('occupied');
      _draggedCell.classList.add('empty');
      _draggedCell.removeAttribute('data-habit-id');
      _draggedCell.style.backgroundColor = '';
      _draggedCell.title = 'Position ' + oldPosition;
    }

    // Update target cell
    if (targetName) {
      targetName.textContent = _draggedCell.querySelector('.grid-habit-name')
        ? ''  // already cleared above
        : (draggedName ? draggedName.textContent : '');
    }

    // Actually: rebuild target to show the dragged habit
    target.innerHTML = '';
    var posNum = document.createElement('span');
    posNum.className   = 'grid-pos-num';
    posNum.textContent = newPosition;
    target.appendChild(posNum);

    var nameSpan = document.createElement('span');
    nameSpan.className = 'grid-habit-name';
    // Fetch name from original dragged cell (before it got cleared)
    nameSpan.textContent = habitId
      ? (document.querySelector('[data-habit-id="' + habitId + '"] .grid-habit-name')
         ? '' : '')
      : '';

    // Simpler: store the original name in a data attribute
    var origName = _draggedCell.getAttribute('data-orig-name') || habitId;
    nameSpan.textContent = origName.substring(0, 8);
    target.appendChild(nameSpan);

    target.dataset.habitId  = habitId;
    target.dataset.position = newPosition;
    target.classList.add('occupied');
    target.classList.remove('empty');
    target.setAttribute('draggable', 'true');
    target.style.backgroundColor = _draggedCell.style.backgroundColor;

    // Wire up new drag handlers
    target.addEventListener('dragstart', onDragStart);
    target.addEventListener('dragend',   onDragEnd);

    _pendingPositions[habitId] = newPosition;

    // Show save button
    var saveBtn = document.getElementById('save-positions');
    if (saveBtn) saveBtn.style.display = '';
  }

  /**
   * POST all pending position changes to the server.
   */
  function savePendingPositions(saveBtn) {
    if (!username) return;

    var items = Object.keys(_pendingPositions).map(function (hid) {
      return { habitID: hid, position: _pendingPositions[hid] };
    });

    if (items.length === 0) return;

    var originalText = saveBtn.textContent;
    saveBtn.textContent = 'Saving\u2026';
    saveBtn.disabled    = true;

    fetch('/' + username + '/habit/reorder/post', {
      method:  'POST',
      headers: {
        'Content-Type':     'application/json',
        'X-Requested-With': 'XMLHttpRequest',
      },
      credentials: 'same-origin',
      body:    JSON.stringify(items),
    })
    .then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    })
    .then(function () {
      _pendingPositions = {};
      saveBtn.textContent = 'Saved!';
      setTimeout(function () { window.location.reload(); }, 600);
    })
    .catch(function () {
      saveBtn.textContent = 'Error – try again';
      saveBtn.disabled    = false;
    });
  }


  /* -------------------------------------------------------------------------
     4. Grid position picker (settings page)
     ------------------------------------------------------------------------- */

  /**
   * Wire up all .pos-picker grids on the page.
   * Each picker sits inside a form that also has dayweek checkboxes.
   */
  function initGridPickers() {
    document.querySelectorAll('.pos-picker').forEach(function (picker) {
      var form    = picker.closest('form');
      var habitID = picker.dataset.habitId || '';
      if (!form) return;

      // Cell click: select position, update hidden input
      picker.querySelectorAll('.pos-picker-cell').forEach(function (cell) {
        cell.addEventListener('click', function () {
          if (cell.disabled) return;
          picker.querySelectorAll('.pos-picker-cell').forEach(function (c) {
            c.classList.remove('selected');
          });
          cell.classList.add('selected');
          var hidden = form.querySelector('input[name="position"]');
          if (hidden) hidden.value = cell.dataset.position;
        });
      });

      // Dayweek change: refresh conflict state
      form.querySelectorAll('input[type="checkbox"][name="dayweek"]').forEach(function (cb) {
        cb.addEventListener('change', function () {
          refreshPickerConflicts(picker, habitID);
        });
      });

      // Initial load
      refreshPickerConflicts(picker, habitID);
    });
  }

  /**
   * Fetch conflict data for a picker and update cell states.
   *
   * Cells are marked .conflicted and disabled when another habit occupies
   * that position on overlapping days.  Occupied-but-no-conflict cells get
   * the .occupied class (a visual hint, still clickable).
   */
  function refreshPickerConflicts(picker, habitID) {
    var form    = picker.closest('form');
    var dayweek = 0;
    form.querySelectorAll('input[type="checkbox"][name="dayweek"]:checked')
        .forEach(function (cb) { dayweek += parseInt(cb.value, 10) || 0; });
    if (dayweek === 0) dayweek = 127;

    var url = '/' + username + '/habit/positions/json?dayweek=' + dayweek;
    if (habitID) url += '&exclude=' + encodeURIComponent(habitID);

    fetch(url, {
      headers:     { 'X-Requested-With': 'XMLHttpRequest' },
      credentials: 'same-origin',
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      var infoMap = {};
      (data.positions || []).forEach(function (p) { infoMap[p.position] = p; });

      picker.querySelectorAll('.pos-picker-cell').forEach(function (cell) {
        var pos  = parseInt(cell.dataset.position, 10);
        var info = infoMap[pos];

        if (info && info.conflicted) {
          cell.disabled = true;
          cell.classList.add('conflicted');
          cell.classList.remove('occupied');
          cell.title = 'Position ' + pos + ' — conflict with “' + info.name + '”';
        } else if (info) {
          cell.disabled = false;
          cell.classList.remove('conflicted');
          cell.classList.add('occupied');
          cell.title = 'Position ' + pos + ' — “' + info.name + '” (different days)';
        } else {
          cell.disabled = false;
          cell.classList.remove('conflicted', 'occupied');
          cell.title = 'Position ' + pos;
        }
      });
    })
    .catch(function () { /* leave cells unchanged on network error */ });
  }


  /* -------------------------------------------------------------------------
     Initialise everything on DOMContentLoaded
     ------------------------------------------------------------------------- */

  document.addEventListener('DOMContentLoaded', function () {
    initToggleCells();
    initIconPreviews();
    initGridDrag();
    initGridPickers();

    // Store original habit names on grid preview cells so drag-swap works
    document.querySelectorAll('.grid-preview-cell.occupied').forEach(function (cell) {
      var nameEl = cell.querySelector('.grid-habit-name');
      if (nameEl) {
        cell.setAttribute('data-orig-name', nameEl.textContent);
      }
    });
  });

}());
