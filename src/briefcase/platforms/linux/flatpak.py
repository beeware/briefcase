# An implementation would go here!

# needs system tools: flatpak and flatpak-builder
#
# also I used https://github.com/flatpak/flatpak-builder-tools/blob/master/pip/flatpak-pip-generator
# to transform eg: 'requirements.txt' into the "python3-requirements.json"
# 
# but really we want to transform the pyproject.toml directly and to have the
# transformer be a library not a standalone python program.
# 
# commands run:
#
# flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
# flatpak install flathub org.freedesktop.Platform//21.08 org.freedesktop.Sdk//21.08
# pip freeze > requirements.txt
# flatpak-pip-generator --requirements-file=requirements.txt
#
# org.zoic.hello.yaml:
#
#   app-id: org.zoic.hello
#   runtime: org.freedesktop.Platform
#   runtime-version: '21.08'
#   sdk: org.freedesktop.Sdk
#   command: hello.py
#   modules:
#     - name: hello
#       buildsystem: simple
#       build-commands:
#         - install -D hello.py /app/bin/hello.py
#       sources:
#         - type: file
#           path: hello.py
#     - python3-requirements.json
#   finish-args:
#     - "--socket=fallback-x11"
#     - "--socket=wayland"
#
# flatpak-builder --user --install --force-clean build-dir/ org.zoic.hello.yaml
# flatpak run -v org.zoic.hello
#
# and that got the app to pop up on my machine ...
#
# Issues:
# * the flakpak-builder manifest file is either json or yaml, it'll parse JSON
#   from a tempfile or /dev/stdin but it interprets include paths relative so
#   use absolute paths if that's what you want to do.
# * flatpak-builder is in C (!)
# * flatpak-pip-generator is a python program which translates requirements.txt
#   files into includable "python3-requirements.json" module *but* it isn't 
#   distributed on pypi, isn't a library and doesn't load pyproject.toml so I
#   suspect we're better off doing this stuff here instead.


