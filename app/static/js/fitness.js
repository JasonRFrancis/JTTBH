'use strict';

/**
 * fitness.js
 * ----------
 * Handles inline set logging on the fitness index page and
 * day-tab navigation on the settings page.
 *
 * No polling — each action is fire-and-forget with optimistic UI.
 */

/* ── Helpers ─────────────────────────────────────────────────────────── */

function post(url, data) {
  return fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'X-Requested-With': 'XMLHttpRequest',
    },
    body: new URLSearchParams(data).toString(),
  }).then(function (r) { return r.json(); });
}

/* ── Body weight form ────────────────────────────────────────────────── */

(function initBodyWeight() {
  var form = document.getElementById('bw-form');
  if (!form) return;

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var input = form.querySelector('#bw-input');
    var val = parseFloat(input.value);
    if (!val || val <= 0) return;

    post(window.FITNESS_URLS.weight, { weight: val })
      .then(function (res) {
        if (res.status === 'ok') {
          var saved = document.getElementById('bw-saved');
          saved.textContent = res.weight + ' lbs recorded';
          saved.removeAttribute('hidden');
        }
      })
      .catch(function () {});
  });
})();

/* ── Inline set logging ──────────────────────────────────────────────── */

(function initSetLogging() {
  var tplStrength = document.getElementById('tpl-set-strength');
  var tplCardio   = document.getElementById('tpl-set-cardio');
  if (!tplStrength && !tplCardio) return;

  /* Read prefill data from the <template class="prefill-data"> inside an exercise article */
  function getPrefill(article) {
    var t = article.querySelector('template.prefill-data');
    if (!t) return {};
    var d = t.dataset;
    return {
      weight:   d.weight   || '',
      reps:     d.reps     || '',
      notes:    d.notes    || '',
      duration: d.duration || '',
      speed:    d.speed    || '',
      incline:  d.incline  || '',
    };
  }

  /* Count current (logged + pending) sets for an exercise article */
  function setCount(article) {
    return article.querySelectorAll('.set-row').length;
  }

  /* Build a logged (read-only) strength set row */
  function buildLoggedStrengthRow(logSetID, setNum, weight, reps, notes) {
    var summary = (weight ? Math.round(weight) : '—') + ' lbs × ' + (reps || '—');
    if (notes) summary += ' · <span class="set-adj">' + notes + '</span>';
    var li = document.createElement('li');
    li.className = 'set-row set-row--logged';
    li.dataset.logSetId = logSetID;
    li.innerHTML =
      '<span class="set-num">' + setNum + '</span>' +
      '<span class="set-summary">' + summary + '</span>' +
      '<button class="btn-delete-set" type="button" data-log-set-id="' + logSetID + '" aria-label="Delete set">×</button>';
    return li;
  }

  /* Build a logged (read-only) cardio row */
  function buildLoggedCardioRow(logSetID, duration, speed, incline) {
    var parts = [];
    if (duration) parts.push(duration + ' min');
    if (speed)    parts.push(speed + ' mph');
    if (incline)  parts.push(Math.round(incline) + '°');
    var li = document.createElement('li');
    li.className = 'set-row set-row--logged';
    li.dataset.logSetId = logSetID;
    li.innerHTML =
      '<span class="set-summary">' + (parts.join(' · ') || '—') + '</span>' +
      '<button class="btn-delete-set" type="button" data-log-set-id="' + logSetID + '" aria-label="Delete">×</button>';
    return li;
  }

  /* Handle "+ Set" / "+ Log" button clicks */
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.btn-add-set');
    if (!btn) return;

    var article  = btn.closest('.exercise');
    var type     = btn.dataset.exerciseType || 'strength';
    var isCardio = type === 'cardio';
    var tpl      = isCardio ? tplCardio : tplStrength;
    if (!tpl) return;

    var clone = tpl.content.cloneNode(true);
    var li    = clone.querySelector('li');
    var prefill = getPrefill(article);

    if (isCardio) {
      li.querySelector('.inp-duration').value = prefill.duration;
      li.querySelector('.inp-speed').value    = prefill.speed;
      li.querySelector('.inp-incline').value  = prefill.incline;
      li.querySelector('.inp-duration').focus();
    } else {
      var setNum = setCount(article) + 1;
      li.querySelector('.set-num').textContent = setNum;
      li.querySelector('.inp-weight').value = prefill.weight;
      li.querySelector('.inp-reps').value   = prefill.reps;
      li.querySelector('.inp-notes').value  = prefill.notes;
      li.querySelector('.inp-weight').focus();
    }

    var list = article.querySelector('.set-list');
    list.appendChild(li);
    btn.style.display = 'none'; // hide while entry row is open
  });

  /* Handle confirm (✓) button */
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.btn-confirm-set');
    if (!btn) return;

    var li      = btn.closest('.set-row');
    var article = li.closest('.exercise');
    var exId    = article.dataset.exerciseId;
    var type    = article.dataset.exerciseType || 'strength';
    var isCardio = type === 'cardio';

    var data = { exercise_id: exId };

    if (isCardio) {
      data.duration = li.querySelector('.inp-duration').value || '';
      data.speed    = li.querySelector('.inp-speed').value    || '';
      data.incline  = li.querySelector('.inp-incline').value  || '';
    } else {
      data.set_number = article.querySelectorAll('.set-row--logged').length + 1;
      data.weight     = li.querySelector('.inp-weight').value || '';
      data.reps       = li.querySelector('.inp-reps').value   || '';
      data.notes      = li.querySelector('.inp-notes').value  || '';
    }

    li.classList.add('set-row--saving');

    post(window.FITNESS_URLS.logSet, data)
      .then(function (res) {
        if (res.status !== 'ok') { li.classList.remove('set-row--saving'); return; }

        // Replace entry row with logged (read-only) row
        var logSetID = res.logSetID;
        var setNum = article.querySelectorAll('.set-row--logged').length + 1;
        var logged;

        if (isCardio) {
          logged = buildLoggedCardioRow(logSetID,
            data.duration, data.speed, data.incline);
        } else {
          logged = buildLoggedStrengthRow(logSetID, setNum, data.weight, data.reps, data.notes);
          // Update prefill template with just-logged values
          var t = article.querySelector('template.prefill-data');
          if (t) {
            t.dataset.weight = data.weight;
            t.dataset.reps   = data.reps;
            t.dataset.notes  = data.notes;
          }
        }

        li.replaceWith(logged);

        // Show "+ Set" button again
        var addBtn = article.querySelector('.btn-add-set');
        if (addBtn) addBtn.style.display = '';
      })
      .catch(function () { li.classList.remove('set-row--saving'); });
  });

  /* Handle cancel (×) on new row */
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.btn-cancel-set');
    if (!btn) return;
    var li = btn.closest('.set-row');
    var article = li.closest('.exercise');
    li.remove();
    var addBtn = article.querySelector('.btn-add-set');
    if (addBtn) addBtn.style.display = '';
  });

  /* Handle delete (×) on logged row */
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.btn-delete-set');
    if (!btn) return;
    var logSetID = btn.dataset.logSetId;
    if (!logSetID) return;
    var li  = btn.closest('.set-row');
    var url = window.FITNESS_URLS.deleteSet.replace('SETID', logSetID);
    li.classList.add('set-row--saving');
    post(url, {})
      .then(function (res) {
        if (res.status === 'ok') li.remove();
        else li.classList.remove('set-row--saving');
      })
      .catch(function () { li.classList.remove('set-row--saving'); });
  });
})();

