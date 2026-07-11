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
    // JS active: hide the no-JS submit buttons; label/checkbox handles clicks
    document.querySelectorAll('.habit-toggle-btn').forEach(function (btn) {
      btn.hidden = true;
    });
    document.querySelectorAll('.habit-checkbox:not([disabled])').forEach(function (cb) {
      cb.addEventListener('change', handleToggleChange);
    });
  }

  // Safety net: these forms should never actually submit — the checkbox's
  // 'change' handler above is what drives the toggle. If a submit slips
  // through anyway (Enter pressed while a form control has focus, or the
  // hidden fallback button was clicked before hiding it took effect),
  // intercept it here instead of letting the browser navigate away via the
  // no-JS PRG redirect.
  document.addEventListener('submit', function (e) {
    var cb = e.target.querySelector && e.target.querySelector('.habit-checkbox:not([disabled])');
    if (!cb) return;
    e.preventDefault();
    cb.checked = !cb.checked;
    handleToggleChange({ currentTarget: cb });
  });

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

    var url = cb.closest('form').action;

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
      // No fetch API: submit the existing form (navigates away).
      delete _pendingToggles[key];
      cb.closest('form').submit();
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
     4. Position swap list (settings page)
     ------------------------------------------------------------------------- */

  var _swapSource       = null;  // { habitId, position, element }
  var _pendingPositions = {};    // habitID -> new position


  function initPositionList() {
    var list    = document.getElementById('position-list');
    var saveBtn = document.getElementById('save-positions');
    if (!list) return;

    list.querySelectorAll('.swap-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        onSwapClick(btn.closest('.position-row'));
      });
    });

    if (saveBtn) {
      saveBtn.addEventListener('click', function () { savePendingPositions(saveBtn); });
    }
  }

  function onSwapClick(row) {
    if (!row) return;
    var habitId  = row.dataset.habitId;
    var btn      = row.querySelector('.swap-btn');
    var name     = (row.querySelector('.pos-name') || {}).textContent || habitId;

    if (!_swapSource) {
      _swapSource = { habitId: habitId, element: row };
      row.classList.add('swap-selected');
      if (btn) btn.textContent = 'Cancel';
      updateGridStatus('Swap "' + name.trim() + '" — click another habit\'s Swap button to exchange positions, or Cancel to abort.');
    } else if (_swapSource.habitId === habitId) {
      cancelSwap();
    } else {
      var sourceRow   = _swapSource.element;
      var sourcePosEl = sourceRow.querySelector('.pos-badge');
      var targetPosEl = row.querySelector('.pos-badge');
      var sourcePos   = parseInt(sourceRow.dataset.position, 10);
      var targetPos   = parseInt(row.dataset.position, 10);

      // Exchange positions in the DOM
      sourceRow.dataset.position = targetPos;
      row.dataset.position       = sourcePos;
      if (sourcePosEl) sourcePosEl.textContent = targetPos;
      if (targetPosEl) targetPosEl.textContent = sourcePos;

      // Track for save
      _pendingPositions[_swapSource.habitId] = targetPos;
      _pendingPositions[habitId]             = sourcePos;

      resortPositionList();
      cancelSwap();

      updateGridStatus('Positions swapped. Click Save Positions to apply.');
      var saveBtn = document.getElementById('save-positions');
      if (saveBtn) saveBtn.style.display = '';
    }
  }

  function cancelSwap() {
    if (_swapSource) {
      _swapSource.element.classList.remove('swap-selected');
      var btn = _swapSource.element.querySelector('.swap-btn');
      if (btn) btn.textContent = 'Swap';
      _swapSource = null;
    }
    updateGridStatus('');
  }

  function resortPositionList() {
    var list = document.getElementById('position-list');
    if (!list) return;
    var rows = Array.from(list.querySelectorAll('.position-row'));
    rows.sort(function (a, b) {
      return parseInt(a.dataset.position, 10) - parseInt(b.dataset.position, 10);
    });
    rows.forEach(function (row) { list.appendChild(row); });
  }

  function updateGridStatus(msg) {
    var el = document.getElementById('grid-status');
    if (el) el.textContent = msg;
  }

  function savePendingPositions(saveBtn) {
    if (!username) return;

    var items = Object.keys(_pendingPositions).map(function (hid) {
      return { habitID: hid, position: _pendingPositions[hid] };
    });
    if (items.length === 0) return;

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
    initPositionList();
    initGridPickers();
  });

}());
