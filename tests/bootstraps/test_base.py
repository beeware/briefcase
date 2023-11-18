from briefcase.bootstraps.base import BaseGuiBootstrap


def test_base_bootstrap_fields():
    """Defined fields are implemented and implemented fields are defined."""
    for field in BaseGuiBootstrap.fields:
        assert field in BaseGuiBootstrap.__dict__

    for field in [
        attr
        for attr in BaseGuiBootstrap.__dict__
        if not attr.startswith("_")
        and attr not in {"fields", "display_name_annotation", "extra_context"}
    ]:
        assert field in BaseGuiBootstrap.fields
