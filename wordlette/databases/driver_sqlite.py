import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, date, time
from os.path import sep
from typing import Type, Any, TypeVar, TypeGuard, Callable, get_origin, Generator, Self

from wordlette.configs import ConfigModel
from wordlette.databases.drivers import DatabaseDriver
from wordlette.databases.models import DatabaseModel
from wordlette.databases.properties import DatabaseProperty
from wordlette.databases.query_ast import (
    ASTGroupNode,
    when,
    ASTReferenceNode,
    ASTLiteralNode,
    ASTLogicalOperatorNode,
    ASTComparisonNode,
    ASTOperatorNode,
    ASTGroupFlagNode,
    ResultOrdering,
)
from wordlette.databases.settings_forms import DatabaseSettingsForm
from wordlette.databases.statuses import (
    DatabaseStatus,
    DatabaseSuccessStatus,
    DatabaseExceptionStatus,
)
from wordlette.forms.field_types import TextField, Link, SubmitButton
from wordlette.models import FieldSchema, Auto
from wordlette.utils.dependency_injection import inject
from wordlette.utils.suppress_with_capture import SuppressWithCapture

T = TypeVar("T")


placeholder_example_path = "/path/to/database.db" if sep == "/" else r"C:\\path\to\database.db"


class SQLiteSettingsForm(DatabaseSettingsForm):
    filename: str @ TextField(
        placeholder=placeholder_example_path,
        label="Where should your SQLite database be located?",
    )

    buttons = (
        Link("Back", href="/configure-database"),
        SubmitButton("Next", type="submit"),
    )


@dataclass
class SelectQuery:
    limit: int = 0
    model: Type[DatabaseModel] | None = None
    offset: int = 0
    order_by: dict[str, ResultOrdering] = field(default_factory=dict)
    tables: list[DatabaseModel] = field(default_factory=list)
    values: list[Any] = field(default_factory=list)
    where: str = ""


class SQLConstraint(Auto):
    def __init__(self, name: str, value: str):
        self.name = name
        self.value = value

    def __call__(self, *args, **kwargs):
        return self

    def __repr__(self):
        return f"SQL{self.name.title()}Constraint[{self.value}]"


class SQLAutoIncrement(SQLConstraint):
    def __init__(self):
        super().__init__("", "AUTOINCREMENT")

    def __repr__(self):
        return type(self).__name__


class SQLiteConfig(ConfigModel):
    filename: str @ FieldSchema


