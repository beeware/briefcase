import json
from importlib import metadata
from pathlib import Path


def _is_editable_pep610(dist_name: str) -> bool:
    """Check if briefcase is installed as editable build.

    The check requires, that the tool that installs briefcase support PEP610 (eg. pip
    since v20.1).
    """
    try:
        dist = metadata.distribution(dist_name)
    except metadata.PackageNotFoundError:
        raise

    direct_url = dist.read_text("direct_url.json")
    if direct_url is None:
        return False

    try:
        data = json.loads(direct_url)
        return data.get("dir_info", {}).get("editable", False)
    except Exception:
        return False


IS_EDITABLE = _is_editable_pep610("briefcase")
REPO_ROOT = Path(__file__).parent.parent.parent if IS_EDITABLE else None
