import subprocess
import os

from briefcase.exceptions import BriefcaseCommandError


def get_devices(sdk_path, sub=subprocess):
    # Add our `adb` to start of the path.
    env = dict(os.environ)
    env['PATH'] = str(sdk_path / 'platform-tools') + ':' + env.get('PATH', '')
    try:
        output = sub.check_output(['adb', 'devices'], env=env)
    except subprocess.CalledProcessError:
        raise BriefcaseCommandError("Unable to run `adb devices`")

    results = []
    for line in output.split('\n'):
        line = line.strip()
        if not line:
            continue
        if line == 'List of devices attached':
            continue
        if '\t' in line:
            first, rest = line.split('\t', 1)
            if rest.strip() == 'device':
                results.append(first)
    return results
