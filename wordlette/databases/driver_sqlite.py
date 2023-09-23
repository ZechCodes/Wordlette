import sqlite3
from typing import Type, Any

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
    DatabaseErrorStatus,
)
from wordlette.models import FieldSchema
from wordlette.utils.dependency_injection import inject
from wordlette.utils.suppress_with_capture import SuppressWithCapture


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

        return DatabaseErrorStatus(*error) if error else DatabaseSuccessStatus(self)

    async def disconnect(self) -> DatabaseStatus:
        with SuppressWithCapture(Exception) as error:
            self._db.close()
            self._connected = False

        return DatabaseErrorStatus(*error) if error else DatabaseSuccessStatus(self)

    async def add(self, *items: DatabaseModel) -> DatabaseStatus:
        with SuppressWithCapture(Exception) as error:
            session = self._db.cursor()
            for item in items:
                self._insert(item, session)

        return DatabaseErrorStatus(*error) if error else DatabaseSuccessStatus(self)

    async def delete(self, *items: DatabaseModel) -> DatabaseStatus:
        pass

    async def fetch(
        self, *predicates: ASTGroupNode
    ) -> DatabaseStatus[list[DatabaseModel]]:
        ast = when(*predicates)
        with SuppressWithCapture(Exception) as error:
            session = self._db.cursor()
            result = self._select(ast, session)

        return DatabaseErrorStatus(*error) if error else DatabaseSuccessStatus(result)

    async def sync_schema(self, models: set[Type[DatabaseModel]]) -> DatabaseStatus:
        with SuppressWithCapture(Exception) as error:
            session = self._db.cursor()
            for model in models:
                self._create_table(model, session)

        return DatabaseErrorStatus(*error) if error else DatabaseSuccessStatus(self)

    async def update(self, *items: DatabaseModel) -> DatabaseStatus:
        pass

    def _build_column(self, field: DatabaseProperty, pk: bool) -> str:
        column = [field.name, self._get_sqlite_type(field.type)]
        if pk:
            column.append("PRIMARY KEY")

        return " ".join(column)

    def _build_select_query(
        self, ast: ASTGroupNode
    ) -> tuple[str, list[Any], Type[DatabaseModel]]:
        model = None
        where = []
        tables = []
        values = []
        node_stack = [iter(ast)]
        while node_stack:
            match next(node_stack[~0], None):
                case ASTGroupNode() as group:
                    node_stack.append(iter(group))

                case ASTReferenceNode(field, model):
                    name = f"{model.__model_name__}.{field.name}"
                    where.append(name)
                    tables.append(model.__model_name__)
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

        query = ["SELECT * FROM", ", ".join(tables)]
        if where:
            query.extend(["WHERE", " ".join(where)])

        query.append(";")

        return " ".join(query), values, model

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
        columns = ", ".join(field.name for field in fields)
        values = [getattr(item, field.name) for field in fields]
        qs = ", ".join(["?"] * len(fields))
        session.execute(
            f"INSERT INTO {item.__model_name__} ({columns}) VALUES ({qs});", values
        )

    def _select(self, predicates: ASTGroupNode, session: sqlite3.Cursor):
        query, values, model = self._build_select_query(predicates)
        session.execute(query, values)
        result = session.fetchall()
        return [model(*row) for row in result]

    def _get_sqlite_type(self, type_: Type) -> str:
        return self.type_mapping.get(type_, "TEXT")
