class WorkerData:
    def __init__(self, name, categories, skill_levels=None):
        self.name = name
        self.categories = categories
        if skill_levels is None:
            self.skill_levels = [1] * len(categories)
        else:
            self.skill_levels = skill_levels

    def to_dict(self):
        return {
            "name": self.name,
            "skill_levels": self.skill_levels
        }

    @classmethod
    def from_dict(cls, data, categories):
        return cls(
            name=data["name"],
            categories=categories,
            skill_levels=data["skill_levels"]
        )