class Module:
    def __init__(self, funk, names: list, perms: str, access: list, template: str, desc: str):
        self.names = names
        self.funk = funk
        self.perms = perms
        self.access = access
        self.template = template
        self.desc = desc


class Filter:
    def __init__(self, funk, name: str, desc: str):
        self.funk = funk
        self.name = name
        self.desc = desc
