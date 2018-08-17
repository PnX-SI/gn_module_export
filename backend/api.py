from enum import Enum
from geonature.utils.env import DB


class Node:  # Query implementation bridge
    def __init__(self, id):
        self.ID = id


class Collection(Node):
    def __init__(self, id, label, rules):
        self._public = False
        self.label = label
        self.ruleset = rules
        super().__init__(self, id)

    def items(self):  # {error: message, collection: data}
        selection = [rule for rule in self.ruleset.rules if not rule.relation]
        filters = [rule for rule in self.ruleset.rules if rule.relation]
        return DB.session.query(selection).filter(filters).all()

    def has_item(ID):  # boolean
        raise NotImplementedError

    def addItems(items):  # {error: message, collection: data}
        # update mutation
        raise NotImplementedError

    def removeItems(items):  # {error: message, collection: data}
        # update mutation
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

RelMap = {
    'EQUALS': '=',
    'NOT_EQUALS': '!=',
    'GREATER_THAN': '>',
    'LESS_THAN': '<',
    'CONTAINS': 'LIKE',
    'NOT_CONTAINS': 'NOT LIKE',
    'STARTS_WITH': 'LIKE',
    'ENDS_WITH': 'NOT LIKE'
}
