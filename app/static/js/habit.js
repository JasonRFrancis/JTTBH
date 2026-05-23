/**
 * JTTBH Habit Tracker – Client-side JavaScript
 *
 * 1. Habit cell toggle (optimistic UI update + fire-and-forget POST).
 * 2. Polling: periodic sync with server state via GET /habit/index/json.
 * 3. Icon preview on the settings page.
 * 4. Drag-to-reorder grid positions (mouse and keyboard) on the settings page.
 * 5. Grid position picker conflict highlighting.
 *
 * Requires before this script:
 *   const username = ...;
 *   const refDate  = ...;   (habit index page only)
 */

(function () {
  'use strict';

  /* -------------------------------------------------------------------------
     Shared state
     ------------------------------------------------------------------------- */

  var _pendingToggles  = {};  // "habitId|date" -> { changeId }
  var POLL_INTERVAL_MS = 10000;


  /* -------------------------------------------------------------------------
     1. Habit cell toggle
     ------------------------------------------------------------------------- */

  function initToggleCheckboxes() {
    document.querySelectorAll('.habit-checkbox:not([disabled])').forEach(function (cb) {
      cb.addEventListener('change', handleToggleChange);
    });
  }

  function handleToggleChange(event) {
    var cb      = event.currentTarget;
    var habitId = cb.dataset.habitId;
    var dateStr = cb.dataset.date;
    if (!habitId || !dateStr || !username) return;

    // Browser has already toggled cb.checked. Reflect the new state immediately.
    var newCompleted = cb.checked;
    var labelName    = (cb.getAttribute('aria-label') || '').split(':')[0];
    cb.setAttribute('aria-label', labelName + ': ' + (newCompleted ? 'completed' : 'not completed'));
    updateTodayStats();

    // Record this change so the reconciler skips this cell until the request settles.
    var key      = habitId + '|' + dateStr;
    var changeId = crypto.randomUUID();
    _pendingToggles[key] = { changeId: changeId };

    var url = '/' + username + '/habit/toggle/post/' + habitId + '/' + dateStr;

    if (typeof fetch === 'function') {
      fetch(url, {
        method:      'POST',
        headers:     {
          'X-Requested-With': 'XMLHttpRequest',
          'Content-Type':     'application/x-www-form-urlencoded',
        },
        body:        'change_id=' + encodeURIComponent(changeId),
        credentials: 'same-origin',
      })
      .catch(function () {})  // errors are reconciled by the poll
      .finally(function () {
        // Only clear the pending flag if this is still the active change for this cell.
        // A later toggle on the same cell will have a higher changeId and must not be cleared.
        if (_pendingToggles[key] && _pendingToggles[key].changeId === changeId) {
          delete _pendingToggles[key];
        }
      });
    } else {
      // No fetch API: fall back to a plain form POST (navigates away).
      delete _pendingToggles[key];
      var form = document.createElement('form');
      form.method = 'POST';
      form.action = url;
      document.body.appendChild(form);
      form.submit();
    }
  }


  /* -------------------------------------------------------------------------
     2. Polling: keep habit state in sync with the server
     ------------------------------------------------------------------------- */

  function startPolling() {
    if (!document.querySelector('.habit-checkbox')) return;
    setInterval(pollHabitState, POLL_INTERVAL_MS);
  }

  function pollHabitState() {
    if (!username) return;

    var url = '/' + username + '/habit/index/json';
    if (typeof refDate !== 'undefined' && refDate) url += '?ref=' + refDate;

    fetch(url, {
      headers:     { 'X-Requested-With': 'XMLHttpRequest' },
      credentials: 'same-origin',
    })
    .then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    })
    .then(function (data) {
      reconcileHabitState(data.state || {});
    })
    .catch(function () {});
  }

  /**
   * Reconcile the DOM with the server state map.
   *
   * state: { "habitId|date": { completed: 1|0, changeId: "uuid"|null } }
   * Keys absent from state are treated as completed=0.
   * Cells with a pending local change are skipped unless the server confirms
   * the exact change (matching changeId), at which point the pending flag clears.
   */
  function reconcileHabitState(state) {
    document.querySelectorAll('.habit-checkbox').forEach(function (cb) {
      var key    = cb.dataset.habitId + '|' + cb.dataset.date;
      var entry  = state[key] || { completed: 0, changeId: null };
      var pending = _pendingToggles[key];

      if (pending) {
        // Server has confirmed our specific change — safe to clear the pending flag.
        if (entry.changeId && entry.changeId === pending.changeId) {
          delete _pendingToggles[key];
        } else {
          return;  // still in-flight; skip this cell
        }
      }

      var serverCompleted = entry.completed === 1;
      if (cb.checked !== serverCompleted) {
        cb.checked = serverCompleted;
        var name = (cb.getAttribute('aria-label') || '').split(':')[0];
        cb.setAttribute('aria-label', name + ': ' + (serverCompleted ? 'completed' : 'not completed'));
      }
    });

    updateTodayStats();
  }

  function updateTodayStats() {
    var today     = new Date().toISOString().slice(0, 10);
    var total     = 0;
    var completed = 0;

    document.querySelectorAll('.habit-checkbox').forEach(function (cb) {
      if (cb.dataset.date !== today || cb.disabled) return;
      total++;
      if (cb.checked) completed++;
    });

    var countEl = document.querySelector('.today-count');
    if (countEl) countEl.textContent = completed + '/' + total;

    var progress = document.querySelector('.habit-progress');
    if (progress) {
      progress.value = completed;
      progress.max   = total;
      progress.setAttribute('aria-label', completed + ' of ' + total + ' habits completed today');
    }
  }


  /* -------------------------------------------------------------------------
     3. Icon preview on settings page
     ------------------------------------------------------------------------- */

  function initIconPreviews() {
    document.querySelectorAll('select.icon-select').forEach(function (sel) {
      sel.addEventListener('change', function () { handleIconChange(sel); });
      handleIconChange(sel);
    });
  }

  function handleIconChange(sel) {
    var previewId = sel.dataset.preview;
    var preview;
    if (previewId) {
      preview = document.getElementById(previewId);
    } else {
      var sibling = sel.nextElementSibling;
      while (sibling) {
        if (sibling.classList.contains('icon-preview')) { preview = sibling; break; }
        sibling = sibling.nextElementSibling;
      }
      if (!preview) {
        var parent = sel.closest('.form-row');
        if (parent) {
          var next = parent.nextElementSibling;
          if (next && next.classList.contains('icon-preview')) preview = next;
        }
      }
    }

    if (!preview) return;

    var selected = sel.options[sel.selectedIndex];
    if (!selected || !selected.value) { preview.innerHTML = ''; return; }

    var iconName = selected.value;
    preview.innerHTML = '<span style="color:#6b7280;font-size:0.75rem;">Loading…</span>';

    fetch('/api/icon/' + encodeURIComponent(iconName), {
      headers:     { 'X-Requested-With': 'XMLHttpRequest' },
      credentials: 'same-origin',
    })
    .then(function (r) {
      if (!r.ok) throw new Error('Not found');
      return r.json();
    })
    .then(function (data) {
      preview.innerHTML = data.svg
        ? data.svg
        : '<span style="color:#6b7280;font-size:0.75rem;">' + iconName + '</span>';
    })
    .catch(function () {
      preview.innerHTML = '<span style="color:#6b7280;font-size:0.75rem;">' + iconName + '</span>';
    });
  }


  /* -------------------------------------------------------------------------
     4. Grid drag-to-reorder (mouse + keyboard)
     ------------------------------------------------------------------------- */

  var _draggedCell      = null;   // mouse drag source
  var _keyboardDragCell = null;   // keyboard drag source
  var _pendingPositions = {};     // habitID -> new position


  /* --- Shared move logic -------------------------------------------------- */

  function rebuildCell(cell, pos, habitId, name, bg, isOccupied) {
    var nameShort = name ? name.substring(0, 8) + (name.length > 8 ? '…' : '') : '';
    cell.innerHTML =
      '<span class="grid-pos-num">' + pos + '</span>' +
      (name ? '<span class="grid-habit-name">' + nameShort + '</span>' : '');

    cell.dataset.position      = pos;
    cell.style.backgroundColor = bg || '';

    cell.removeEventListener('dragstart',  onDragStart);
    cell.removeEventListener('dragend',    onDragEnd);
    cell.removeEventListener('keydown',    onGridCellKeyDown);

    if (isOccupied && habitId) {
      cell.dataset.habitId = habitId;
      cell.setAttribute('data-orig-name', name || '');
      cell.title = (name || habitId) + ' (pos ' + pos + ')';
      cell.setAttribute('aria-label', (name || habitId) + ', position ' + pos + '. Press Space or Enter to move.');
      cell.classList.add('occupied');
      cell.classList.remove('empty');
      cell.setAttribute('draggable', 'true');
      cell.setAttribute('tabindex', '0');
      cell.setAttribute('role', 'button');
      cell.addEventListener('dragstart', onDragStart);
      cell.addEventListener('dragend',   onDragEnd);
      cell.addEventListener('keydown',   onGridCellKeyDown);
    } else {
      delete cell.dataset.habitId;
      cell.removeAttribute('data-orig-name');
      cell.removeAttribute('aria-label');
      cell.title = 'Position ' + pos;
      cell.classList.remove('occupied');
      cell.classList.add('empty');
      cell.removeAttribute('draggable');
      cell.removeAttribute('tabindex');
      cell.removeAttribute('role');
    }
  }

  function executeGridMove(source, target) {
    var sourceId   = source.dataset.habitId;
    var sourcePos  = parseInt(source.dataset.position, 10);
    var sourceName = source.getAttribute('data-orig-name') || sourceId || '';
    var sourceBg   = source.style.backgroundColor;

    var targetPos  = parseInt(target.dataset.position, 10);
    if (!sourceId || isNaN(sourcePos) || isNaN(targetPos)) return;

    var targetId   = target.dataset.habitId;
    var targetName = target.getAttribute('data-orig-name') || targetId || '';
    var targetBg   = target.style.backgroundColor;

    if (targetId) {
      rebuildCell(source, sourcePos, targetId, targetName, targetBg, true);
      _pendingPositions[targetId] = sourcePos;
    } else {
      rebuildCell(source, sourcePos, null, '', '', false);
    }

    rebuildCell(target, targetPos, sourceId, sourceName, sourceBg, true);
    _pendingPositions[sourceId] = targetPos;

    var saveBtn = document.getElementById('save-positions');
    if (saveBtn) saveBtn.style.display = '';
  }


  /* --- Mouse drag --------------------------------------------------------- */

  function initGridDrag() {
    var grid = document.getElementById('grid-preview');
    if (!grid) return;

    grid.querySelectorAll('.grid-preview-cell.occupied').forEach(function (cell) {
      cell.addEventListener('dragstart', onDragStart);
      cell.addEventListener('dragend',   onDragEnd);
    });

    grid.querySelectorAll('.grid-preview-cell').forEach(function (cell) {
      cell.addEventListener('dragover',  onDragOver);
      cell.addEventListener('dragleave', onDragLeave);
      cell.addEventListener('drop',      onDrop);
    });

    var saveBtn = document.getElementById('save-positions');
    if (saveBtn) {
      saveBtn.addEventListener('click', function () { savePendingPositions(saveBtn); });
    }
  }

  function onDragStart(event) {
    _draggedCell = event.currentTarget;
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('text/plain', _draggedCell.dataset.habitId || '');
    setTimeout(function () { if (_draggedCell) _draggedCell.style.opacity = '0.4'; }, 0);
  }

  function onDragEnd() {
    if (_draggedCell) _draggedCell.style.opacity = '';
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
    executeGridMove(_draggedCell, target);
  }


  /* --- Keyboard drag ------------------------------------------------------ */

  function initGridKeyboard() {
    var grid = document.getElementById('grid-preview');
    if (!grid) return;

    grid.querySelectorAll('.grid-preview-cell.occupied').forEach(function (cell) {
      cell.setAttribute('tabindex', '0');
      cell.setAttribute('role', 'button');
      var name = cell.getAttribute('data-orig-name') || cell.dataset.habitId || '';
      cell.setAttribute('aria-label', name + ', position ' + cell.dataset.position + '. Press Space or Enter to move.');
      cell.addEventListener('keydown', onGridCellKeyDown);
    });
  }

  function onGridCellKeyDown(event) {
    if (event.key !== ' ' && event.key !== 'Enter' && event.key !== 'Escape') return;
    event.preventDefault();

    var cell = event.currentTarget;

    if (event.key === 'Escape') {
      cancelKeyboardDrag();
      return;
    }

    if (!_keyboardDragCell) {
      if (!cell.classList.contains('occupied')) return;
      _keyboardDragCell = cell;
      cell.classList.add('keyboard-dragging');
      document.querySelectorAll('#grid-preview .grid-preview-cell').forEach(function (c) {
        if (c === cell) return;
        c.setAttribute('tabindex', '0');
        c.setAttribute('role', 'button');
        if (!c.getAttribute('aria-label')) {
          c.setAttribute('aria-label', 'Position ' + c.dataset.position + '. Press Space or Enter to move habit here.');
        }
        c.addEventListener('keydown', onGridCellKeyDown);
      });
      updateGridStatus(
        'Moving ' + (cell.getAttribute('data-orig-name') || 'habit') +
        '. Tab to a destination and press Space or Enter to place it. Press Escape to cancel.'
      );
    } else {
      if (cell === _keyboardDragCell) { cancelKeyboardDrag(); return; }
      var source = _keyboardDragCell;
      cancelKeyboardDrag();
      executeGridMove(source, cell);
      cell.focus();
      updateGridStatus('Moved. Press Save Positions to apply changes.');
    }
  }

  function cancelKeyboardDrag() {
    if (_keyboardDragCell) {
      _keyboardDragCell.classList.remove('keyboard-dragging');
      _keyboardDragCell = null;
    }
    document.querySelectorAll('#grid-preview .grid-preview-cell.empty').forEach(function (c) {
      c.removeAttribute('tabindex');
      c.removeAttribute('role');
      c.removeAttribute('aria-label');
      c.removeEventListener('keydown', onGridCellKeyDown);
    });
    updateGridStatus('');
  }

  function updateGridStatus(msg) {
    var el = document.getElementById('grid-status');
    if (el) el.textContent = msg;
  }


  /* --- Save --------------------------------------------------------------- */

  function savePendingPositions(saveBtn) {
    if (!username) return;

    var items = Object.keys(_pendingPositions).map(function (hid) {
      return { habitID: hid, position: _pendingPositions[hid] };
    });
    if (items.length === 0) return;

    var originalText    = saveBtn.textContent;
    saveBtn.textContent = 'Saving…';
    saveBtn.disabled    = true;

    fetch('/' + username + '/habit/reorder/post', {
      method:      'POST',
      headers:     { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
      credentials: 'same-origin',
      body:        JSON.stringify(items),
    })
    .then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    })
    .then(function () {
      _pendingPositions   = {};
      saveBtn.textContent = 'Saved!';
      setTimeout(function () { window.location.reload(); }, 600);
    })
    .catch(function () {
      saveBtn.textContent = 'Error – try again';
      saveBtn.disabled    = false;
    });
  }


  /* -------------------------------------------------------------------------
     5. Grid position picker (settings page)
     ------------------------------------------------------------------------- */

  function initGridPickers() {
    document.querySelectorAll('.pos-picker').forEach(function (picker) {
      var form    = picker.closest('form');
      var habitID = picker.dataset.habitId || '';
      if (!form) return;

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

      form.querySelectorAll('input[type="checkbox"][name="dayweek"]').forEach(function (cb) {
        cb.addEventListener('change', function () {
          refreshPickerConflicts(picker, habitID);
        });
      });

      refreshPickerConflicts(picker, habitID);
    });
  }

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
          cell.title = 'Position ' + pos + ' — conflict with "' + info.name + '"';
        } else if (info) {
          cell.disabled = false;
          cell.classList.remove('conflicted');
          cell.classList.add('occupied');
          cell.title = 'Position ' + pos + ' — "' + info.name + '" (different days)';
        } else {
          cell.disabled = false;
          cell.classList.remove('conflicted', 'occupied');
          cell.title = 'Position ' + pos;
        }
      });
    })
    .catch(function () {});
  }


  /* -------------------------------------------------------------------------
     Init
     ------------------------------------------------------------------------- */

  document.addEventListener('DOMContentLoaded', function () {
    initToggleCheckboxes();
    startPolling();
    initIconPreviews();
    initGridDrag();
    initGridKeyboard();
    initGridPickers();

    document.querySelectorAll('.grid-preview-cell.occupied').forEach(function (cell) {
      var nameEl = cell.querySelector('.grid-habit-name');
      if (nameEl) cell.setAttribute('data-orig-name', nameEl.textContent);
    });
  });

}());
