// quote.js — tag chips for quote forms

function initTagChips() {
  document.querySelectorAll('.tag-chips-field').forEach(field => {
    const hidden = field.querySelector('input[type="hidden"]');
    const input = field.querySelector('.tag-chips-input');
    const chipList = field.querySelector('.tag-chips-list');
    if (!hidden || !input || !chipList) return;

    // Parse existing value from hidden input into chips
    function renderChips(tags) {
      chipList.innerHTML = '';
      tags.forEach(tag => {
        if (!tag.trim()) return;
        const chip = document.createElement('span');
        chip.className = 'tag-chip-item';
        chip.textContent = tag.trim();
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'tag-chip-remove';
        btn.textContent = '×';
        btn.setAttribute('aria-label', 'Remove ' + tag.trim());
        btn.addEventListener('click', () => {
          const current = getTags();
          updateTags(current.filter(t => t !== tag.trim()));
        });
        chip.appendChild(btn);
        chipList.appendChild(chip);
      });
    }

    function getTags() {
      return hidden.value ? hidden.value.split(',').map(t => t.trim()).filter(Boolean) : [];
    }

    function updateTags(tags) {
      const unique = [...new Set(tags.map(t => t.replace(/\s+/g, '').trim()).filter(Boolean))];
      hidden.value = unique.join(',');
      renderChips(unique);
    }

    // Init from existing value
    updateTags(getTags());

    // Convert to chip on comma, space, or Enter
    input.addEventListener('keydown', e => {
      if (e.key === ',' || e.key === ' ' || e.key === 'Enter') {
        e.preventDefault();
        const val = input.value.replace(/[, ]+/g, '').trim();
        if (val) {
          const tags = getTags();
          if (!tags.includes(val)) tags.push(val);
          updateTags(tags);
          input.value = '';
        }
      }
      if (e.key === 'Backspace' && !input.value) {
        const tags = getTags();
        if (tags.length) { updateTags(tags.slice(0, -1)); }
      }
    });

    // Also convert on blur
    input.addEventListener('blur', () => {
      const val = input.value.replace(/[, ]+/g, '').trim();
      if (val) {
        const tags = getTags();
        if (!tags.includes(val)) tags.push(val);
        updateTags(tags);
        input.value = '';
      }
    });
  });
}

// Pre-seeded gospel-principles categories for autocomplete
const GOSPEL_TAGS = [
  'God','Jesus Christ','Holy Ghost','Scripture','Prayer','Faith','Repentance',
  'Baptism','Confirmation','Atonement','Resurrection','Eternal Life',
  'Agency','Obedience','Commandments','Tithing','Fasting','Sabbath',
  'Priesthood','Ordinances','Covenants','Temple','Marriage','Family',
  'Parenting','Service','Charity','Love','Humility','Honesty',
  'Forgiveness','Gratitude','Wisdom','Knowledge','Intelligence',
  'Revelation','Prophecy','Church','Missionary','Word of Wisdom',
  'Eternal Progression','Plan of Salvation','Creation','Spirit World',
  'Judgment','Kingdoms of Glory','Second Coming','Millennium','Death',
  'Premortal Life','Apostasy','Restoration','Book of Mormon','Prophets'
];

function initTagAutocomplete() {
  document.querySelectorAll('.tag-chips-input[list]').forEach(input => {
    const listId = input.getAttribute('list');
    let dl = document.getElementById(listId);
    if (!dl) {
      dl = document.createElement('datalist');
      dl.id = listId;
      document.body.appendChild(dl);
    }
    // Get existing tags from the page
    const existing = [];
    document.querySelectorAll('.tag-pill, .tag-chip').forEach(el => {
      const text = el.textContent.trim();
      if (text && text !== 'All' && !existing.includes(text)) existing.push(text);
    });
    const all = [...new Set([...GOSPEL_TAGS, ...existing])].sort();
    dl.innerHTML = all.map(t => `<option value="${t}">`).join('');
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => { initTagChips(); initTagAutocomplete(); });
} else {
  initTagChips();
  initTagAutocomplete();
}
