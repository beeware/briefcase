# Briefcase with Offline Template embedded 

This is a fork of the original briefcase project with several embedded templates.

## Installation

### Install with pip

You may directly install it with pip.

```Bash
git config --system core.longpaths true
pip install git+https://github.com/cycleuser/briefcase.git
```

If you can hardly visit GtiHub, please use the commands below:

```Bash
git config --system core.longpaths true
pip install git+https://gitlab.com/GeoPyTool/briefcase.git
```

### Clone and Install



Please notice that the path can be really long, so you may need to set `core.longpaths` to `true` in your git config. But you may still encounter some problems like `No such file or directory` errors on some templates.

To sole this, just go to a directory with a short path, and then clone the repository.
For example:

```Bash
cd D:/
git clone https://github.com/cycleuser/briefcase.git
cd briefcase
pip install .
```

## Use it

Then use an `--offline` flag to use the embedded templates.

```Bash
python -m briefcase new --offline
```

![image](https://github.com/cycleuser/briefcase/assets/6130092/31269588-c663-4431-8d8d-84c81d7c5c1f)


If you want to use onlie templates, just remove the `--online` flag.

```Bash
python -m briefcase new
```
![image](https://github.com/cycleuser/briefcase/assets/6130092/e008a59e-5dad-4f27-95a3-f12b13af61a8)
