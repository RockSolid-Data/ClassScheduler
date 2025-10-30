'''
Base Data Access Object (DAO) for all DAOs in the FertilizerCommandCenter

This module provides a base class with common functionality for database operations.
It ensures proper handling of database connections by using Peewee's model-database binding.
'''
from contextlib import contextmanager
from librepy.peewee.peewee import DoesNotExist, IntegrityError


class BaseDAO:
    """Common DAO utilities for Peewee models.

    Provides connection management, safe execution, common read helpers
    (get_by_id, first, count, exists, paginate) and simple mutations.
    """

    def __init__(self, model_class, logger):
        """Initialize the DAO.

        Args:
            model_class: Peewee model class this DAO operates on.
            logger: Logger for info/error messages.
        """
        self.model_class = model_class
        self.logger = logger

    @property
    def database(self):
        """Return the Peewee Database bound to the model."""
        return self.model_class._meta.database

    # ---------- Connection / transaction ----------

    def _ensure_connection(self, operation_func):
        """Ensure the callable runs with an active DB connection.

        If the database is closed, open a short-lived connection context,
        otherwise reuse the current connection.
        """
        db = self.database
        if getattr(db, "is_closed", lambda: True)():
            with db.connection_context():
                return operation_func()
        return operation_func()

    @contextmanager
    def atomic(self):
        """Provide a transactional context manager.

        Uses db.atomic() when available; otherwise yields a no-op context.
        """
        db = self.database
        if hasattr(db, "atomic"):
            with db.atomic():
                yield
        else:
            # Fallback: not all DBs expose atomic() in older wrappers
            yield

    # ---------- Execution wrappers ----------

    def execute_query(self, query_func, *args, **kwargs):
        """Execute a callable within a managed DB connection.

        Args:
            query_func: Zero-arg callable or callable expecting provided args/kwargs.
            *args: Positional args to pass to the callable.
            **kwargs: Keyword args to pass to the callable.

        Returns:
            The callable result.
        """
        return self._ensure_connection(lambda: query_func(*args, **kwargs))

    def safe_execute(self, operation_name, query_func, default_return=None, reraise_integrity=True):
        """Execute a callable and handle common DB errors consistently.

        Args:
            operation_name: Human-friendly label for logs.
            query_func: Zero-arg callable to execute.
            default_return: Value to return on handled errors.
            reraise_integrity: If True, re-raise IntegrityError after logging.

        Returns:
            The callable result or default_return on handled errors.
        """
        try:
            return self.execute_query(query_func)
        except DoesNotExist:
            self.logger.info(f"{operation_name}: not found")
            return default_return
        except IntegrityError as e:
            self.logger.error(f"{operation_name}: integrity error: {e}")
            if reraise_integrity:
                raise
            return default_return
        except Exception as e:
            self.logger.error(f"{operation_name}: error: {e}")
            return default_return

    # ---------- Canonical reads ----------

    def get_by_id(self, entity_id, fields=None, operation_name=None):
        """Fetch a single row by primary key.

        Args:
            entity_id: Primary key value.
            fields: Optional iterable of Peewee Field instances or field names (strings) to select.
                When None, selects all model fields.
            operation_name: Optional label for logging.

        Returns:
            Model instance or None if not found or on error.
        """
        Model = self.model_class
        op = operation_name or f"get_by_id({entity_id}) on {Model.__name__}"

        def _q():
            cols = None
            if fields:
                cols = [getattr(Model, f) if isinstance(f, str) else f for f in fields]
            pk_field = Model._meta.primary_key
            q = Model.select(*(cols or ())).where(pk_field == entity_id)
            return q.first()

        return self.safe_execute(op, _q, default_return=None)

    def get_or_none(self, *where, fields=None, operation_name=None):
        """Get the first row matching where-clause or None.

        Args:
            *where: Peewee expressions to filter by.
            fields: Optional iterable of Peewee Field instances or field names (strings) to select.
                When None, selects all model fields.
            operation_name: Optional label for logging.
        """
        Model = self.model_class
        op = operation_name or f"get_or_none on {Model.__name__}"

        def _q():
            cols = None
            if fields:
                cols = [getattr(Model, f) if isinstance(f, str) else f for f in fields]
            q = Model.select(*(cols or ()))
            if where:
                q = q.where(*where)
            return q.first()

        return self.safe_execute(op, _q, default_return=None)

    def first(self, where_clause=None, order_by=None, operation_name=None):
        """Return the first row matching the filters or None.

        Args:
            where_clause: Optional Peewee expression.
            order_by: Optional order clause(s).
            operation_name: Optional label for logging.
        """
        def _q():
            q = self.model_class.select()
            if where_clause is not None:
                q = q.where(where_clause)
            if order_by is not None:
                q = q.order_by(order_by)
            return q.first()
        op = operation_name or f"first on {self.model_class.__name__}"
        return self.safe_execute(op, _q, default_return=None)

    def get_all(self, order_by=None, where_clause=None, fields=None, operation_name=None):
        """Return all rows, optionally filtered and ordered.

        Args:
            order_by: Optional order clause(s).
            where_clause: Optional Peewee expression.
            fields: Optional iterable of Peewee Field instances or field names (strings) to select.
                When None, selects all model fields.
            operation_name: Optional label for logging.

        Returns:
            List of model instances (possibly empty).
        """
        Model = self.model_class
        op = operation_name or f"fetching all {Model.__name__}"
        def _q():
            cols = None
            if fields:
                cols = [getattr(Model, f) if isinstance(f, str) else f for f in fields]
            q = Model.select(*(cols or ()))
            if where_clause is not None:
                q = q.where(where_clause)
            if order_by is not None:
                q = q.order_by(order_by)
            return list(q)
        return self.safe_execute(op, _q, default_return=[])

    def get_all_dicts(self, fields=None, where_clause=None, order_by=None, operation_name=None):
        """Return rows as list of dictionaries.

        Args:
            fields: Optional iterable of Peewee Field instances or field names (strings).
                When None, selects all model fields.
            where_clause: Optional Peewee expression to filter rows.
            order_by: Optional order clause(s).
            operation_name: Optional label for logging.

        Returns:
            List[dict]: Each row as a dictionary keyed by model field names.
        """
        Model = self.model_class
        op = operation_name or f"fetching all {Model.__name__} (dicts)"

        def _q():
            # Resolve provided field names to Peewee field objects using a list comprehension (as specified)
            cols = None
            if fields:
                cols = [getattr(Model, f) if isinstance(f, str) else f for f in fields]
            q = Model.select(*(cols or ()))
            if where_clause is not None:
                q = q.where(where_clause)
            if order_by is not None:
                q = q.order_by(order_by)
            return list(q.dicts())

        return self.safe_execute(op, _q, default_return=[])

    def to_dict(self, instance, fields=None):
        """Convert a model instance managed by this DAO to a dict.

        Args:
            instance: Peewee model instance (or None).
            fields: Optional iterable of Peewee Field instances or field names (strings)
                to include in the dict. When None, includes all model fields.

        Returns:
            dict | None: A dictionary mapping field names to values; None when instance is None.
        """
        if instance is None:
            return None
        Model = self.model_class
        # Determine which fields to include
        if fields:
            cols = [getattr(Model, f) if isinstance(f, str) else f for f in fields]
        else:
            cols = list(Model._meta.sorted_fields)
        # Build dict using field names and attribute values from instance
        return {fld.name: getattr(instance, fld.name) for fld in cols}

    def count(self, where_clause=None, operation_name=None):
        """Count rows, optionally filtered.

        Args:
            where_clause: Optional Peewee expression.
            operation_name: Optional label for logging.

        Returns:
            Integer count (0 on error).
        """
        op = operation_name or f"count {self.model_class.__name__}"
        def _q():
            q = self.model_class.select()
            if where_clause is not None:
                q = q.where(where_clause)
            return q.count()
        return self.safe_execute(op, _q, default_return=0)

    def exists(self, where_clause=None, operation_name=None):
        """Check whether any row exists for the given filter.

        Args:
            where_clause: Optional Peewee expression.
            operation_name: Optional label for logging.

        Returns:
            True if at least one row exists; False otherwise.
        """
        op = operation_name or f"exists {self.model_class.__name__}"
        def _q():
            q = self.model_class.select(self.model_class._meta.primary_key).limit(1)
            if where_clause is not None:
                q = q.where(where_clause)
            return q.exists()
        return bool(self.safe_execute(op, _q, default_return=False))

    def paginate(self, page=1, per_page=50, where_clause=None, order_by=None, operation_name=None):
        """Paginate rows and return the current page and total count.

        Args:
            page: 1-based page number.
            per_page: Page size (> 0).
            where_clause: Optional Peewee expression.
            order_by: Optional order clause(s).
            operation_name: Optional label for logging.

        Returns:
            Tuple (rows, total) where rows is a list for the page and total is
            the total number of matching rows.
        """
        page = max(int(page or 1), 1)
        per_page = max(int(per_page or 1), 1)
        offset = (page - 1) * per_page

        rows = self.get_all(order_by=order_by, where_clause=where_clause)
        total = len(rows) if where_clause is not None and order_by is None else self.count(where_clause)
        # DB-level pagination:
        def _q():
            q = self.model_class.select()
            if where_clause is not None:
                q = q.where(where_clause)
            if order_by is not None:
                q = q.order_by(order_by)
            return list(q.limit(per_page).offset(offset))
        page_rows = self.safe_execute(
            operation_name or f"paginate {self.model_class.__name__}",
            _q,
            default_return=[]
        )
        return page_rows, total

    # ---------- Mutations ----------

    def create(self, operation_name=None, **data):
        """Create a new row with the given data.

        Args:
            operation_name: Optional label for logging.
            **data: Field values for the new row.

        Returns:
            Created model instance or None on error.
        """
        op = operation_name or f"create {self.model_class.__name__}"
        return self.safe_execute(op, lambda: self.model_class.create(**data), default_return=None)

    def update_fields(self, where_clause, updates: dict, operation_name=None):
        """Update fields for rows matching the filter.

        Args:
            where_clause: Peewee expression selecting rows to update.
            updates: Dict of field updates.
            operation_name: Optional label for logging.

        Returns:
            Number of rows updated (0 on error).
        """
        op = operation_name or f"update {self.model_class.__name__}"
        def _q():
            return self.model_class.update(**updates).where(where_clause).execute()
        return int(self.safe_execute(op, _q, default_return=0))

    def delete_where(self, where_clause, operation_name=None):
        """Delete rows matching the filter.

        Args:
            where_clause: Peewee expression selecting rows to delete.
            operation_name: Optional label for logging.

        Returns:
            Number of rows deleted (0 on error).
        """
        op = operation_name or f"delete {self.model_class.__name__}"
        def _q():
            return self.model_class.delete().where(where_clause).execute()
        return int(self.safe_execute(op, _q, default_return=0))

    # ---------- Validation ----------

    def validate_string_field(self, value, field_name, max_length=None, required=True):
        """Validate and normalize a string field.

        Strips whitespace, enforces required flag and max_length.

        Args:
            value: Input value.
            field_name: Name used in error messages.
            max_length: Optional maximum allowed length.
            required: If True, empty values raise ValueError.

        Returns:
            Normalized string or None when not required and empty.

        Raises:
            ValueError: When constraints are violated.
        """
        if value is None or value == "":
            if required:
                raise ValueError(f"{field_name} is required")
            return None
        normalized = str(value).strip()
        if required and not normalized:
            raise ValueError(f"{field_name} cannot be empty")
        if max_length and len(normalized) > max_length:
            raise ValueError(f"{field_name} cannot exceed {max_length} characters")
        return normalized

    def validate_numeric_field(self, value, field_name, min_value=None, max_value=None, required=True):
        """Validate and normalize a numeric field to float.

        Args:
            value: Input value to parse as number.
            field_name: Name used in error messages.
            min_value: Optional minimum inclusive value.
            max_value: Optional maximum inclusive value.
            required: If True, empty values raise ValueError.

        Returns:
            Parsed float or None when not required and empty.

        Raises:
            ValueError: When parsing fails or constraints are violated.
        """
        if value is None or value == "":
            if required:
                raise ValueError(f"{field_name} is required")
            return None
        try:
            numeric_value = float(value)
        except (ValueError, TypeError):
            raise ValueError(f"{field_name} must be a valid number")
        if min_value is not None and numeric_value < min_value:
            raise ValueError(f"{field_name} must be at least {min_value}")
        if max_value is not None and numeric_value > max_value:
            raise ValueError(f"{field_name} cannot exceed {max_value}")
        return numeric_value

    # --- Generic backref fetcher ---
    def related(self, instance, backref_name, where_clause=None, order_by=None, limit=None, offset=None, as_dict=False, fields=None):
        """Fetch related rows via a backref on the given instance.

        Args:
            instance: Parent model instance with a backref attribute.
            backref_name: Name of the backref attribute.
            where_clause: Optional Peewee expression.
            order_by: Optional order clause(s).
            limit: Optional max number of rows to return.
            offset: Optional number of rows to skip.
            as_dict: When True, returns list of dictionaries via Peewee's dicts().
            fields: Optional iterable of field objects or field-name strings to select when
                returning dicts (ignored when as_dict=False).

        Returns:
            List of related model instances (default) or List[dict] when as_dict=True.
        """
        def _q():
            q = getattr(instance, backref_name)  # this is a ModelSelect from the backref
            # Optionally narrow selected columns when producing dicts
            if as_dict and fields:
                RelatedModel = q.model
                cols = [getattr(RelatedModel, f) if isinstance(f, str) else f for f in fields]
                q = q.select(*cols)
            if where_clause is not None:
                q = q.where(where_clause)
            if order_by is not None:
                q = q.order_by(order_by)
            if offset is not None:
                q = q.offset(offset)
            if limit is not None:
                q = q.limit(limit)
            return list(q.dicts()) if as_dict else list(q)

        return self.execute_query(_q)

    # --- Sugar: dao.<backref>(instance, **kwargs) ---
    def __getattr__(self, backref_name):
        """Create a convenience accessor for a backref on demand.

        Returns a function that calls related(instance, backref_name, ...).
        """
        def accessor(instance, where_clause=None, order_by=None, limit=None, offset=None, as_dict=False, fields=None):
            """Fetch related rows for the given instance using the backref name."""
            return self.related(
                instance,
                backref_name,
                where_clause=where_clause,
                order_by=order_by,
                limit=limit,
                offset=offset,
                as_dict=as_dict,
                fields=fields,
            )

        return accessor


    def parent(self, instance, fk_name, dict=False, fields=None, operation_name=None):
        """Return the parent via a forward foreign key on the given instance.

        The lookup always runs through DAO connection handling (safe_execute/execute_query)
        to ensure a proper database connection.

        Examples:
            invoice_dao.parent(invoice, 'customer')
            invoice_dao.parent(invoice, 'customer', dict=True, fields=['customer_id', 'name'])

        Args:
            instance: Child model instance that has a forward FK attribute.
            fk_name: Name of the forward foreign key attribute on the instance.
            dict: When True, return a dictionary of field values; otherwise return the parent instance.
            fields: Optional iterable of Peewee Field objects or field-name strings to include when dict=True.
                When omitted, includes all fields found in ParentModel._meta.sorted_fields.
            operation_name: Optional label for logging.

        Returns:
            The parent model instance, a dictionary of its field values when dict=True, or None when not found.
        """
        ChildModel = self.model_class
        op = operation_name or f"parent({fk_name}) on {ChildModel.__name__}"

        def _q():
            parent_obj = getattr(instance, fk_name)
            if parent_obj is None:
                return None
            if not dict:
                return parent_obj
            # Build dict from the parent model instance
            ParentModel = parent_obj.__class__
            if fields:
                cols = [getattr(ParentModel, f) if isinstance(f, str) else f for f in fields]
            else:
                cols = list(ParentModel._meta.sorted_fields)
            return {fld.name: getattr(parent_obj, fld.name) for fld in cols}

        return self.safe_execute(op, _q, default_return=None)
