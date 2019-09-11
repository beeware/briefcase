
class BaseCommand:
    def __init__(self, platform, output_format, parser, extra):
        self.platform = platform
        self.output_format = output_format

        self.add_options(parser)
        self.options = parser.parse_args(extra)

    def add_options(self, parser):
        pass


class CreateCommand(BaseCommand):
    def __call__(self):
        self.verify_tools()
        print("CREATE:", self.description)

    def verify_tools(self):
        "Verify that the tools needed to run this command exist"


class UpdateCommand(BaseCommand):
    def __call__(self):
        print("UPDATE:", self.description)


class BuildCommand(BaseCommand):
    def __call__(self):
        print("BUILD:", self.description)


class RunCommand(BaseCommand):
    def __call__(self):
        print("RUN:", self.description)


class PublishCommand(BaseCommand):
    def __call__(self):
        print("PUBLISH:", self.description)
