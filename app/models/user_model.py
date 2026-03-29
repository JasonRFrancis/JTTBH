"""
JTTBH User Model
================
Represents a row in the ``user`` table and provides all user-related
persistence operations.

Table: user
-----------
    userID          VARCHAR(36)  PK  (UUID)
    google_id       VARCHAR(255) UNIQUE
    email           VARCHAR(255) UNIQUE
    name            VARCHAR(255)
    username        VARCHAR(64)  UNIQUE
    approval_status ENUM('pending','approved','rejected')
    access_token    TEXT
    refresh_token   TEXT
    token_expires   DATETIME
    created_at      DATETIME
    updated_at      DATETIME

Table: user_permission
----------------------
    id              INT          PK  AUTO_INCREMENT
    user_id         VARCHAR(36)  FK -> user.userID
    perm_read       INT          (bitvector)
    perm_write      INT          (bitvector)
    set_by          VARCHAR(36)  FK -> user.userID
    created_at      DATETIME

The most recently inserted row for a given user_id is treated as the
current permission record.
"""

import uuid
from datetime import datetime

from app.models.base_model import BaseModel
from app.services.database import db_manager


class User(BaseModel):
    """
    Domain model for a JTTBH user account.

    All classmethods return ``User`` instances (or ``None`` / lists) and
    communicate with the database via the ``db_manager`` singleton.
    """

    table_name = 'user'

    # ------------------------------------------------------------------
    # Finders (classmethods)
    # ------------------------------------------------------------------

    @classmethod
    def find_by_id(cls, user_id: str) -> 'User | None':
        """
        Look up a user by their UUID primary key.

        Parameters
        ----------
        user_id : str
            UUID string matching the ``userID`` column.

        Returns
        -------
        User | None
        """
        row = db_manager.execute_one(
            'SELECT * FROM user WHERE userID = %s',
            (user_id,),
        )
        return cls(**row) if row else None

    @classmethod
    def find_by_email(cls, email: str) -> 'User | None':
        """
        Look up a user by their email address.

        Parameters
        ----------
        email : str
            Email address to search for.

        Returns
        -------
        User | None
        """
        row = db_manager.execute_one(
            'SELECT * FROM user WHERE email = %s',
            (email,),
        )
        return cls(**row) if row else None

    @classmethod
    def find_by_google_id(cls, google_id: str) -> 'User | None':
        """
        Look up a user by their Google OAuth subject ID.

        Parameters
        ----------
        google_id : str
            The ``sub`` field from the Google ID token.

        Returns
        -------
        User | None
        """
        row = db_manager.execute_one(
            'SELECT * FROM user WHERE google_id = %s',
            (google_id,),
        )
        return cls(**row) if row else None

    @classmethod
    def find_by_username(cls, username: str) -> 'User | None':
        """
        Look up a user by their username.

        Parameters
        ----------
        username : str
            Username to search for (case-sensitive).

        Returns
        -------
        User | None
        """
        row = db_manager.execute_one(
            'SELECT * FROM user WHERE username = %s',
            (username,),
        )
        return cls(**row) if row else None

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        google_id: str,
        email: str,
        name: str,
        username: str,
    ) -> 'User':
        """
        Insert a new user row with ``approval_status = 'pending'``.

        Parameters
        ----------
        google_id : str
            Google OAuth subject ID.
        email : str
            User's email address.
        name : str
            User's full display name from Google.
        username : str
            Chosen username (must be unique).

        Returns
        -------
        User
            The newly created user object.

        Raises
        ------
        pymysql.Error
            If the INSERT fails (e.g. duplicate email / username).
        """
        user_id = str(uuid.uuid4())
        now = datetime.utcnow()

        db_manager.execute_insert(
            '''
            INSERT INTO user
                (userID, google_id, email, name, username, approval_status,
                 created_at, updated_at)
            VALUES
                (%s, %s, %s, %s, %s, 'pending', %s, %s)
            ''',
            (user_id, google_id, email, name, username, now, now),
        )

        return cls(
            userID=user_id,
            google_id=google_id,
            email=email,
            name=name,
            username=username,
            approval_status='pending',
            created_at=now,
            updated_at=now,
        )

    # ------------------------------------------------------------------
    # Update (exception to insert-only rule)
    # ------------------------------------------------------------------

    def update(self, **fields) -> None:
        """
        Update arbitrary columns on this user row.

        This is an intentional exception to the project's insert-only
        convention because user account state (tokens, approval status,
        username, etc.) must be mutable in place.

        Parameters
        ----------
        **fields
            Column name / value pairs to update.  Only the provided columns
            are changed; others remain untouched.

        Raises
        ------
        ValueError
            If no fields are provided.
        pymysql.Error
            On any database error.

        Example
        -------
        ::

            user.update(name='New Name', access_token='ya29.xxxx')
        """
        if not fields:
            raise ValueError('update() requires at least one field.')

        fields['updated_at'] = datetime.utcnow()

        set_clause = ', '.join(f'{col} = %s' for col in fields)
        values     = list(fields.values()) + [self.userID]

        db_manager.execute_update(
            f'UPDATE user SET {set_clause} WHERE userID = %s',
            values,
        )

        # Reflect changes on the instance itself
        for col, val in fields.items():
            setattr(self, col, val)

    # ------------------------------------------------------------------
    # Permissions
    # ------------------------------------------------------------------

    def get_permissions(self) -> tuple[int, int]:
        """
        Return the current read and write permission bitvectors.

        Reads the most recently inserted row from ``user_permission`` for
        this user.

        Returns
        -------
        tuple[int, int]
            ``(perm_read, perm_write)`` – defaults to ``(0, 0)`` if no
            permission row exists.
        """
        row = db_manager.execute_one(
            '''
            SELECT perm_read, perm_write
            FROM   user_permission
            WHERE  user_id = %s
            ORDER  BY created_at DESC, id DESC
            LIMIT  1
            ''',
            (self.userID,),
        )
        if row:
            return (row['perm_read'], row['perm_write'])
        return (0, 0)

    def is_admin(self) -> bool:
        """
        Return True if the user's read permission includes the admin bit.

        Returns
        -------
        bool
        """
        from app.services.decorators import PERM_ADMIN  # noqa: PLC0415
        perm_read, _ = self.get_permissions()
        return bool(perm_read & PERM_ADMIN)

    def set_permissions(
        self,
        read: int,
        write: int,
        admin_user_id: str,
    ) -> None:
        """
        Insert a new ``user_permission`` row for this user.

        A new row is always inserted (never updated) so the full history of
        permission changes is preserved.

        Parameters
        ----------
        read : int
            The new read permission bitvector.
        write : int
            The new write permission bitvector.
        admin_user_id : str
            UUID of the administrator making the change.
        """
        db_manager.execute_insert(
            '''
            INSERT INTO user_permission
                (user_id, perm_read, perm_write, set_by, created_at)
            VALUES
                (%s, %s, %s, %s, NOW())
            ''',
            (self.userID, read, write, admin_user_id),
        )

    # ------------------------------------------------------------------
    # Approval workflow
    # ------------------------------------------------------------------

    def approve(self, admin_user_id: str) -> None:
        """
        Approve this user's registration.

        Sets ``approval_status = 'approved'`` and grants a default permission
        set that includes dashboard read access.

        Parameters
        ----------
        admin_user_id : str
            UUID of the administrator performing the approval.
        """
        from app.services.decorators import PERM_DASHBOARD  # noqa: PLC0415

        self.update(approval_status='approved')

        # Grant a minimal default permission set
        default_read  = PERM_DASHBOARD
        default_write = PERM_DASHBOARD
        self.set_permissions(default_read, default_write, admin_user_id)

    def reject(self, admin_user_id: str) -> None:
        """
        Reject this user's registration.

        Sets ``approval_status = 'rejected'`` and removes all permissions.

        Parameters
        ----------
        admin_user_id : str
            UUID of the administrator performing the rejection.
        """
        self.update(approval_status='rejected')
        self.set_permissions(0, 0, admin_user_id)

    # ------------------------------------------------------------------
    # Bulk queries (classmethods)
    # ------------------------------------------------------------------

    @classmethod
    def get_all_users(cls) -> list[dict]:
        """
        Return all users with their current permissions.

        Returns
        -------
        list[dict]
            One dict per user, including ``perm_read`` and ``perm_write``
            from the latest ``user_permission`` row (NULL when no permission
            row exists).
        """
        return db_manager.execute_query(
            '''
            SELECT
                u.userID,
                u.email,
                u.name,
                u.username,
                u.approval_status,
                u.created_at,
                up.perm_read,
                up.perm_write
            FROM user u
            LEFT JOIN user_permission up
                ON up.id = (
                    SELECT id
                    FROM   user_permission
                    WHERE  user_id = u.userID
                    ORDER  BY created_at DESC, id DESC
                    LIMIT  1
                )
            ORDER BY u.created_at DESC
            ''',
        )

    @classmethod
    def get_pending_users(cls) -> list[dict]:
        """
        Return all users whose ``approval_status`` is ``'pending'``.

        Returns
        -------
        list[dict]
            Subset of ``get_all_users()`` filtered to pending accounts,
            ordered oldest-first so admins can process them in order.
        """
        return db_manager.execute_query(
            '''
            SELECT
                userID,
                email,
                name,
                username,
                approval_status,
                created_at
            FROM user
            WHERE approval_status = 'pending'
            ORDER BY created_at ASC
            ''',
        )
