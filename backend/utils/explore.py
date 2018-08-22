from sqlalchemy.inspection import inspect
from geonature.utils.env import DB


def model_by_name(name):
    for m in DB._decl_class_registry.values():
        if hasattr(m, '__name__') and m.__name__ == name:
            return m


def model_from_tablename(tablename):
    for m in DB._decl_class_registry.values():
        if hasattr(m, '__tablename__') and m.__tablename__ == tablename:
            return m


def get_relation_models(relations):
    # referred_classes = [r.mapper.class_ for r in i.relationships]
    def relation_models(relation):
        return [model_from_tablename(c.table.name)
                for c in relation.remote_side]

    return [m for relation in relations
            for m in relation_models(relation)]


def get_selection_models(selection):
    updated_selection = []

    def selection_models(label):
        # selection = ['User.name', 'User.addresses.email']
        elements = label.split('.')
        model = model_by_name(elements[0])
        if len(elements) == 2:
            updated_selection.append(getattr(model, elements[-1]))
            return [model]
        elif len(elements) > 2:
            relations = inspect(model).relationships
            models = get_relation_models(relations)
            updated_selection.append(getattr(models[-1], elements[-1]))
            return [model, *models]

    uniq = []
    models = [m for s in selection for m in selection_models(s)]
    [uniq.append(m) for m in models if m not in uniq]
    return (updated_selection, uniq)

# [ ] User
# [*]    name
# [*]    addresses.email
# selection = ['User.name', 'User.addresses.email']
# selection, models = get_selection_models(selection)
# print('selection:\n\t', selection)
# print('models:\n\t', models)
#
# relations = inspect(models[0]).relationships
# r_models = get_relation_models(relations)
# print('relation_models:\n\t', r_models)
# # print([list(zip(selection, row))
# #        for row in session.query(*models)
# #                          .join(*r_models)
# #                          .filter(User.name == new_person.name).all()])
#
# q = session.query(*selection)
# q = q.join(*get_relation_models(relations))
# print('prepared query:\n\t', q)
# print(q.all())
