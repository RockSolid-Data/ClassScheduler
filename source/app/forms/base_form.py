# forms/base.py
from typing import Any, Dict, List, Optional, Callable, Type


class BaseForm:
    """
    Usage:
        class TemplateForm(BaseForm):
            class Meta(BaseForm.Meta):
                dao = TemplateDAO
                create_fn = "upsert_template"
                update_fn = "upsert_template"
                pk_field  = "template_id"

            def clean(self):
                # read inputs via self.get()/self.require()
                # validate, normalize, then fill self.cleaned_data
                ...
    """

    # ---- Class-level configuration (override in child via inner Meta) ----
    class Meta:
        dao: Optional[Type[Any]] = None
        dao_factory: Optional[Callable[[Any], Any]] = None
        create_fn: str = "create"
        update_fn: str = "update"
        pk_field: str = "id"

    # ---- Init & public API ----
    def __init__(
        self,
        data: Optional[Dict[str, Any]] = None,
        instance: Any = None,
        partial: bool = False,
        context: Any = None,
    ):
        self.data = data or {}
        self.instance = instance
        self.partial = partial
        self.context = context

        self.cleaned_data: Dict[str, Any] = {}
        self._errors: List[Dict[str, str]] = []
        self._is_bound = (data is not None) or (instance is not None)

        self._dao_cache: Any = None  # lazy DAO instance

    @property
    def errors(self) -> List[Dict[str, str]]:
        """Read-only list like [{'field': '...', 'message': '...'}]."""
        return list(self._errors)

    def is_valid(self) -> bool:
        """
        Clears previous results, runs clean(), and returns True if no errors.
        """
        self._errors.clear()
        self.cleaned_data.clear()

        if not self._is_bound:
            self.add_error(None, "Form is not bound (no data/instance).")
            return False

        self.clean()
        return not self._errors

    def save(self) -> Dict[str, Any]:
        """
        Uses Meta to pick DAO + method:
            if pk present -> Meta.update_fn
            else          -> Meta.create_fn
        Expects self.cleaned_data to be ready (run is_valid() first).
        """
        if self._errors:
            return {"ok": False, "errors": self.errors}

        dao = self._get_dao()
        method_name = self.Meta.update_fn if self._pk_value() else self.Meta.create_fn
        method = getattr(dao, method_name, None)
        if not callable(method):
            raise AttributeError(f"DAO missing method '{method_name}'")
        result = method(**self.cleaned_data)
        return {"ok": True, "result": result}

    # ---- Helpers for child forms ----
    def add_error(self, field: Optional[str], message: str) -> None:
        """Append a validation error; use field=None for non-field errors."""
        self._errors.append({"field": field or "__all__", "message": message})

    def get(self, field: str, default: Any = None) -> Any:
        """Fetch optional field from incoming data."""
        return self.data.get(field, default)

    def require(self, field: str) -> Any:
        """
        Require a field unless partial=True and it's absent (PATCH semantics).
        Returns the value (may be None if explicitly provided).
        """
        if self.partial and field not in self.data:
            return None
        val = self.data.get(field)
        if val is None or (isinstance(val, str) and val.strip() == ""):
            self.add_error(field, "This field is required.")
        return val

    def clean(self) -> None:
        """
        Override in child:
          - read via get()/require()
          - validate/normalize
          - fill self.cleaned_data for DAO
        """
        pass

    # ---- Internals (DAO + PK) ----
    def _get_dao(self) -> Any:
        """Instantiate DAO from Meta.dao or Meta.dao_factory (cached)."""
        if self._dao_cache is not None:
            return self._dao_cache
        if self.Meta.dao_factory:
            self._dao_cache = self.Meta.dao_factory(self.context)
        elif self.Meta.dao:
            self._dao_cache = self.Meta.dao()
        else:
            raise ValueError(f"{self.__class__.__name__}.Meta must set dao or dao_factory")
        return self._dao_cache

    def _pk_value(self) -> Any:
        """Return primary key value from instance or data (Meta.pk_field)."""
        pk = self.Meta.pk_field
        if self.instance is not None and hasattr(self.instance, pk):
            return getattr(self.instance, pk)
        return self.data.get(pk)

    def _peewee_field_names_from_dao(self) -> set:
        """Return set of Peewee model field names from bound DAO.

        Inspects dao.model_class._meta.fields and returns its keys as a set.
        """
        dao = self._get_dao()
        if not hasattr(dao, "model_class"):
            raise AttributeError("DAO must expose model_class")
        model_cls = dao.model_class
        if not hasattr(model_cls, "_meta") or not hasattr(model_cls._meta, "fields"):
            raise AttributeError("DAO.model_class must be a Peewee model with _meta.fields")
        return set(model_cls._meta.fields.keys())