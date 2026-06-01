/* study.js — subscription edit filter checkboxes + schedule search */

(function () {

  /* ── Subscription edit: author / category filter checkboxes ── */

  function syncHidden(cbClass, hiddenId) {
    const checked = Array.from(document.querySelectorAll('.' + cbClass + ':checked'))
      .map(cb => cb.value);
    const hidden = document.getElementById(hiddenId);
    if (hidden) hidden.value = checked.join(', ');
  }

  function wireChecklist(cbClass, hiddenId, searchId, clearBtnTarget) {
    const items = document.querySelectorAll('.' + cbClass);
    if (!items.length) return;

    items.forEach(cb => cb.addEventListener('change', () => syncHidden(cbClass, hiddenId)));
    syncHidden(cbClass, hiddenId);

    const search = document.getElementById(searchId);
    if (search) {
      search.addEventListener('input', function () {
        const q = this.value.toLowerCase();
        items.forEach(cb => {
          const li = cb.closest('li');
          if (li) li.style.display = cb.value.toLowerCase().includes(q) ? '' : 'none';
        });
      });
    }

    const clearBtn = document.querySelector('[data-target="' + clearBtnTarget + '"]');
    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        items.forEach(cb => { cb.checked = false; });
        syncHidden(cbClass, hiddenId);
      });
    }
  }

  wireChecklist('author-cb',   'filter_author_hidden',   'author-search',   'author');
  wireChecklist('category-cb', 'filter_category_hidden', 'category-search', 'category');

  /* ── Schedule page: search + show-scheduled-only ── */

  const scheduleSearch = document.getElementById('schedule-search');
  const showScheduled  = document.getElementById('show-scheduled-only');
  const scheduleItems  = document.querySelectorAll('.schedule-item');

  function filterSchedule() {
    const q = scheduleSearch ? scheduleSearch.value.toLowerCase() : '';
    const onlyScheduled = showScheduled ? showScheduled.checked : false;
    scheduleItems.forEach(item => {
      const matchText = !q ||
        (item.dataset.title || '').includes(q) ||
        (item.dataset.author || '').includes(q);
      const matchSched = !onlyScheduled || item.dataset.scheduled === '1';
      item.style.display = matchText && matchSched ? '' : 'none';
    });
  }

  if (scheduleSearch) scheduleSearch.addEventListener('input', filterSchedule);
  if (showScheduled)  showScheduled.addEventListener('change', filterSchedule);

}());
