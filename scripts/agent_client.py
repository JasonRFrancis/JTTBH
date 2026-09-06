#!/usr/bin/env python3
"""
JTTBH agent client
==================
A tiny stdlib-only client for the remote AI agent that helps with Jason's
projects. It talks to the ``/api/v1`` REST API using a Bearer key minted by
``scripts/generate_api_key.py`` (restrict the key by editing its ``permissions``
JSON — e.g. ``{"read": 64, "write": 64}`` for projects-only access).

The Projects page on jttbh.com is the control surface: Jason writes guidance and
approves proposed subprojects there; the agent reads guidance and writes progress
back through this client.

Intended loop (run on a schedule on the other machine)
-----------------------------------------------------
    c = JTTBHClient(os.environ["JTTBH_URL"], os.environ["JTTBH_API_KEY"],
                    os.environ["JTTBH_USER"])
    for p in c.list_projects():
        if p["status"] == "done":
            continue
        msgs, cursor = c.poll_messages(p["projectID"], since=load_cursor(p))
        guidance = [m for m in msgs if m["kind"] == "guidance"]
        if guidance:
            # ... act on the new guidance ...
            c.report(p["projectID"], "Did X and Y; Z still open.")
        if need_to_ask:
            c.ask(p["projectID"], "Which of A or B should I prioritise?")
        if a_split_would_help:
            c.propose_subproject(p["projectID"], "Data cleanup",
                                 "Separate track for normalising the CSV export.")
        save_cursor(p, cursor)

Task checklist: the agent owns it. ``add_task`` / ``check_task`` publish the plan
Jason watches on the page (he reads it; he doesn't edit it).
"""

import json
import os
import urllib.error
import urllib.request


class JTTBHClient:
    def __init__(self, base_url: str, api_key: str, username: str):
        self.base = base_url.rstrip('/') + '/api/v1/' + username
        self.key = api_key

    # -- transport ------------------------------------------------------

    def _request(self, method: str, path: str, body: dict | None = None):
        url = self.base + path
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header('Authorization', f'Bearer {self.key}')
        if data is not None:
            req.add_header('Content-Type', 'application/json')
        try:
            with urllib.request.urlopen(req) as resp:
                payload = json.loads(resp.read() or b'{}')
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors='replace')
            raise RuntimeError(f'{method} {path} -> {e.code}: {detail}') from None
        if payload.get('error'):
            raise RuntimeError(f'{method} {path} -> {payload["error"]}')
        return payload.get('data')

    # -- projects -----------------------------------------------------------

    def list_projects(self) -> list[dict]:
        return self._request('GET', '/projects')['projects']

    def get_project(self, project_id: str) -> dict:
        """Full detail: description, next_step, status, resources, tasks, messages."""
        return self._request('GET', f'/projects/{project_id}')

    def set_status(self, project_id: str, status: str) -> None:
        """status in: active, blocked, awaiting_review, done."""
        self._request('POST', f'/projects/{project_id}/status', {'status': status})

    def set_next_step(self, project_id: str, text: str) -> None:
        self._request('POST', f'/projects/{project_id}/status', {'next_step': text})

    # -- thread -----------------------------------------------------------

    def poll_messages(self, project_id: str, since: int = 0) -> tuple[list[dict], int]:
        """Return (messages after `since`, new cursor). Store the cursor per
        project between runs so you only see new guidance."""
        data = self._request('GET', f'/projects/{project_id}/messages?since={since}')
        return data['messages'], data['cursor']

    def ask(self, project_id: str, question: str) -> str:
        """Post a clarifying question. This flips the project to `blocked` so it
        surfaces at the top of Jason's Projects page."""
        return self._request('POST', f'/projects/{project_id}/messages',
                             {'kind': 'question', 'body': question})['message_id']

    def report(self, project_id: str, update: str) -> str:
        """Post a progress update (does not change status)."""
        return self._request('POST', f'/projects/{project_id}/messages',
                             {'kind': 'progress', 'body': update})['message_id']

    def propose_subproject(self, project_id: str, title: str,
                           description: str = '', rationale: str = '') -> str:
        """Suggest a subproject. Jason approves it on the page, which creates the
        child project."""
        return self._request('POST', f'/projects/{project_id}/messages', {
            'kind': 'proposal',
            'body': rationale,
            'meta': {'title': title, 'description': description},
        })['message_id']

    # -- plan checklist (agent writes) ----------------------------------

    def add_task(self, project_id: str, title: str, note: str = '') -> str:
        return self._request('POST', f'/projects/{project_id}/tasks',
                             {'title': title, 'note': note})['task_id']

    def check_task(self, project_id: str, task_id: str, done: bool = True) -> None:
        self._request('POST', f'/projects/{project_id}/tasks/{task_id}',
                      {'done': done})

    def edit_task(self, project_id: str, task_id: str, **fields) -> None:
        """fields: title, note, position, done."""
        self._request('POST', f'/projects/{project_id}/tasks/{task_id}', fields)

    def delete_task(self, project_id: str, task_id: str) -> None:
        self._request('DELETE', f'/projects/{project_id}/tasks/{task_id}')


def _demo() -> None:
    c = JTTBHClient(os.environ['JTTBH_URL'], os.environ['JTTBH_API_KEY'],
                    os.environ['JTTBH_USER'])
    projects = c.list_projects()
    print(f'{len(projects)} project(s):\n')
    for p in projects:
        flag = f'  [{p["open_questions"]} open Q]' if p['open_questions'] else ''
        print(f'- {p["name"]}  ({p["status"]}){flag}')
        detail = c.get_project(p['projectID'])
        for t in detail['tasks']:
            print(f'    [{"x" if t["done"] else " "}] {t["title"]}')
        for m in detail['messages']:
            who = 'you' if m['author'] == 'user' else 'agent'
            print(f'    {who}/{m["kind"]}: {(m["body"] or "")[:70]}')
    print()


if __name__ == '__main__':
    _demo()
