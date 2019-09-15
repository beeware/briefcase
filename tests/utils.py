from briefcase.config import BaseConfig


class SimpleAppConfig(BaseConfig):
    def __init__(self, name, template=None, **kwargs):
        self.name = name
        self.template = template
        super().__init__(**kwargs)
