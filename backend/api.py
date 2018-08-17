from enum import Enum


class Node:
    def __init__(self, id):
        self.ID = id


class Collection(Node):
    def __init__(self, id, label, rules):
        self.label = label
        self.ruleset = rules
        super.__init__(self, id)

    def items(self):
        raise NotImplementedError

    def has_item(ID):  # boolean
        raise NotImplementedError

    def addItems(items):
        raise NotImplementedError

    def removeItems(items):
        raise NotImplementedError

    def publish(self):
        self._public = True

    def unpublish(self):
        self._public = False


class CollectionRuleSet:
    def __init__(self, rules):
        self.rules = rules


class CollectionRule:
    def __init__(self, field, relation=None, condition=None):
        self.field = field          # criterion, column
        self.relation = relation    # op
        self.condition = condition  # value


class CollectionRuleField(Enum):
    pass


CollectionRelation = Enum(
    'EQUALS', 'NOT_EQUALS',
    'CONTAINS', 'NOT_CONTAINS',
    'GREATER_THAN', 'LESS_THAN',
    'STARTS_WITH', 'ENDS_WITH',
    module=__name__)
