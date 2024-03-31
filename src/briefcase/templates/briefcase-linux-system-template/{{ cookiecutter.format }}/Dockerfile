FROM {{ cookiecutter.docker_base_image }}

# Set the working directory
WORKDIR /app

# Disable pip's warnings and SDL audio
ENV PIP_ROOT_USER_ACTION=ignore \
    PIP_NO_WARN_SCRIPT_LOCATION=0 \
    SDL_AUDIODRIVER=dummy

{% if cookiecutter.vendor_base == "debian" -%}
# Run apt non-interactively; use ARG so this only applies while building the image
ARG DEBIAN_FRONTEND="noninteractive"

# Install System python
RUN apt-get update -y && \
    apt-get install --no-install-recommends -y \
      python{{ cookiecutter.python_version|py_tag }}-dev \
      python{{ cookiecutter.python_version|py_tag }}-venv \
      python{{ cookiecutter.python_version|py_tag }}-pip
{%- elif cookiecutter.vendor_base == "rhel" -%}
# Install System python
RUN dnf install -y \
      python{{ cookiecutter.python_version|py_tag }}-devel \
      python{{ cookiecutter.python_version|py_tag }}-pip
{%- elif cookiecutter.vendor_base == "suse" -%}
# Install System python
RUN zypper install -y \
    python{{ cookiecutter.python_version|py_tag }}-devel \
    python{{ cookiecutter.python_version|py_tag }}-pip
{%- elif cookiecutter.vendor_base == "arch" -%}
# Install System python
RUN pacman -Syu --noconfirm \
    python{{ cookiecutter.python_version|py_tag }} \
    python-pip
{%- endif %}

# Upgrade pip et alia
# PEP 668 allows distros to mark the system Python as "externally managed". With this
# configuration, `pip install` will error when using the system Python. This setting
# ignores this configuration in the distro and allows for installing the latest pip.
RUN PIP_BREAK_SYSTEM_PACKAGES=1 \
    python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel

# As root, install system packages required by app
ARG SYSTEM_REQUIRES
{% if cookiecutter.vendor_base == "debian" -%}
RUN apt-get update -y && \
    apt-get install --no-install-recommends -y build-essential pkg-config git ${SYSTEM_REQUIRES}
{%- elif cookiecutter.vendor_base == "rhel" -%}
RUN dnf install -y gcc make rpm-build pkgconf-pkg-config git ${SYSTEM_REQUIRES}
{%- elif cookiecutter.vendor_base == "suse" -%}
RUN zypper install -y -t pattern devel_basis
RUN zypper install -y rpm-build pkgconf-pkg-config git ${SYSTEM_REQUIRES}
{%- elif cookiecutter.vendor_base == "arch" -%}
RUN pacman -Syu --noconfirm base-devel pkgconf git ${SYSTEM_REQUIRES}
{%- endif %}

{% if cookiecutter.use_non_root_user -%}
# Ensure Docker user UID:GID matches host user UID:GID (beeware/briefcase#403)
# Use --non-unique to avoid problems when the UID:GID of the host user
# collides with entries provided by the Docker container.
ARG HOST_UID
ARG HOST_GID
RUN groupadd --non-unique --gid $HOST_GID briefcase && \
    useradd --non-unique --uid $HOST_UID --gid $HOST_GID brutus --home /home/brutus && \
    mkdir -p /home/brutus && chown brutus:briefcase /home/brutus

# Use the brutus user for operations in the container
USER brutus
{%- endif %}

# ========== START USER PROVIDED CONTENT ==========
{{ cookiecutter.dockerfile_extra_content }}
