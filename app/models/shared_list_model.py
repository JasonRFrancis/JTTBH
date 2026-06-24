"""
Shared List Model
=================
Persistence layer for collaborative shared lists.

Tables
------
shared_list        — list metadata (owner, name)
shared_list_member — membership, permissions, invite status
shared_list_item   — insert-only items (title=NULL means deleted)
"""

import uuid
from datetime import datetime

from app.services.database import db_manager


class SharedListModel:

    # ------------------------------------------------------------------
    # List management
    # ------------------------------------------------------------------

    @staticmethod
    def create_list(owner_id: str, name: str) -> str:
        """Create a new shared list. Returns the new listID."""
        list_id = str(uuid.uuid4())
        db_manager.execute_insert(
            "INSERT INTO shared_list (listID, ownerID, name) VALUES (%s, %s, %s)",
            (list_id, owner_id, name.strip()),
        )
        return list_id

    @staticmethod
    def get_list(list_id: str) -> dict | None:
        return db_manager.execute_one(
            """SELECT sl.listID, sl.ownerID, sl.name, sl.created,
                      u.username as owner_username
               FROM shared_list sl
               JOIN `user` u ON u.userID = sl.ownerID
               WHERE sl.listID = %s""",
            (list_id,),
        )

    @staticmethod
    def rename_list(list_id: str, name: str) -> None:
        db_manager.execute_update(
            "UPDATE shared_list SET name = %s WHERE listID = %s",
            (name.strip(), list_id),
        )

    @staticmethod
    def delete_list(list_id: str) -> None:
        """Delete list and all associated members and items."""
        db_manager.execute_update(
            "DELETE FROM shared_list_item WHERE listID = %s", (list_id,)
        )
        db_manager.execute_update(
            "DELETE FROM shared_list_member WHERE listID = %s", (list_id,)
        )
        db_manager.execute_update(
            "DELETE FROM shared_list WHERE listID = %s", (list_id,)
        )

    @staticmethod
    def get_lists_for_todo_index(user_id: str) -> list[dict]:
        """
        Return all lists that should appear in the user's todo bottom section:
        - Lists owned by the user (always shown)
        - Lists where user is an accepted member with show_in_todo = 1
        """
        return db_manager.execute_query(
            """SELECT sl.listID, sl.ownerID, sl.name, sl.created,
                      u.username as owner_username,
                      CASE WHEN sl.ownerID = %s THEN 'edit' ELSE slm.permission END as permission,
                      CASE WHEN sl.ownerID = %s THEN 1 ELSE 0 END as is_owner
               FROM shared_list sl
               JOIN `user` u ON u.userID = sl.ownerID
               LEFT JOIN shared_list_member slm
                     ON slm.listID = sl.listID AND slm.userID = %s
               WHERE sl.ownerID = %s
                  OR (slm.userID = %s AND slm.status = 'accepted' AND slm.show_in_todo = 1)
               ORDER BY sl.name""",
            (user_id, user_id, user_id, user_id, user_id),
        )

    @staticmethod
    def get_all_lists_for_user(user_id: str) -> list[dict]:
        """
        All lists the user owns or is an accepted member of (for settings page).
        """
        return db_manager.execute_query(
            """SELECT sl.listID, sl.ownerID, sl.name, sl.created,
                      u.username as owner_username,
                      CASE WHEN sl.ownerID = %s THEN 'edit' ELSE slm.permission END as permission,
                      CASE WHEN sl.ownerID = %s THEN 1 ELSE 0 END as is_owner,
                      COALESCE(slm.show_in_todo, 0) as show_in_todo
               FROM shared_list sl
               JOIN `user` u ON u.userID = sl.ownerID
               LEFT JOIN shared_list_member slm
                     ON slm.listID = sl.listID AND slm.userID = %s
               WHERE sl.ownerID = %s
                  OR (slm.userID = %s AND slm.status = 'accepted')
               ORDER BY sl.name""",
            (user_id, user_id, user_id, user_id, user_id),
        )

    @staticmethod
    def get_list_with_items(list_id: str) -> dict | None:
        """
        Return list metadata plus all active items grouped by contributor.

        Returns a dict with keys: listID, ownerID, owner_username, name, created,
        contributors (list of {userID, username, items}).
        """
        meta = SharedListModel.get_list(list_id)
        if not meta:
            return None

        rows = db_manager.execute_query(
            """SELECT si.itemID, si.listID, si.userID, si.title,
                      si.position, si.completed, si.completed_by, si.created,
                      u.username as contributor_username
               FROM shared_list_item si
               JOIN `user` u ON u.userID = si.userID
               WHERE si.listID = %s
                 AND si.id = (
                     SELECT MAX(si2.id)
                     FROM shared_list_item si2
                     WHERE si2.itemID = si.itemID
                 )
                 AND si.title IS NOT NULL
               ORDER BY u.username, si.position, si.created""",
            (list_id,),
        )

        # Group by contributor
        contributors_map: dict[str, dict] = {}
        for row in rows:
            uid = row['userID']
            if uid not in contributors_map:
                contributors_map[uid] = {
                    'userID':   uid,
                    'username': row['contributor_username'],
                    'items':    [],
                }
            contributors_map[uid]['items'].append(row)

        result = dict(meta)
        result['contributors'] = list(contributors_map.values())
        return result

    # ------------------------------------------------------------------
    # Membership
    # ------------------------------------------------------------------

    @staticmethod
    def get_members(list_id: str) -> list[dict]:
        """All members (not the owner) with their status and permission."""
        return db_manager.execute_query(
            """SELECT slm.id, slm.listID, slm.userID, slm.permission,
                      slm.status, slm.show_in_todo, slm.created,
                      u.username, u.name as display_name,
                      u2.username as invited_by_username
               FROM shared_list_member slm
               JOIN `user` u  ON u.userID  = slm.userID
               JOIN `user` u2 ON u2.userID = slm.invited_by
               WHERE slm.listID = %s
               ORDER BY slm.created""",
            (list_id,),
        )

    @staticmethod
    def get_pending_invites(user_id: str) -> list[dict]:
        """Pending invitations for the given user."""
        return db_manager.execute_query(
            """SELECT slm.id, slm.listID, slm.permission, slm.created,
                      sl.name as list_name,
                      u_owner.username as owner_username,
                      u_inv.username   as invited_by_username
               FROM shared_list_member slm
               JOIN shared_list sl   ON sl.listID   = slm.listID
               JOIN `user` u_owner   ON u_owner.userID = sl.ownerID
               JOIN `user` u_inv     ON u_inv.userID   = slm.invited_by
               WHERE slm.userID = %s AND slm.status = 'pending'
               ORDER BY slm.created DESC""",
            (user_id,),
        )

    @staticmethod
    def is_owner(list_id: str, user_id: str) -> bool:
        row = db_manager.execute_one(
            "SELECT 1 FROM shared_list WHERE listID = %s AND ownerID = %s",
            (list_id, user_id),
        )
        return row is not None

    @staticmethod
    def is_member(list_id: str, user_id: str) -> bool:
        """True if user is the owner or an accepted member."""
        row = db_manager.execute_one(
            """SELECT 1 FROM shared_list sl
               LEFT JOIN shared_list_member slm
                     ON slm.listID = sl.listID AND slm.userID = %s
               WHERE sl.listID = %s
                 AND (sl.ownerID = %s
                      OR (slm.userID = %s AND slm.status = 'accepted'))""",
            (user_id, list_id, user_id, user_id),
        )
        return row is not None

    @staticmethod
    def get_member_permission(list_id: str, user_id: str) -> str | None:
        """Return 'edit' or 'view', or None if not a member."""
        if SharedListModel.is_owner(list_id, user_id):
            return 'edit'
        row = db_manager.execute_one(
            """SELECT permission FROM shared_list_member
               WHERE listID = %s AND userID = %s AND status = 'accepted'""",
            (list_id, user_id),
        )
        return row['permission'] if row else None

    @staticmethod
    def invite_member(list_id: str, user_id: str, permission: str, invited_by: str) -> bool:
        """
        Create a pending invitation. Returns False if the user is already
        invited or is a member, True on success.
        """
        existing = db_manager.execute_one(
            "SELECT id FROM shared_list_member WHERE listID = %s AND userID = %s",
            (list_id, user_id),
        )
        if existing:
            return False
        db_manager.execute_insert(
            """INSERT INTO shared_list_member
               (listID, userID, permission, invited_by, status)
               VALUES (%s, %s, %s, %s, 'pending')""",
            (list_id, user_id, permission, invited_by),
        )
        return True

    @staticmethod
    def accept_invite(list_id: str, user_id: str, show_in_todo: bool) -> None:
        db_manager.execute_update(
            """UPDATE shared_list_member
               SET status = 'accepted', show_in_todo = %s
               WHERE listID = %s AND userID = %s AND status = 'pending'""",
            (1 if show_in_todo else 0, list_id, user_id),
        )

    @staticmethod
    def decline_invite(list_id: str, user_id: str) -> None:
        db_manager.execute_update(
            """UPDATE shared_list_member
               SET status = 'declined'
               WHERE listID = %s AND userID = %s AND status = 'pending'""",
            (list_id, user_id),
        )

    @staticmethod
    def update_member_permission(list_id: str, user_id: str, permission: str) -> None:
        db_manager.execute_update(
            """UPDATE shared_list_member
               SET permission = %s
               WHERE listID = %s AND userID = %s""",
            (permission, list_id, user_id),
        )

    @staticmethod
    def remove_member(list_id: str, user_id: str) -> None:
        db_manager.execute_update(
            "DELETE FROM shared_list_member WHERE listID = %s AND userID = %s",
            (list_id, user_id),
        )

    @staticmethod
    def toggle_show_in_todo(list_id: str, user_id: str) -> None:
        db_manager.execute_update(
            """UPDATE shared_list_member
               SET show_in_todo = 1 - show_in_todo
               WHERE listID = %s AND userID = %s AND status = 'accepted'""",
            (list_id, user_id),
        )

    @staticmethod
    def leave_list(list_id: str, user_id: str) -> None:
        db_manager.execute_update(
            "DELETE FROM shared_list_member WHERE listID = %s AND userID = %s",
            (list_id, user_id),
        )

    # ------------------------------------------------------------------
    # Items (insert-only; title=NULL means deleted)
    # ------------------------------------------------------------------

    @staticmethod
    def create_item(list_id: str, user_id: str, title: str) -> str:
        """Insert a new item. Returns the new itemID."""
        item_id = str(uuid.uuid4())
        # Position = max existing position for this user in this list + 1
        pos_row = db_manager.execute_one(
            """SELECT COALESCE(MAX(si.position), -1) + 1 as next_pos
               FROM shared_list_item si
               WHERE si.listID = %s AND si.userID = %s
                 AND si.id = (
                     SELECT MAX(si2.id) FROM shared_list_item si2
                     WHERE si2.itemID = si.itemID
                 )
                 AND si.title IS NOT NULL""",
            (list_id, user_id),
        )
        position = pos_row['next_pos'] if pos_row else 0
        db_manager.execute_insert(
            """INSERT INTO shared_list_item
               (itemID, listID, userID, title, position, created_by)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (item_id, list_id, user_id, title.strip(), position, user_id),
        )
        return item_id

    @staticmethod
    def get_item(item_id: str) -> dict | None:
        """Return the current state of an item (latest non-deleted row)."""
        return db_manager.execute_one(
            """SELECT si.itemID, si.listID, si.userID, si.title,
                      si.position, si.completed, si.completed_by
               FROM shared_list_item si
               WHERE si.itemID = %s
                 AND si.id = (
                     SELECT MAX(si2.id) FROM shared_list_item si2
                     WHERE si2.itemID = si.itemID
                 )
                 AND si.title IS NOT NULL""",
            (item_id,),
        )

    @staticmethod
    def toggle_item(item_id: str, user_id: str) -> None:
        """Toggle completion. Inserts a new row preserving all other fields."""
        current = SharedListModel.get_item(item_id)
        if not current:
            return
        new_completed = None if current['completed'] else datetime.now()
        new_completed_by = None if current['completed'] else user_id
        db_manager.execute_insert(
            """INSERT INTO shared_list_item
               (itemID, listID, userID, title, position, completed, completed_by, created_by)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                item_id,
                current['listID'],
                current['userID'],
                current['title'],
                current['position'],
                new_completed,
                new_completed_by,
                user_id,
            ),
        )

    @staticmethod
    def update_item(item_id: str, title: str, user_id: str) -> None:
        """Update item title via insert-only."""
        current = SharedListModel.get_item(item_id)
        if not current:
            return
        db_manager.execute_insert(
            """INSERT INTO shared_list_item
               (itemID, listID, userID, title, position, completed, completed_by, created_by)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                item_id,
                current['listID'],
                current['userID'],
                title.strip(),
                current['position'],
                current['completed'],
                current['completed_by'],
                user_id,
            ),
        )

    @staticmethod
    def delete_item(item_id: str, user_id: str) -> None:
        """Soft-delete by inserting a row with title=NULL."""
        current = SharedListModel.get_item(item_id)
        if not current:
            return
        db_manager.execute_insert(
            """INSERT INTO shared_list_item
               (itemID, listID, userID, title, position, completed, completed_by, created_by)
               VALUES (%s, %s, %s, NULL, %s, %s, %s, %s)""",
            (
                item_id,
                current['listID'],
                current['userID'],
                current['position'],
                current['completed'],
                current['completed_by'],
                user_id,
            ),
        )
