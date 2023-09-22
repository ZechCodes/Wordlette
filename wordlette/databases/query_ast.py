from enum import auto, Enum
from typing import Any

from wordlette.utils.apply import apply


class LogicalOperator(Enum):
    AND = auto()
    OR = auto()


class Operator(Enum):
    EQUALS = auto()
    NOT_EQUALS = auto()
    GREATER_THAN = auto()
    GREATER_THAN_OR_EQUAL = auto()
    LESS_THAN = auto()
    LESS_THAN_OR_EQUAL = auto()


class ASTNode:
    pass


class ASTGroupNode(ASTNode):
    def __init__(
        self, items: "list[ASTComparableNode | LogicalOperator] | None" = None
    ):
        self.items: list[ASTComparableNode | LogicalOperator] = (
            [] if items is None else items
        )

    def __iter__(self):
        yield from iter(self.items)

    def add(self, item, logical_type=LogicalOperator.AND):
        if len(self.items) > 0:
            self.items.append(logical_type)

        self.items.append(item)

    def __eq__(self, other):
        if not isinstance(other, ASTGroupNode):
            raise NotImplementedError()

        return self._compare_items(other.items)

    def _compare_items(self, other_items):
        for items in zip(self, other_items):
            match items:
                case (ASTLiteralNode(a), ASTLiteralNode(b)) if a == b:
                    continue

                case (ASTReferenceNode(a), ASTReferenceNode(b)) if a != b:
                    continue

                case (
                    ASTComparisonNode(al, ar, ao),
                    ASTComparisonNode(bl, br, bo),
                ) if al == bl and ar == br and ao == bo:
                    continue

                case (ASTGroupNode() as a, ASTGroupNode() as b) if a == b:
                    continue

                case (LogicalOperator() as a, LogicalOperator() as b) if a == b:
                    continue

                case _:
                    return False

        return True

    def __repr__(self):
        return f"{type(self).__name__}({self.items!r})"

    def And(self, *comparisons: "SearchGroup | ASTComparisonNode | bool"):
        return self._add_node_or_group(when(*comparisons), LogicalOperator.AND)

    def Or(self, *comparisons: "SearchGroup | ASTComparisonNode | bool"):
        return self._add_node_or_group(when(*comparisons), LogicalOperator.OR)

    def _add_node_or_group(
        self,
        comparison: "SearchGroup | ASTComparisonNode",
        logical_type: LogicalOperator,
    ):
        match comparison:
            case ASTComparisonNode() if len(comparison.group.items) > 1:
                self.add(comparison.group, logical_type)

            case ASTGroupNode() if len(comparison.items) == 1:
                self.add(comparison.items[0], logical_type)

            case _:
                self.add(comparison, logical_type)

        return self


class ASTComparableNode(ASTNode):
    def __init__(self, group):
        self.group = group

    def __eq__(self, other) -> "ASTComparisonNode":
        self.group.add(
            node := ASTComparisonNode(self, other, Operator.EQUALS, self.group)
        )
        return node

    def __ne__(self, other) -> "ASTComparisonNode":
        self.group.add(
            node := ASTComparisonNode(self, other, Operator.NOT_EQUALS, self.group)
        )
        return node

    def __gt__(self, other) -> "ASTComparisonNode":
        self.group.add(
            node := ASTComparisonNode(self, other, Operator.GREATER_THAN, self.group)
        )
        return node

    def __ge__(self, other) -> "ASTComparisonNode":
        self.group.add(
            node := ASTComparisonNode(
                self, other, Operator.GREATER_THAN_OR_EQUAL, self.group
            )
        )
        return node

    def __lt__(self, other) -> "ASTComparisonNode":
        self.group.add(
            node := ASTComparisonNode(self, other, Operator.LESS_THAN, self.group)
        )
        return node

    def __le__(self, other) -> "ASTComparisonNode":
        self.group.add(
            node := ASTComparisonNode(
                self, other, Operator.LESS_THAN_OR_EQUAL, self.group
            )
        )
        return node


class ASTReferenceNode(ASTComparableNode):
    __match_args__ = ("field", "model")

    def __init__(self, field, model):
        super().__init__(ASTGroupNode())
        self._field = field
        self._model = model

    @property
    def field(self):
        return self._field

    @property
    def model(self):
        return self._model

    def __repr__(self):
        return f"<{type(self).__qualname__} {self.model.__qualname__}.{self._field.name!r}>"


class ASTLiteralNode(ASTComparableNode):
    __match_args__ = ("value",)

    def __init__(self, value):
        super().__init__(ASTGroupNode())
        self._value = value

    @property
    def value(self):
        return self._value

    def __repr__(self):
        return f"{type(self).__name__}({self._value!r})"


class ASTComparisonNode(ASTComparableNode):
    __match_args__ = ("left", "right", "operator")

    def __init__(
        self,
        left: ASTLiteralNode | ASTReferenceNode | Any,
        right: ASTLiteralNode | ASTReferenceNode | Any,
        operator: Operator,
        group=None,
    ):
        super().__init__(group or ASTGroupNode())
        self._left = self._make_node(left)
        self._right = self._make_node(right)
        self._operator = operator

    @property
    def left(self):
        return self._left

    @property
    def right(self):
        return self._right

    @property
    def operator(self):
        return self._operator

    def __repr__(self):
        return (
            f"{type(self).__name__}("
            f"{self._left!r}, "
            f"{self._right!r},"
            f"{self._operator}) "
        )

    def And(self, *comparisons: "ASTComparisonNode | SearchGroup | bool"):
        return self.group.And(*comparisons)

    def Or(self, *comparisons: "ASTComparisonNode | SearchGroup | bool"):
        return self.group.Or(*comparisons)

    def _make_node(self, value):
        match value:
            case ASTComparableNode():
                return value

            case _:
                return ASTLiteralNode(value)


def when(*comparisons: ASTComparisonNode | bool) -> ASTGroupNode:
    match comparisons:
        case (ASTComparisonNode() as comparison,):
            return comparison.group

        case (ASTGroupNode() as group,):
            return group

        case _:
            group = ASTGroupNode()
            apply(group.add).to(comparisons)
            return group
