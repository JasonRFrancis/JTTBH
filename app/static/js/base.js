/**
 * JTTBH – base.js
 * ================
 * Minimal, vanilla JS loaded on every page.
 *
 * Features
 * --------
 * - Flash message auto-dismiss (5 s fade-out then remove).
 * - CSRF helper (get form data including hidden fields).
 *
 * Progressive enhancement only: all functionality is additive.
 * The page works fully without JS.
 */

'use strict';

/* ------------------------------------------------------------------ */
/* Flash message auto-dismiss                                          */
/* ------------------------------------------------------------------ */

(function initFlashDismiss() {
  const FADE_DELAY  = 5000;  // ms before fade starts
  const FADE_DURATION = 400; // ms for the CSS transition

  /**
   * Schedule auto-dismissal for a single flash message element.
   * @param {HTMLElement} el
   */
  function scheduleMessageDismiss(el) {
    setTimeout(function () {
      el.style.transition = 'opacity ' + FADE_DURATION + 'ms ease';
      el.style.opacity = '0';
      setTimeout(function () {
        if (el.parentNode) {
          el.parentNode.removeChild(el);
        }
      }, FADE_DURATION);
    }, FADE_DELAY);
  }

  // Process messages already in the DOM on page load
  var messages = document.querySelectorAll('.message');
  messages.forEach(scheduleMessageDismiss);

  // Watch for dynamically inserted messages (e.g. from fetch responses)
  var container = document.querySelector('.messages');
  if (container && typeof MutationObserver !== 'undefined') {
    var observer = new MutationObserver(function (mutations) {
      mutations.forEach(function (mutation) {
        mutation.addedNodes.forEach(function (node) {
          if (node.nodeType === Node.ELEMENT_NODE &&
              node.classList.contains('message')) {
            scheduleMessageDismiss(node);
          }
        });
      });
    });
    observer.observe(container, { childList: true });
  }
}());


/* ------------------------------------------------------------------ */
/* Flash message insert helper                                         */
/* ------------------------------------------------------------------ */

/**
 * Programmatically insert a flash-style message into the .messages
 * section.  Creates the section if it does not exist.
 *
 * @param {string} text     – Message text to display.
 * @param {string} category – 'success' | 'error' | 'warning' | 'message'
 */
function showMessage(text, category) {
  category = category || 'message';

  var container = document.querySelector('.messages');

  if (!container) {
    container = document.createElement('section');
    container.className = 'messages';
    container.setAttribute('aria-live', 'polite');
    container.setAttribute('aria-label', 'Notifications');

    // Insert before <main>, or fall back to body prepend
    var main = document.querySelector('main');
    if (main && main.parentNode) {
      main.parentNode.insertBefore(container, main);
    } else {
      document.body.insertBefore(container, document.body.firstChild);
    }
  }

  var el = document.createElement('p');
  el.className = 'message message--' + category;
  el.setAttribute('role', 'alert');
  el.textContent = text;

  container.appendChild(el);
}

// Expose globally so feature JS can call showMessage(...)
window.showMessage = showMessage;


/* ------------------------------------------------------------------ */
/* Form helpers                                                        */
/* ------------------------------------------------------------------ */

/**
 * Collect all name/value pairs from a <form> element, including hidden
 * fields, as a plain object.  Does NOT include file inputs.
 *
 * @param {HTMLFormElement} form
 * @returns {Object}
 */
function getFormData(form) {
  var data = {};
  var elements = form.elements;
  for (var i = 0; i < elements.length; i++) {
    var el = elements[i];
    if (!el.name || el.disabled) continue;
    if (el.type === 'checkbox' || el.type === 'radio') {
      if (el.checked) data[el.name] = el.value;
      continue;
    }
    if (el.type === 'file') continue;
    data[el.name] = el.value;
  }
  return data;
}

/**
 * Build a FormData object from a plain key-value object.
 *
 * @param {Object} data
 * @returns {FormData}
 */
function buildFormData(data) {
  var fd = new FormData();
  Object.keys(data).forEach(function (key) {
    fd.append(key, data[key]);
  });
  return fd;
}

// Expose helpers globally for feature JS
window.jttbh = window.jttbh || {};
window.jttbh.getFormData  = getFormData;
window.jttbh.buildFormData = buildFormData;
window.jttbh.showMessage  = showMessage;
