from wordlette.databases.query_ast import ASTReferenceNode
from wordlette.models import FieldSchema, Field


class DatabaseProperty(Field):
    def __get__(self, instance, owner):
        if instance is None:
            return ASTReferenceNode(self, owner)

        return super().__get__(instance, owner)


class Property(FieldSchema, field_type=DatabaseProperty):
    pass
