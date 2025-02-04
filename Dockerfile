# IMPORTANT: Changes in this file do not automatically affect the Docker image used by the CI server.
# You need to build and push it manually, see the wiki for details:
# https://github.com/hyrise/hyrise/wiki/Docker-Image

FROM ubuntu:24.04
ENV DEBIAN_FRONTEND noninteractive
ENV TZ=Europe/London
ARG USERNAME=reproduction
ARG USER_UID=1000
ARG USER_GID=$USER_UID
RUN apt-get update \
    && apt-get install -y \
        autoconf \
        bash-completion \
        bc \
        bison \
        clang-17 \
        gcc-11 \
        cmake \
        curl \
        flex \
        git \
        graphviz \
        libboost-all-dev \
        libbz2-dev \
        libcurl4-openssl-dev \
        libhwloc-dev \
        libncurses5-dev \
        libnuma-dev \
        libnuma1 \
        libpq-dev \
        libreadline-dev \
        libsqlite3-dev \
        libssl-dev \
        libtbb-dev \
        libxerces-c-dev \
        libzstd-dev \
        lld \
        lsb-release \
        man \
        numactl \
        parallel \
        pkg-config \
        postgresql-server-dev-all \
        python3 \
        python3-pip \
        software-properties-common \
        sudo \
        time \
        valgrind \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && ln -sf /usr/bin/llvm-symbolizer-17 /usr/bin/llvm-symbolizer \
    && pip3 --break-system-packages install scipy pandas matplotlib \
    && echo foo $USER_GID $USERNAME $USER_UID \
    && groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \

USER $USERNAME

