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
})();
