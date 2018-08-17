class Node:
    def __init__(self, id):
        self.ID = id


class Collection(Node):
    def __init__(self, id, ruleset):
        self.ruleset = ruleset
        super.__init__(self, id)


class RuleSet:
    def __init__(self, rules):
        self.rules = rules


class Rule:
    def __init__(self, column_header, operator, value):
        self.header = column_header
        self.op = operator
        self.val = value
