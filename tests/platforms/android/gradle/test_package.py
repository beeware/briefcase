def test_packaging_formats(package_command):
    assert package_command.packaging_formats == ["aab", "apk", "debug-apk"]
