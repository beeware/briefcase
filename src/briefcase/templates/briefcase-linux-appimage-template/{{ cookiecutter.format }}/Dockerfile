{% if cookiecutter.manylinux_image -%}
FROM quay.io/pypa/{{ cookiecutter.manylinux_image }}
{%- else %}
# Ubuntu:18.04 based AppImages are for legacy projects
FROM ubuntu:18.04
{%- endif %}

# Set the working directory
WORKDIR /app

# Disable pip's warnings
ENV PIP_ROOT_USER_ACTION=ignore \
    PIP_NO_WARN_SCRIPT_LOCATION=0

{% if cookiecutter.vendor_base == "debian" -%}
# Make sure installation of tzdata is non-interactive
ENV DEBIAN_FRONTEND="noninteractive"

# Install git and file (for linuxdeploy)
RUN apt-get update -y && \
    apt-get install --no-install-recommends -y git file
{%- else -%}
# Install git and file (for linuxdeploy)
RUN yum install -y git file
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
{%- endif %}

# As root, Install system packages required by app
ARG SYSTEM_REQUIRES
{% if cookiecutter.vendor_base == "debian" -%}
RUN apt-get install --no-install-recommends -y build-essential ${SYSTEM_REQUIRES}
{%- else -%}
RUN yum install -y gcc make pkgconfig ${SYSTEM_REQUIRES}
{%- endif %}

{% if cookiecutter.use_non_root_user -%}
# Use the brutus user for operations in the container
USER brutus
{%- endif %}

# Configure builds so that clang isn't required, and put the Standalone Python on the build path
ENV CC="gcc -pthread"
ENV PATH="/app/{{ cookiecutter.formal_name }}.AppDir/usr/python/bin:${PATH}"

# ========== START USER PROVIDED CONTENT ==========
{{ cookiecutter.dockerfile_extra_content }}
