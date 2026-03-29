"""
JTTBH Base Model
================
Lightweight base class for all domain models.

Subclasses set a ``table_name`` class attribute and use the
``DatabaseManager`` singleton directly for all persistence.  There is no
metaclass magic, no relationship tracking, and no unit-of-work pattern –
just plain Python objects that happen to carry the data returned from SQL
queries.

Usage
-----
::

    class Widget(BaseModel):
        table_name = 'widget'

    w = Widget(widget_id=1, name='Sprocket', qty=12)
    print(w.to_dict())          # {'widget_id': 1, 'name': 'Sprocket', 'qty': 12}
    print(w.widget_id)          # 1
"""


class BaseModel:
    """
    Minimal base class for JTTBH domain models.

    Attributes
    ----------
    table_name : str | None
        The name of the corresponding database table.  Subclasses must
        override this.
    """

    table_name: str | None = None

    def __init__(self, **kwargs):
        """
        Initialise the model by setting each keyword argument as an attribute.

        Parameters
        ----------
        **kwargs
            Column name / value pairs, typically from a ``DictCursor`` result
            row.

        Example
        -------
        ::

            row = db_manager.execute_one('SELECT * FROM user WHERE userID = %s', (uid,))
            user = User(**row)
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self) -> dict:
        """
        Serialise the model instance to a plain dictionary.

        Only instance attributes are included (class-level attributes such as
        ``table_name`` are excluded).  This makes it easy to pass model data
        to Jinja2 templates or JSON responses.

        Returns
        -------
        dict
            A shallow copy of the instance's ``__dict__``.
        """
        return {
            key: value
            for key, value in self.__dict__.items()
            # Skip private/dunder attributes
            if not key.startswith('_')
        }

    def __repr__(self) -> str:
        attrs = ', '.join(f'{k}={v!r}' for k, v in self.to_dict().items())
        return f'{self.__class__.__name__}({attrs})'
