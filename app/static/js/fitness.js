'use strict';

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

    post(window.FITNESS_URLS.weight, { weight: val, log_date: window.FITNESS_URLS.logDate })
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
  var tplMachine    = document.getElementById('tpl-set-machine');
  var tplHandWeight = document.getElementById('tpl-set-hand-weight');
  var tplBodyweight = document.getElementById('tpl-set-bodyweight');
  var tplCardio     = document.getElementById('tpl-set-cardio');
  var tplVideo      = document.getElementById('tpl-set-video');
  if (!tplMachine && !tplHandWeight && !tplBodyweight && !tplCardio && !tplVideo) return;

  // JS active: swap no-JS static forms for the dynamic btn-add-set buttons
  document.querySelectorAll('.set-form-noscript').forEach(function (f) { f.hidden = true; });
  document.querySelectorAll('.btn-add-set').forEach(function (b) { b.hidden = false; });

  function getPrefill(article) {
    var t = article.querySelector('template.prefill-data');
    if (!t) return {};
    var d = t.dataset;
    return {
      setup:    d.setup    || '',
      weight:   d.weight   || '',
      reps:     d.reps     || '',
      notes:    d.notes    || '',
      duration: d.duration || '',
      speed:    d.speed    || '',
    };
  }

  function setCount(article) {
    return article.querySelectorAll('.set-row').length;
  }

  function buildLoggedMachineRow(logSetID, setNum, weight, reps, setup, notes) {
    var summary = (weight ? Math.round(weight) : '—') + ' lbs × ' + (reps || '—');
    if (setup) summary += '<span class="set-adj"> adj ' + setup + '</span>';
    if (notes) summary += ' · <span class="set-notes">' + notes + '</span>';
    var li = document.createElement('li');
    li.className = 'set-row set-row--logged';
    li.dataset.logSetId = logSetID;
    li.innerHTML =
      '<span class="set-num">' + setNum + '</span>' +
      '<span class="set-summary">' + summary + '</span>' +
      '<button class="btn-delete-set" type="button" data-log-set-id="' + logSetID + '" aria-label="Delete set">×</button>';
    return li;
  }

  function buildLoggedHandWeightRow(logSetID, setNum, weight, reps, notes) {
    var summary = (weight ? Math.round(weight) : '—') + ' lbs × ' + (reps || '—');
    if (notes) summary += ' · <span class="set-notes">' + notes + '</span>';
    var li = document.createElement('li');
    li.className = 'set-row set-row--logged';
    li.dataset.logSetId = logSetID;
    li.innerHTML =
      '<span class="set-num">' + setNum + '</span>' +
      '<span class="set-summary">' + summary + '</span>' +
      '<button class="btn-delete-set" type="button" data-log-set-id="' + logSetID + '" aria-label="Delete set">×</button>';
    return li;
  }

  function buildLoggedBodyweightRow(logSetID, setNum, reps, duration, notes) {
    var parts = [];
    if (reps)     parts.push(reps + ' reps');
    if (duration) parts.push(duration + 's');
    if (notes)    parts.push('<span class="set-notes">' + notes + '</span>');
    var li = document.createElement('li');
    li.className = 'set-row set-row--logged';
    li.dataset.logSetId = logSetID;
    li.innerHTML =
      '<span class="set-num">' + setNum + '</span>' +
      '<span class="set-summary">' + (parts.join(' · ') || '—') + '</span>' +
      '<button class="btn-delete-set" type="button" data-log-set-id="' + logSetID + '" aria-label="Delete set">×</button>';
    return li;
  }

  function buildLoggedCardioRow(logSetID, setup, duration, speed, notes) {
    var parts = [];
    if (duration) parts.push(duration + ' min');
    if (speed)    parts.push(speed + ' mph');
    if (setup)    parts.push('<span class="set-adj">' + setup + '</span>');
    if (notes)    parts.push('<span class="set-notes">' + notes + '</span>');
    var li = document.createElement('li');
    li.className = 'set-row set-row--logged';
    li.dataset.logSetId = logSetID;
    li.innerHTML =
      '<span class="set-summary">' + (parts.join(' · ') || '—') + '</span>' +
      '<button class="btn-delete-set" type="button" data-log-set-id="' + logSetID + '" aria-label="Delete">×</button>';
    return li;
  }

  function buildLoggedVideoRow(logSetID, notes) {
    var summary = 'Done';
    if (notes) summary += ' · <span class="set-notes">' + notes + '</span>';
    var li = document.createElement('li');
    li.className = 'set-row set-row--logged';
    li.dataset.logSetId = logSetID;
    li.innerHTML =
      '<span class="set-summary">' + summary + '</span>' +
      '<button class="btn-delete-set" type="button" data-log-set-id="' + logSetID + '" aria-label="Delete">×</button>';
    return li;
  }

  /* + Set / + Log / ✓ Mark Done */
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.btn-add-set');
    if (!btn) return;

    var article = btn.closest('.exercise');
    var type    = btn.dataset.exerciseType || 'machine';
    var tpl;
    if      (type === 'machine')     tpl = tplMachine;
    else if (type === 'hand_weight') tpl = tplHandWeight;
    else if (type === 'bodyweight')  tpl = tplBodyweight;
    else if (type === 'cardio')      tpl = tplCardio;
    else if (type === 'video')       tpl = tplVideo;
    if (!tpl) return;

    var clone   = tpl.content.cloneNode(true);
    var li      = clone.querySelector('li');
    var prefill = getPrefill(article);
    var setNum  = setCount(article) + 1;

    if (type === 'machine') {
      li.querySelector('.set-num').textContent = setNum;
      li.querySelector('.inp-setup').value     = prefill.setup;
      li.querySelector('.inp-weight').value    = prefill.weight;
      li.querySelector('.inp-reps').value      = prefill.reps;
      li.querySelector('.inp-notes').value     = prefill.notes;
      li.querySelector('.inp-weight').focus();
    } else if (type === 'hand_weight') {
      li.querySelector('.set-num').textContent = setNum;
      li.querySelector('.inp-weight').value    = prefill.weight;
      li.querySelector('.inp-reps').value      = prefill.reps;
      li.querySelector('.inp-notes').value     = prefill.notes;
      li.querySelector('.inp-weight').focus();
    } else if (type === 'bodyweight') {
      li.querySelector('.set-num').textContent  = setNum;
      li.querySelector('.inp-reps').value       = prefill.reps;
      li.querySelector('.inp-duration').value   = prefill.duration;
      li.querySelector('.inp-notes').value      = prefill.notes;
      li.querySelector('.inp-reps').focus();
    } else if (type === 'cardio') {
      li.querySelector('.inp-setup').value    = prefill.setup;
      li.querySelector('.inp-duration').value = prefill.duration;
      li.querySelector('.inp-speed').value    = prefill.speed;
      li.querySelector('.inp-notes').value    = prefill.notes;
      li.querySelector('.inp-duration').focus();
    } else if (type === 'video') {
      li.querySelector('.inp-notes').focus();
    }

    article.querySelector('.set-list').appendChild(li);
    btn.style.display = 'none';
  });

  /* Confirm (✓) */
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.btn-confirm-set');
    if (!btn) return;

    var li      = btn.closest('.set-row');
    var article = li.closest('.exercise');
    var exId    = article.dataset.exerciseId;
    var type    = article.dataset.exerciseType || 'machine';
    var data    = { exercise_id: exId, log_date: window.FITNESS_URLS.logDate };

    if (type === 'machine') {
      data.set_number = article.querySelectorAll('.set-row--logged').length + 1;
      data.weight     = li.querySelector('.inp-weight').value || '';
      data.reps       = li.querySelector('.inp-reps').value   || '';
      data.setup      = li.querySelector('.inp-setup').value  || '';
      data.notes      = li.querySelector('.inp-notes').value  || '';
    } else if (type === 'hand_weight') {
      data.set_number = article.querySelectorAll('.set-row--logged').length + 1;
      data.weight     = li.querySelector('.inp-weight').value || '';
      data.reps       = li.querySelector('.inp-reps').value   || '';
      data.notes      = li.querySelector('.inp-notes').value  || '';
    } else if (type === 'bodyweight') {
      data.set_number = article.querySelectorAll('.set-row--logged').length + 1;
      data.reps       = li.querySelector('.inp-reps').value     || '';
      data.duration   = li.querySelector('.inp-duration').value || '';
      data.notes      = li.querySelector('.inp-notes').value    || '';
    } else if (type === 'cardio') {
      data.setup    = li.querySelector('.inp-setup').value    || '';
      data.duration = li.querySelector('.inp-duration').value || '';
      data.speed    = li.querySelector('.inp-speed').value    || '';
      data.notes    = li.querySelector('.inp-notes').value    || '';
    } else if (type === 'video') {
      data.notes = li.querySelector('.inp-notes').value || '';
    }

    li.classList.add('set-row--saving');

    post(window.FITNESS_URLS.logSet, data)
      .then(function (res) {
        if (res.status !== 'ok') { li.classList.remove('set-row--saving'); return; }

        var logSetID     = res.logSetID;
        var setNum       = article.querySelectorAll('.set-row--logged').length + 1;
        var prefillTpl   = article.querySelector('template.prefill-data');
        var logged;

        if (type === 'machine') {
          logged = buildLoggedMachineRow(logSetID, setNum, data.weight, data.reps, data.setup, data.notes);
          if (prefillTpl) {
            prefillTpl.dataset.weight = data.weight;
            prefillTpl.dataset.reps   = data.reps;
            prefillTpl.dataset.setup  = data.setup;
            prefillTpl.dataset.notes  = data.notes;
          }
        } else if (type === 'hand_weight') {
          logged = buildLoggedHandWeightRow(logSetID, setNum, data.weight, data.reps, data.notes);
          if (prefillTpl) {
            prefillTpl.dataset.weight = data.weight;
            prefillTpl.dataset.reps   = data.reps;
            prefillTpl.dataset.notes  = data.notes;
          }
        } else if (type === 'bodyweight') {
          logged = buildLoggedBodyweightRow(logSetID, setNum, data.reps, data.duration, data.notes);
          if (prefillTpl) {
            prefillTpl.dataset.reps     = data.reps;
            prefillTpl.dataset.duration = data.duration;
            prefillTpl.dataset.notes    = data.notes;
          }
        } else if (type === 'cardio') {
          logged = buildLoggedCardioRow(logSetID, data.setup, data.duration, data.speed, data.notes);
          if (prefillTpl) {
            prefillTpl.dataset.setup     = data.setup;
            prefillTpl.dataset.duration  = data.duration;
            prefillTpl.dataset.speed     = data.speed;
            prefillTpl.dataset.notes     = data.notes;
          }
        } else if (type === 'video') {
          logged = buildLoggedVideoRow(logSetID, data.notes);
        }

        if (logged) li.replaceWith(logged);

        var addBtn = article.querySelector('.btn-add-set');
        if (addBtn && type === 'video') addBtn.textContent = '✓ Done again';
        if (addBtn) addBtn.style.display = '';
      })
      .catch(function () { li.classList.remove('set-row--saving'); });
  });

  /* Cancel (×) on new row */
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.btn-cancel-set');
    if (!btn) return;
    var li      = btn.closest('.set-row');
    var article = li.closest('.exercise');
    li.remove();
    var addBtn = article.querySelector('.btn-add-set');
    if (addBtn) addBtn.style.display = '';
  });

  /* Delete (×) on logged row */
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

      tabs.forEach(function (t) {
        t.classList.toggle('day-tab--active', t === tab);
        t.setAttribute('aria-selected', t === tab ? 'true' : 'false');
      });

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
      var opt  = sel.options[sel.selectedIndex];
      var type = opt ? (opt.dataset.type || '') : '';

      var setupF     = form.querySelector('.setup-field');
      var setsRepsF  = form.querySelector('.sets-reps-fields');
      var weightF    = form.querySelector('.weight-field');
      var cardioF    = form.querySelector('.cardio-fields');

      if (setupF)    setupF.hidden    = !(type === 'machine' || type === 'cardio');
      if (setsRepsF) setsRepsF.hidden = !(type === 'machine' || type === 'hand_weight' || type === 'bodyweight');
      if (weightF)   weightF.hidden   = !(type === 'machine' || type === 'hand_weight');
      if (cardioF)   cardioF.hidden   = type !== 'cardio';
    }

    sel.addEventListener('change', update);
    update();
  });
})();
