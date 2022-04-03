
def test_packaging_formats(package_command):
    assert package_command.packaging_formats == ['pkg', 'box']


def test_default_packaging_format(package_command):
    assert package_command.default_packaging_format == 'pkg'
