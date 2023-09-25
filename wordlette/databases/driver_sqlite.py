import sqlite3
from datetime import datetime, date, time
from typing import Type, Any, TypeVar, TypeGuard, Callable, get_origin, Generator

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
)
from wordlette.databases.statuses import (
    DatabaseStatus,
    DatabaseSuccessStatus,
    DatabaseExceptionStatus,
)
from wordlette.models import FieldSchema, Auto
from wordlette.utils.dependency_injection import inject
from wordlette.utils.suppress_with_capture import SuppressWithCapture

T = TypeVar("T")


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


class SQLiteDriver(DatabaseDriver, driver_name="sqlite"):
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

        if error:
            self._db.rollback()
            return DatabaseExceptionStatus(*error)

        session.close()
        return DatabaseSuccessStatus(self)

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
        self, *predicates: ASTGroupNode
    ) -> DatabaseStatus[list[DatabaseModel]]:
        ast = when(*predicates)
        with SuppressWithCapture(Exception) as error:
            session = self._db.cursor()
            result = self._select(ast, session)

        return (
            DatabaseExceptionStatus(*error) if error else DatabaseSuccessStatus(result)
        )

    async def sync_schema(self, models: set[Type[DatabaseModel]]) -> DatabaseStatus:
        session = self._db.cursor()
        with SuppressWithCapture(Exception) as error:
            for model in models:
                self._create_table(model, session)

        if error:
            self._db.rollback()
            return DatabaseExceptionStatus(*error)

        session.close()
        return DatabaseSuccessStatus(self)

    async def update(self, *items: DatabaseModel) -> DatabaseStatus:
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

    def _process_ast(
        self, ast: ASTGroupNode
    ) -> tuple[Type[DatabaseModel], list[DatabaseModel], str, list[Any]]:
        model = None
        tables = []
        where = []
        values = []
        node_stack = [iter(ast)]
        while node_stack:
            match next(node_stack[~0], None):
                case ASTGroupNode() as group:
                    node_stack.append(iter(group))

                case ASTReferenceNode(field, model):
                    name = f"{model.__model_name__}.{field.name}"
                    where.append(name)
                    tables.append(model)
                    model = model

                case ASTLiteralNode(value):
                    where.append("?")
                    values.append(value)

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

        return model, tables, " ".join(where), values

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
        model, tables, where, values = self._process_ast(predicates)
        query = self._build_select_query(tables, where)
        session.execute(query, values)
        result = session.fetchall()
        return [model(*self._validate_row_values(model, row)) for row in result]

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

    def _build_select_query(self, tables: list[DatabaseModel], where: str):
        return f"SELECT * FROM {tables[0].__model_name__} WHERE {where};"


def is_auto(obj: Any) -> TypeGuard[Auto]:
    return isinstance(obj, Auto)
