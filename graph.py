from enum import Enum

uniswap_graph_url = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2"

class Sort(Enum):
    ASC = "asc"
    DESC = "desc"

    def __str__(self):
        return self.value


class Operator(Enum):
    GREATER_THAN = "_gt"
    GREATER_THAN_OR_EQUAL = "_gte"
    LESS_THAN = "_lt"
    NOT = "_not"
    IN = "_in"
    NOT_IN = "_not_in"
    CONTAINS = "_contains"
    NOT_CONTAINS = "_not_contains"
    STARTS_WITH = "_starts_with"
    ENDS_WITH = "_ends_with"
    NOT_STARTS_WITH = "_not_starts_with"
    NOT_ENDS_WITH = "_not_ends_with"

    def __str__(self):
        return self.value


class ConditionField:
    def __init__(self, name, value, operator=None):
        self._name = name
        self._value = value
        self.operator = operator

    @property
    def name(self):
        return self._name if not isinstance(self.operator, Operator) else "%s%s" % (self._name, self.operator)

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def value(self):
        if isinstance(self._value, str):
            return """ "%s" """ % self._value
        return self._value

    @value.setter
    def value(self, value):
        self._value = value


class LimitCondition:
    def __init__(self, limit):
        self.limit = limit

    def __str__(self):
        return "first: %d " % self.limit


class WhereCondition:
    def __init__(self, conditions):
        self.conditions = conditions

    def __str__(self):
        r = ""
        i = 0
        for condition in self.conditions:
            assert(isinstance(condition, ConditionField))
            if i > 0:
                r += ","
            r += "%(field_name)s: %(value)s" % {"field_name": condition.name, "value": condition.value}
            i += 1
        return "where:{%s}" % r if r is not "" else ""


class OrderCondition:
    def __init__(self, field, sorted_type):
        self.field = field
        self.sorted_type = sorted_type.lower()
        if self.sorted_type != "asc" and self.sorted_type != "desc":
            raise Exception("invalid sorted type: must be asc or desc")

    def __str__(self):
        return "orderBy: %s, orderDirection: %s" % (self.field, self.sorted_type)


class Conditions:
    def __init__(self, conditions=None):
        self.conditions = conditions

    def __str__(self):
        i = 0
        r = ""
        for condition in self.conditions:
            if i > 0:
                r += ", "
            r += str(condition)
            i += 1
        return r


class Field:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return " %s " % self.name


class NestedField(Field):
    def __init__(self, **kwargs):
        name, fields = kwargs.popitem()
        super().__init__(name)
        self.fields = Fields(fields)

    def __str__(self):
        return " %s{%s} " % (self.name, str(self.fields))


class Fields:
    def __init__(self, fields):
        self.fields = []
        for field in fields:
            if isinstance(field, str):
                self.fields.append(Field(field))
            else:
                (k, v) = field.popitem()
                f = Fields(v)
                self.fields.append({k: f})

    def __str__(self):
        r = ""
        for field in self.fields:
            if isinstance(field, Field):
                r += " %s" % str(field)
            else:
                (k, v) = field.popitem()
                r += " %s {%s}" % (k, v)
        return r


def create_query(query, conditions, fields):
    q = "{%(query)s(%(conditions)s){%(fields)s}}" % {"query": query, "conditions": str(conditions), "fields": fields}
    print(q)
    return q