/* ── Settings day tabs ───────────────────────────────────────────────── */

(function initDayTabs() {
  var tabs = document.querySelectorAll('.day-tab');
  if (!tabs.length) return;

  tabs.forEach(function (tab) {
    tab.addEventListener('click', function () {
      var day = tab.dataset.day;

      // Toggle tabs
      tabs.forEach(function (t) {
        t.classList.toggle('day-tab--active', t === tab);
        t.setAttribute('aria-selected', t === tab ? 'true' : 'false');
      });

      // Toggle panels
      document.querySelectorAll('.day-panel').forEach(function (panel) {
        panel.classList.toggle('day-panel--hidden', panel.dataset.day !== day);
      });
    });
  });
})();

/* ── Settings exercise type toggle ──────────────────────────────────── */

(function initExerciseTypeToggle() {
  document.querySelectorAll('.exercise-select').forEach(function (sel) {
    var form = sel.closest('form');
    if (!form) return;

    function update() {
      var opt = sel.options[sel.selectedIndex];
      var type = opt ? (opt.dataset.type || 'strength') : 'strength';
      var isCardio = type === 'cardio';
      var sf = form.querySelector('.strength-fields');
      var cf = form.querySelector('.cardio-fields');
      if (sf) sf.hidden = isCardio;
      if (cf) cf.hidden = !isCardio;
    }

    sel.addEventListener('change', update);
    update();
  });
})();