class SQLiteDriver(DatabaseDriver, driver_name="sqlite", nice_name="SQLite"):
    __settings_form__ = SQLiteSettingsForm

    logical_operator_mapping = {
        ASTLogicalOperatorNode.AND: "AND",
        ASTLogicalOperatorNode.OR: "OR",
    }

    operator_mapping = {
        ASTOperatorNode.EQUALS: "=",
        ASTOperatorNode.NOT_EQUALS: "!=",
        ASTOperatorNode.GREATER_THAN: ">",
        ASTOperatorNode.GREATER_THAN_OR_EQUAL: ">=",
        ASTOperatorNode.LESS_THAN: "<",
        ASTOperatorNode.LESS_THAN_OR_EQUAL: "<=",
    }

    auto_value_factories = {
        int: SQLAutoIncrement(),
        datetime: SQLConstraint("DEFAULT", "datetime()"),
        date: SQLConstraint("DEFAULT", "date()"),
        time: SQLConstraint("DEFAULT", "time()"),
    }

    type_validators = {
        datetime: lambda value: value,  # No-op to avoid type conflict with date
        date: lambda value: value.split()[0],
    }

    type_mapping = {
        int: "INTEGER",
        str: "TEXT",
        float: "REAL",
        bool: "INTEGER",
    }

    def __init__(self):
        self._connected = False
        self._db: sqlite3.Connection | None = None

    @property
    def connected(self) -> bool:
        return self._connected

    async def connect(self, config: SQLiteConfig @ inject = None) -> DatabaseStatus:
        with SuppressWithCapture(Exception) as error:
            self._db = sqlite3.connect(config.filename)
            self._connected = True

        return DatabaseExceptionStatus(*error) if error else DatabaseSuccessStatus(self)

    async def disconnect(self) -> DatabaseStatus:
        with SuppressWithCapture(Exception) as error:
            self._db.close()
            self._connected = False

        return DatabaseExceptionStatus(*error) if error else DatabaseSuccessStatus(self)

    async def add(self, *items: DatabaseModel) -> DatabaseStatus:
        session = self._db.cursor()
        with SuppressWithCapture(Exception) as error:
            for item in items:
                self._insert(item, session)
                self._sync_with_last_inserted(item, session)

        if error:
            self._db.rollback()
            return DatabaseExceptionStatus(*error)

        session.close()
        return DatabaseSuccessStatus(self)

    async def count(
        self, *predicates: ASTGroupNode | Type[DatabaseModel]
    ) -> DatabaseStatus[int]:
        ast = when(*predicates)
        with SuppressWithCapture(Exception) as error:
            session = self._db.cursor()
            result = self._count(ast, session)

        return (
            DatabaseExceptionStatus(*error) if error else DatabaseSuccessStatus(result)
        )

    async def delete(self, *items: DatabaseModel) -> DatabaseStatus:
        models = {}
        for item in items:
            models.setdefault(type(item), []).append(item)

        session = self._db.cursor()
        for model, items in models.items():
            with SuppressWithCapture(Exception) as error:
                self._delete_rows(model, items, session)

            if error:
                self._db.rollback()
                return DatabaseExceptionStatus(*error)

        session.close()
        return DatabaseSuccessStatus(self)

    async def fetch(
        self, *predicates: ASTGroupNode | Type[DatabaseModel]
    ) -> DatabaseStatus[list[DatabaseModel]]:
        ast = when(*predicates)
        with SuppressWithCapture(Exception) as error:
            session = self._db.cursor()
            result = self._select(ast, session)

        return (
            DatabaseExceptionStatus(*error) if error else DatabaseSuccessStatus(result)
        )

    async def sync_schema(
        self, models: set[Type[DatabaseModel]]
    ) -> DatabaseStatus[Self]:
        session = self._db.cursor()
        with SuppressWithCapture(Exception) as error:
            for model in models:
                self._create_table(model, session)

        if error:
            self._db.rollback()
            return DatabaseExceptionStatus(*error)

        session.close()
        return DatabaseSuccessStatus(self)

    async def update(self, *items: DatabaseModel) -> DatabaseStatus[Self]:
        models = {}
        for item in items:
            models.setdefault(type(item), []).append(item)

        session = self._db.cursor()
        for model, items in models.items():
            with SuppressWithCapture(Exception) as error:
                self._update_rows(model, items, session)

            if error:
                self._db.rollback()
                return DatabaseExceptionStatus(*error)

        session.close()
        return DatabaseSuccessStatus(self)

    def _build_column(self, field: DatabaseProperty, pk: bool) -> str:
        column = [field.name, self._get_sqlite_type(field.type)]
        if pk:
            column.append("PRIMARY KEY")

        if is_auto(field.default):
            match self.get_value_factory(field):
                case SQLAutoIncrement():
                    column.append("AUTOINCREMENT")

                case SQLConstraint() as constraint:
                    column.append(constraint.name)
                    column.append(f"({constraint.value})")

        return " ".join(column)

    def _process_ast(self, ast: ASTGroupNode) -> SelectQuery:
        query = SelectQuery(
            limit=ast.max_results,
            offset=ast.results_page * ast.max_results,
            order_by=self._process_ordering(ast.sorting),
        )
        where = []
        node_stack = [iter(ast)]
        while node_stack:
            match next(node_stack[~0], None):
                case ASTGroupNode() as group:
                    node_stack.append(iter(group))

                case ASTReferenceNode(None, model):
                    query.tables.append(model)
                    query.model = query.model or model

                case ASTReferenceNode(field, model):
                    name = f"{model.__model_name__}.{field.name}"
                    where.append(name)
                    query.tables.append(model)
                    query.model = query.model or model

                case ASTLiteralNode(value):
                    where.append("?")
                    query.values.append(value)

                case ASTLogicalOperatorNode() as op:
                    where.append(self.logical_operator_mapping[op])

                case ASTOperatorNode() as op:
                    where.append(self.operator_mapping[op])

                case ASTComparisonNode(left, right, op):
                    node_stack.append(iter((left, op, right)))

                case ASTGroupFlagNode.OPEN:
                    if len(node_stack) > 1:
                        where.append("(")

                case ASTGroupFlagNode.CLOSE:
                    if len(node_stack) > 1:
                        where.append(")")

                case None:
                    node_stack.pop()

                case node:
                    raise TypeError(f"Unexpected node type: {node}")

        query.where = " ".join(where)
        return query

    def _process_ordering(
        self, sorting: list[ASTReferenceNode]
    ) -> dict[str, ResultOrdering]:
        return {
            f"{ref.model.__model_name__}.{ref.field.name}": ref.ordering
            for ref in sorting
        }

    def _create_table(self, model: Type[DatabaseModel], session: sqlite3.Cursor):
        pk = self._find_primary_key(model)
        columns = ", ".join(
            self._build_column(field, field.name == pk)
            for field in model.__fields__.values()
        )
        session.execute(
            f"CREATE TABLE IF NOT EXISTS {model.__model_name__} ({columns});"
        )

    def _find_primary_key(self, model: Type[DatabaseModel]) -> str:
        fields = list(model.__fields__.values())
        if name := next((f.name for f in fields if f.name.lower() == "id"), None):
            return name

        for field in fields:
            if field.type is int or field.name.casefold() == "id":
                return field.name

        return next(iter(fields)).name

    def _insert(self, item: DatabaseModel, session: sqlite3.Cursor):
        fields = list(item.__fields__.values())
        data = {
            field.name: value
            for field in fields
            if not is_auto(value := getattr(item, field.name))
        }
        qs = ", ".join(["?"] * len(data))
        columns = ", ".join(data.keys())
        values = tuple(data.values())
        session.execute(
            f"INSERT INTO {item.__model_name__} ({columns}) VALUES ({qs});", values
        )

    def _update_rows(
        self,
        model: Type[DatabaseModel],
        items: list[DatabaseModel],
        session: sqlite3.Cursor,
    ):
        pk = self._find_primary_key(model)
        fields = list(model.__fields__.values())
        for item in items:
            values = (getattr(item, field.name) for field in fields if field.name != pk)
            assignments = ", ".join(
                f"{field.name} = ?" for field in fields if field.name != pk
            )
            session.execute(
                f"UPDATE {model.__model_name__} SET {assignments} WHERE {pk} = ?;",
                (*values, getattr(item, pk)),
            )

    def _delete_rows(
        self,
        model: Type[DatabaseModel],
        items: list[DatabaseModel],
        session: sqlite3.Cursor,
    ):
        pk = self._find_primary_key(model)
        keys = [getattr(item, pk) for item in items]
        qs = ", ".join(["?"] * len(items))
        session.execute(
            f"DELETE FROM {model.__model_name__} WHERE {pk} IN ({qs});", keys
        )

    def _select(self, predicates: ASTGroupNode, session: sqlite3.Cursor):
        query = self._process_ast(predicates)
        query_str = self._build_select_query(query)
        session.execute(query_str, query.values)
        result = session.fetchall()
        return [
            query.model(*self._validate_row_values(query.model, row)) for row in result
        ]

    def _count(self, predicates: ASTGroupNode, session: sqlite3.Cursor):
        query = self._process_ast(predicates)
        query_str = self._build_count_query(query)
        session.execute(query_str, query.values)
        result = session.fetchone()
        return result[0]

    def _validate_row_values(
        self, model: Type[DatabaseModel], row: tuple[Any]
    ) -> Generator[Any, None, None]:
        for field, value in zip(model.__fields__.values(), row):
            if validator := self._find_type_validator(field.type, value):
                yield validator(value)
            else:
                yield value

    def _find_type_validator(
        self, type_hint: Type[T], value: Any
    ) -> Callable[[Any], T] | None:
        hint = get_origin(type_hint) or type_hint
        for validator_type, validator in self.type_validators.items():
            if issubclass(hint, validator_type):
                return validator

        return None

    def _get_sqlite_type(self, type_: Type) -> str:
        return self.type_mapping.get(type_, "TEXT")

    def _build_select_query(self, query: SelectQuery):
        query_builder = [f"SELECT * FROM {query.model.__model_name__}"]
        if query.where:
            query_builder.append(f"WHERE {query.where}")

        if query.limit > 0:
            query_builder.append(f"LIMIT {query.limit}")

            if query.offset > 0:
                query_builder.append(f"OFFSET {query.offset}")

        if query.order_by:
            ordering = ", ".join(
                f"{column} {'ASC' if ordering is ResultOrdering.ASCENDING else 'DESC'}"
                for column, ordering in query.order_by.items()
            )
            query_builder.append("ORDER BY")
            query_builder.append(ordering)

        return " ".join(query_builder) + ";"

    def _build_count_query(self, query: SelectQuery):
        query_builder = [f"SELECT Count(*) FROM {query.model.__model_name__}"]
        if query.where:
            query_builder.append(f"WHERE {query.where}")

        if query.limit > 0:
            query_builder.append(f"LIMIT {query.limit}")

            if query.offset > 0:
                query_builder.append(f"OFFSET {query.offset}")

        return " ".join(query_builder) + ";"

    def _sync_with_last_inserted(self, item: DatabaseModel, session: sqlite3.Cursor):
        pk = self._find_primary_key(type(item))
        result = session.execute("SELECT last_insert_rowid();").fetchone()
        result = self._validate_row_values(type(item), result)
        for field, value in zip(item.__fields__.values(), result):
            item.__field_values__[field.name] = value


def is_auto(obj: Any) -> TypeGuard[Auto]:
    return isinstance(obj, Auto)
