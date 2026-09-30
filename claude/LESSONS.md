
## 2026-09-30 — Read the decorator before claiming a security gap
Claimed API endpoints lacked a username-ownership check because they called `_get_user_id(username)`;
`api_key_required` already enforces key owner == `<username>` (non-admin keys). The real gap was
missing *read-permission* checks on GETs (fixed with `_require_read`). Before reporting an auth
hole, read the decorators on the route and prove it with a request that should be refused.
