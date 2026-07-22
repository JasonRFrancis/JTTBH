/**
 * JTTBH Dashboard – Client-side JavaScript
 *
 * Todo widget: auto-submit the toggle form when its checkbox changes,
 * hiding the no-JS fallback button.
 */

(function () {
  'use strict';

  document.querySelectorAll('.todo-toggle-btn').forEach(function (btn) {
    btn.hidden = true;
  });

  document.addEventListener('change', function (e) {
    if (!e.target.matches('.todo-checkbox')) return;
    var form = e.target.closest('form');
    if (form) form.requestSubmit();
  });

  /* Study widget: AJAX completion toggle (avoids navigating off the dashboard). */
  document.querySelectorAll('.study-widget .complete-form').forEach(function (form) {
    var submitBtn = form.querySelector('.complete-submit');
    if (submitBtn) submitBtn.hidden = true;

    var checkbox = form.querySelector('.complete-checkbox');
    if (!checkbox) return;

    checkbox.addEventListener('change', function () {
      var data = new URLSearchParams(new FormData(form));
      fetch(form.action, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest', 'Content-Type': 'application/x-www-form-urlencoded' },
        body: data.toString()
      })
        .then(function (r) { return r.json(); })
        .then(function (resp) {
          if (resp.status !== 'ok') { checkbox.checked = !checkbox.checked; return; }
          var li = form.closest('.source-item');
          if (li) li.classList.toggle('source-item--done', resp.done);
        })
        .catch(function () { checkbox.checked = !checkbox.checked; });
    });
  });
})();
