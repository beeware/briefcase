
CFLAGS=$(shell /app/bin/python3-config --cflags)
LDFLAGS=$(shell /app/bin/python3-config --ldflags)

all: {{ cookiecutter.app_name }}

{{ cookiecutter.app_name }}: main.c
	gcc -o {{ cookiecutter.app_name }} $^ $(CFLAGS) $(LDFLAGS) -lpython{{ '.'.join(cookiecutter.python_version.split('.')[:2]) }}

clean:
	rm -f {{ cookiecutter.app_name }}

install:
	cp {{ cookiecutter.app_name }} /app/bin/{{ cookiecutter.app_name }}

.PHONY: all clean install
