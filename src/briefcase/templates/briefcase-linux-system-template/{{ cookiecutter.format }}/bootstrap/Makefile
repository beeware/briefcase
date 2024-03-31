CFLAGS=$(shell /usr/bin/python{{ cookiecutter.python_version|py_tag }}-config --cflags --embed)
LDFLAGS=$(shell /usr/bin/python{{ cookiecutter.python_version|py_tag }}-config --ldflags --embed)

all: {{ cookiecutter.app_name }}

pyversion.h:
	python{{ cookiecutter.python_version|py_tag }} -c "import sys; print(f'#define PY_TAG \"{sys.version_info.major}.{sys.version_info.minor}\"')" > pyversion.h

{{ cookiecutter.app_name }}: main.c pyversion.h
	gcc -o {{ cookiecutter.app_name }} $^ $(CFLAGS) $(LDFLAGS) -fPIE

clean:
	rm -rf ../{{ cookiecutter.app_name }}-{{ cookiecutter.version }}/usr/bin
	rm -f {{ cookiecutter.app_name }} pyversion.h

install: all
	mkdir -p ../{{ cookiecutter.app_name }}-{{ cookiecutter.version }}/usr/bin
	cp {{ cookiecutter.app_name }} ../{{ cookiecutter.app_name }}-{{ cookiecutter.version }}/usr/bin

.PHONY: all clean install
