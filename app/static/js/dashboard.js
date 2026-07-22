/**
 * JTTBH Dashboard – Client-side JavaScript
 *
 * Todo widget: AJAX toggle (avoids navigating off the dashboard).
 * Study widget: AJAX completion toggle (avoids navigating off the dashboard).
 * Habit widget: count-only listener (habit.js owns the actual toggle).
 *
 * Every checkbox change updates its widget's count instantly. A periodic
 * poll of /dashboard/index/json then reconciles each widget's full item
 * list against the server — added/removed/edited items from other tabs
 * appear here too. Server rows are already "latest wins" (insert-only
 * tables are read via MAX(id) per item), so the client just mirrors
 * whatever the poll returns; the only local exception is an item with an
 * in-flight optimistic toggle, which is left alone until its request
 * settles so a slightly-stale poll can't stomp on it.
 */

(function () {
  'use strict';

  var POLL_INTERVAL_MS = 30000;
  var username = location.pathname.split('/')[1];
  var todayDateEl = document.querySelector('.today-date');
  var todayStr = todayDateEl
    ? todayDateEl.getAttribute('datetime')
    : new Date().toISOString().slice(0, 10);

  var pendingTodoIds  = new Set();
  var pendingStudyIds = new Set();

  /* -------------------------------------------------------------------------
     Habit widget: habit.js owns the toggle itself; just keep the count in sync.
     ------------------------------------------------------------------------- */

  function updateHabitMeta() {
    var boxes = document.querySelectorAll('.habit-checkbox');
    var el = document.getElementById('habit-widget-meta');
    if (!el || !boxes.length) return;
    var completed = 0;
    boxes.forEach(function (cb) { if (cb.checked) completed++; });
    el.textContent = completed + '/' + boxes.length + ' today';
  }

  document.addEventListener('change', function (e) {
    if (e.target.matches('.habit-checkbox')) updateHabitMeta();
  });

  /* -------------------------------------------------------------------------
     Todo widget
     ------------------------------------------------------------------------- */

  function todoToggleUrl(todoId) {
    return '/' + username + '/todo/toggle/post/' + todoId;
  }

  function updateTodoMeta() {
    var boxes = document.querySelectorAll('.todo-checkbox');
    var el = document.getElementById('todo-widget-count');
    if (!el) return;
    var completed = 0;
    boxes.forEach(function (cb) { if (cb.checked) completed++; });
    el.textContent = completed + '/' + boxes.length;
  }

  function bindTodoCheckbox(checkbox) {
    var form = checkbox.closest('form');

    checkbox.addEventListener('change', function () {
      var li = checkbox.closest('.todo-item');
      var todoId = checkbox.dataset.todoId;

      if (todoId) pendingTodoIds.add(todoId);
      if (li) li.classList.toggle('todo-item--done', checkbox.checked);
      updateTodoMeta();

      fetch(form.action, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        credentials: 'same-origin'
      })
        .then(function (r) { return r.json(); })
        .then(function (resp) {
          if (resp.status !== 'ok') throw new Error('toggle failed');
          if (resp.completed !== checkbox.checked) {
            checkbox.checked = resp.completed;
            if (li) li.classList.toggle('todo-item--done', checkbox.checked);
            updateTodoMeta();
          }
        })
        .catch(function () {
          checkbox.checked = !checkbox.checked;
          if (li) li.classList.toggle('todo-item--done', checkbox.checked);
          updateTodoMeta();
        })
        .finally(function () { if (todoId) pendingTodoIds.delete(todoId); });
    });
  }

  function buildTodoItem(todo) {
    var li = document.createElement('li');
    li.className = 'todo-item' + (todo.completed ? ' todo-item--done' : '');
    li.dataset.todoId = todo.todoID;

    var form = document.createElement('form');
    form.method = 'post';
    form.action = todoToggleUrl(todo.todoID);

    var label = document.createElement('label');
    label.className = 'todo-label';

    var checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.className = 'todo-checkbox';
    checkbox.dataset.todoId = todo.todoID;
    checkbox.checked = !!todo.completed;
    checkbox.setAttribute('aria-label', todo.title);

    var titleSpan = document.createElement('span');
    titleSpan.className = 'todo-title';
    titleSpan.textContent = todo.title;

    label.appendChild(checkbox);
    label.appendChild(titleSpan);

    var toggleBtn = document.createElement('button');
    toggleBtn.type = 'submit';
    toggleBtn.className = 'todo-toggle-btn';
    toggleBtn.textContent = 'Toggle';
    toggleBtn.hidden = true;

    form.appendChild(label);
    form.appendChild(toggleBtn);
    li.appendChild(form);

    if (todo.content) {
      var p = document.createElement('p');
      p.className = 'todo-content';
      p.textContent = todo.content;
      li.appendChild(p);
    }

    bindTodoCheckbox(checkbox);
    return li;
  }

  function updateTodoItemInPlace(li, todo) {
    li.classList.toggle('todo-item--done', todo.completed);

    var cb = li.querySelector('.todo-checkbox');
    if (cb) cb.checked = todo.completed;

    var titleEl = li.querySelector('.todo-title');
    if (titleEl && titleEl.textContent !== todo.title) titleEl.textContent = todo.title;

    var contentEl = li.querySelector('.todo-content');
    if (todo.content) {
      if (!contentEl) {
        contentEl = document.createElement('p');
        contentEl.className = 'todo-content';
        li.appendChild(contentEl);
      }
      if (contentEl.textContent !== todo.content) contentEl.textContent = todo.content;
    } else if (contentEl) {
      contentEl.remove();
    }
  }

  function reconcileTodos(todos) {
    var section = document.querySelector('.todo-widget');
    if (!section) return;

    var metaEl = section.querySelector('.widget-meta');
    var list = section.querySelector('ol.todo-list');

    if (!todos.length) {
      if (list) list.remove();
      if (metaEl) {
        metaEl.innerHTML = '0 items, <a href="/' + username + '/todo/index">add an item?</a>';
      }
      return;
    }

    if (!list) {
      list = document.createElement('ol');
      list.className = 'todo-list';
      list.dataset.username = username;
      section.appendChild(list);
    }

    var existing = {};
    list.querySelectorAll('.todo-item').forEach(function (li) {
      existing[li.dataset.todoId] = li;
    });

    var frag = document.createDocumentFragment();
    todos.forEach(function (todo) {
      var id = todo.todoID;
      var li = existing[id];

      if (li && pendingTodoIds.has(id)) {
        // In-flight local toggle — keep the DOM as-is until it settles.
        frag.appendChild(li);
      } else if (li) {
        updateTodoItemInPlace(li, todo);
        frag.appendChild(li);
      } else {
        frag.appendChild(buildTodoItem(todo));
      }
      delete existing[id];
    });

    list.innerHTML = '';
    list.appendChild(frag);

    if (metaEl) {
      var done = todos.filter(function (t) { return t.completed; }).length;
      metaEl.innerHTML = '<span id="todo-widget-count">' + done + '/' + todos.length + '</span> today';
    }
  }

  document.querySelectorAll('.todo-toggle-btn').forEach(function (btn) { btn.hidden = true; });
  document.querySelectorAll('.todo-checkbox').forEach(bindTodoCheckbox);

  /* -------------------------------------------------------------------------
     Study widget
     ------------------------------------------------------------------------- */

  function studyToggleUrl(sourceId) {
    return '/' + username + '/study/source/complete/post/' + sourceId;
  }

  function updateStudyMeta() {
    var boxes = document.querySelectorAll('.complete-checkbox');
    var el = document.getElementById('study-widget-count');
    if (!el) return;
    var completed = 0;
    boxes.forEach(function (cb) { if (cb.checked) completed++; });
    el.textContent = completed + '/' + boxes.length;
  }

  function bindStudyCheckbox(checkbox) {
    var form = checkbox.closest('form');
    var submitBtn = form.querySelector('.complete-submit');
    if (submitBtn) submitBtn.hidden = true;

    checkbox.addEventListener('change', function () {
      var li = checkbox.closest('.source-item');
      var sourceId = li ? li.dataset.sourceId : null;

      if (sourceId) pendingStudyIds.add(sourceId);
      updateStudyMeta();

      var data = new URLSearchParams(new FormData(form));
      fetch(form.action, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest', 'Content-Type': 'application/x-www-form-urlencoded' },
        body: data.toString()
      })
        .then(function (r) { return r.json(); })
        .then(function (resp) {
          if (resp.status !== 'ok') { checkbox.checked = !checkbox.checked; updateStudyMeta(); return; }
          if (li) li.classList.toggle('source-item--done', resp.done);
        })
        .catch(function () {
          checkbox.checked = !checkbox.checked;
          updateStudyMeta();
        })
        .finally(function () { if (sourceId) pendingStudyIds.delete(sourceId); });
    });
  }

  function buildStudyItem(item) {
    var li = document.createElement('li');
    li.className = 'source-item' + (item.completed ? ' source-item--done' : '');
    li.dataset.sourceId = item.sourceID;

    var top = document.createElement('div');
    top.className = 'source-top';

    var form = document.createElement('form');
    form.className = 'complete-form';
    form.method = 'post';
    form.action = studyToggleUrl(item.sourceID);

    var dateInput = document.createElement('input');
    dateInput.type = 'hidden';
    dateInput.name = 'date';
    dateInput.value = todayStr;

    var checkboxId = 'c' + item.sourceID;
    var checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.id = checkboxId;
    checkbox.className = 'complete-checkbox';
    checkbox.name = 'complete';
    checkbox.checked = !!item.completed;
    checkbox.setAttribute('aria-label', (item.completed ? 'Mark incomplete' : 'Mark complete') + ': ' + item.title);

    var label = document.createElement('label');
    label.setAttribute('for', checkboxId);
    label.className = 'source-title';
    if (item.url) {
      var a = document.createElement('a');
      a.href = item.url;
      a.target = '_blank';
      a.rel = 'noopener';
      a.textContent = item.title;
      label.appendChild(a);
    } else {
      label.textContent = item.title;
    }

    var submitBtn = document.createElement('button');
    submitBtn.type = 'submit';
    submitBtn.className = 'complete-submit';
    submitBtn.innerHTML = '&#10003;';
    submitBtn.hidden = true;

    form.appendChild(dateInput);
    form.appendChild(checkbox);
    form.appendChild(label);
    form.appendChild(submitBtn);
    top.appendChild(form);
    li.appendChild(top);

    bindStudyCheckbox(checkbox);
    return li;
  }

  function updateStudyItemInPlace(li, item) {
    li.classList.toggle('source-item--done', item.completed);

    var cb = li.querySelector('.complete-checkbox');
    if (cb) cb.checked = item.completed;

    var titleEl = li.querySelector('.source-title');
    if (!titleEl) return;
    var linkEl = titleEl.querySelector('a');
    if (linkEl) {
      if (linkEl.textContent !== item.title) linkEl.textContent = item.title;
      if (item.url && linkEl.href !== item.url) linkEl.href = item.url;
    } else if (titleEl.textContent.trim() !== item.title) {
      titleEl.textContent = item.title;
    }
  }

  function reconcileStudy(studyData) {
    var section = document.querySelector('.study-widget');
    if (!section) return;

    var items = studyData.sources || [];
    var metaEl = section.querySelector('.widget-meta');
    var list = section.querySelector('ul.source-list');
    var emptyMsg = section.querySelector('.widget-empty');

    if (!items.length) {
      if (list) list.remove();
      if (!emptyMsg) {
        emptyMsg = document.createElement('p');
        emptyMsg.className = 'widget-empty';
        emptyMsg.textContent = 'Nothing scheduled for today.';
        section.appendChild(emptyMsg);
      }
    } else {
      if (emptyMsg) emptyMsg.remove();

      if (!list) {
        list = document.createElement('ul');
        list.className = 'study-item-list source-list';
        section.appendChild(list);
      }

      var existing = {};
      list.querySelectorAll('.source-item').forEach(function (li) {
        existing[li.dataset.sourceId] = li;
      });

      var frag = document.createDocumentFragment();
      items.forEach(function (item) {
        var id = item.sourceID;
        var li = existing[id];

        if (li && pendingStudyIds.has(id)) {
          frag.appendChild(li);
        } else if (li) {
          updateStudyItemInPlace(li, item);
          frag.appendChild(li);
        } else {
          frag.appendChild(buildStudyItem(item));
        }
        delete existing[id];
      });

      list.innerHTML = '';
      list.appendChild(frag);
    }

    if (metaEl) {
      var streakText = studyData.streak > 0 ? ' · ' + studyData.streak + '-day streak' : '';
      metaEl.innerHTML = '<span id="study-widget-count">' + studyData.completed + '/' + studyData.total + '</span> today' + streakText;
    }
  }

  document.querySelectorAll('.study-widget .complete-checkbox').forEach(bindStudyCheckbox);

  /* -------------------------------------------------------------------------
     Periodic poll: reconcile every widget's full item list against the server.
     ------------------------------------------------------------------------- */

  function pollDashboard() {
    if (!username) return;

    fetch('/' + username + '/dashboard/index/json', {
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      credentials: 'same-origin'
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var habitEl = document.getElementById('habit-widget-meta');
        if (habitEl && data.habit_total !== undefined) {
          habitEl.textContent = data.habit_completed + '/' + data.habit_total + ' today';
        }
        if (data.todos) reconcileTodos(data.todos);
        if (data.study) reconcileStudy(data.study);
      })
      .catch(function () {});
  }

  setInterval(pollDashboard, POLL_INTERVAL_MS);
})();
