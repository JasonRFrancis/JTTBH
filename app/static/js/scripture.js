(function () {
  'use strict';

  if (!Array.isArray(CARDS) || CARDS.length === 0) return;

  var cards       = CARDS.slice();  // copy so we can mutate
  var total       = cards.length;
  var current     = 0;
  var reviewed    = 0;

  var shell       = document.getElementById('review-shell');
  var flashcard   = document.getElementById('flashcard');
  var modeLabel   = document.getElementById('card-mode');
  var promptEl    = document.getElementById('card-prompt');
  var showBtn     = document.getElementById('show-btn');
  var answerEl    = document.getElementById('card-answer');
  var practiceArea = document.getElementById('practice-area');
  var practiceInput = document.getElementById('practice-input');
  var revealBtn   = document.getElementById('reveal-btn');
  var answerText  = document.getElementById('answer-text');
  var gradeButtons = document.getElementById('grade-buttons');
  var progressBar = document.getElementById('progress-bar');
  var progressLabel = document.getElementById('progress-label');
  var doneScreen  = document.getElementById('review-done');
  var doneSummary = document.getElementById('done-summary');

  var MODE_LABELS = {
    reference: 'Reference mode — recall the reference',
    familiar:  'Familiar mode — recall the meaning',
    verbatim:  'Verbatim mode — recite word-for-word'
  };

  function setProgress(n, total) {
    var pct = total > 0 ? Math.round((n / total) * 100) : 0;
    progressBar.style.setProperty('--pct', pct + '%');
    progressLabel.textContent = n + ' / ' + total;
  }

  function buildPrompt(card) {
    switch (card.mode) {
      case 'reference':
        return card.text || card.summary || '(no text — recall the reference)';
      case 'familiar':
        return card.reference;
      case 'verbatim':
        return card.reference;
    }
    return '';
  }

  function buildAnswer(card) {
    switch (card.mode) {
      case 'reference':
        return card.reference;
      case 'familiar':
        return card.summary
          ? card.summary + (card.text ? '\n\n' + card.text : '')
          : card.text || '(no summary — add one when editing)';
      case 'verbatim':
        return card.text || '(no text stored — add it when editing)';
    }
    return '';
  }

  function showCard(index) {
    var card = cards[index];

    modeLabel.textContent = MODE_LABELS[card.mode] || card.mode;
    promptEl.textContent  = buildPrompt(card);

    // Reset state
    answerEl.hidden      = true;
    practiceArea.hidden  = true;
    answerText.textContent = '';
    if (practiceInput) practiceInput.value = '';
    showBtn.hidden = false;
    gradeButtons.hidden = false;

    setProgress(reviewed, total);
    flashcard.hidden = false;
  }

  function revealAnswer() {
    var card = cards[current];
    showBtn.hidden = true;
    answerEl.hidden = false;

    if (card.mode === 'verbatim') {
      practiceArea.hidden = false;
      answerText.hidden   = true;
      gradeButtons.hidden = true;
      if (practiceInput) practiceInput.focus();
    } else {
      answerText.textContent = buildAnswer(card);
      answerText.hidden = false;
    }
  }

  function revealVerbatimText() {
    var card = cards[current];
    practiceArea.hidden = false;  // keep visible so user can compare
    answerText.textContent = buildAnswer(card);
    answerText.hidden   = false;
    gradeButtons.hidden = false;
    revealBtn.disabled  = true;
  }

  function submitGrade(grade) {
    var card = cards[current];

    // Disable grade buttons while request is in flight
    Array.from(gradeButtons.querySelectorAll('.grade-btn')).forEach(function (b) {
      b.disabled = true;
    });

    fetch(GRADE_URL, {
      method:      'POST',
      headers:     {
        'Content-Type':      'application/json',
        'X-Requested-With':  'XMLHttpRequest',
      },
      credentials: 'same-origin',
      body: JSON.stringify({
        scriptureID: card.scriptureID,
        mode:        card.mode,
        grade:       grade,
      }),
    })
    .then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    })
    .then(function () {
      reviewed += 1;
      current  += 1;
      if (current < cards.length) {
        showCard(current);
      } else {
        showDone();
      }
    })
    .catch(function () {
      showMessage('Could not save grade — please try again.', 'error');
      Array.from(gradeButtons.querySelectorAll('.grade-btn')).forEach(function (b) {
        b.disabled = false;
      });
    });
  }

  function showDone() {
    flashcard.hidden  = true;
    doneScreen.hidden = false;
    setProgress(total, total);
    doneSummary.textContent =
      'You reviewed ' + reviewed + ' card' + (reviewed === 1 ? '' : 's') + '.';
  }

  // --- Event listeners ---

  showBtn.addEventListener('click', revealAnswer);

  if (revealBtn) {
    revealBtn.addEventListener('click', revealVerbatimText);
  }

  gradeButtons.addEventListener('click', function (e) {
    var btn = e.target.closest('.grade-btn');
    if (!btn) return;
    submitGrade(btn.dataset.grade);
  });

  // --- Init ---

  showCard(0);

}());
