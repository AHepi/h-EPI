# This image is intentionally linux/amd64-only. A second architecture requires
# its own full authority-PDF replay before it can be claimed equivalent.
ARG UBUNTU_IMAGE=ubuntu:24.04@sha256:33ceb71981b602c1a7443a53469e4dba065f7503eab3078a2d7a57a2ab987517

FROM --platform=linux/amd64 ${UBUNTU_IMAGE} AS poppler-build

ARG UBUNTU_SNAPSHOT=20260828T000000Z
ARG POPPLER_VERSION=26.05.0
ARG POPPLER_SHA256=6fef27ff04f37db43054c86bcdff6128c9fb1f6af4ef3c8b369a7e9abd68d0bb

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    SOURCE_DATE_EPOCH=1787875200 \
    TZ=Etc/UTC

RUN apt-get --snapshot "${UBUNTU_SNAPSHOT}" update \
    && apt-get --snapshot "${UBUNTU_SNAPSHOT}" install -y --no-install-recommends \
        ca-certificates \
        cmake \
        curl \
        g++ \
        libfontconfig1-dev \
        libfreetype-dev \
        libjpeg-dev \
        liblcms2-dev \
        libopenjp2-7-dev \
        libpng-dev \
        ninja-build \
        pkg-config \
        xz-utils \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp/poppler-source

RUN curl --fail --location --proto '=https' --tlsv1.2 \
        --output poppler.tar.xz \
        "https://poppler.freedesktop.org/poppler-${POPPLER_VERSION}.tar.xz" \
    && echo "${POPPLER_SHA256}  poppler.tar.xz" | sha256sum --check --strict \
    && tar --extract --xz --file poppler.tar.xz --strip-components=1 \
        --no-same-owner \
    && cmake -S . -B /tmp/poppler-build -G Ninja \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX="/opt/poppler-${POPPLER_VERSION}" \
        -DCMAKE_INSTALL_LIBDIR=lib \
        '-DCMAKE_INSTALL_RPATH=$ORIGIN/../lib' \
        -DBUILD_CPP_TESTS=OFF \
        -DBUILD_GTK_TESTS=OFF \
        -DBUILD_MANUAL_TESTS=OFF \
        -DBUILD_QT5_TESTS=OFF \
        -DBUILD_QT6_TESTS=OFF \
        -DENABLE_BOOST=OFF \
        -DENABLE_CPP=OFF \
        -DENABLE_GLIB=OFF \
        -DENABLE_GOBJECT_INTROSPECTION=OFF \
        -DENABLE_GPGME=OFF \
        -DENABLE_LIBCURL=OFF \
        -DENABLE_LIBTIFF=OFF \
        -DENABLE_NSS3=OFF \
        -DENABLE_QT5=OFF \
        -DENABLE_QT6=OFF \
        -DENABLE_UTILS=ON \
        -DRUN_GPERF_IF_PRESENT=OFF \
    && cmake --build /tmp/poppler-build --parallel 2 \
    && cmake --install /tmp/poppler-build \
    && "/opt/poppler-${POPPLER_VERSION}/bin/pdfinfo" -v 2>&1 \
        | grep --fixed-strings --line-regexp "pdfinfo version ${POPPLER_VERSION}"

FROM --platform=linux/amd64 ${UBUNTU_IMAGE} AS lean-download

ARG UBUNTU_SNAPSHOT=20260828T000000Z
ARG LEAN_VERSION=4.33.1
ARG LEAN_SHA256=890afd185370f85666025b883914ab4f4b339136f8c96167b69cfb62aecaf235

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    SOURCE_DATE_EPOCH=1787875200 \
    TZ=Etc/UTC

RUN apt-get --snapshot "${UBUNTU_SNAPSHOT}" update \
    && apt-get --snapshot "${UBUNTU_SNAPSHOT}" install -y --no-install-recommends \
        ca-certificates \
        curl \
        zstd \
    && rm -rf /var/lib/apt/lists/* \
    && curl --fail --location --proto '=https' --tlsv1.2 \
        --output /tmp/lean.tar.zst \
        "https://github.com/leanprover/lean4/releases/download/v${LEAN_VERSION}/lean-${LEAN_VERSION}-linux.tar.zst" \
    && echo "${LEAN_SHA256}  /tmp/lean.tar.zst" | sha256sum --check --strict \
    && mkdir -p /opt/lean \
    && tar --extract --use-compress-program=unzstd --file /tmp/lean.tar.zst \
        --strip-components=1 --no-same-owner --directory /opt/lean \
    && rm /tmp/lean.tar.zst \
    && /opt/lean/bin/lean --version \
        | grep --fixed-strings 'Lean (version 4.33.1,' \
        | grep --fixed-strings 'commit 819816b2e0a3bf405af45ae5c7af2491d8f5bee6'

FROM --platform=linux/amd64 ${UBUNTU_IMAGE} AS replay

ARG UBUNTU_SNAPSHOT=20260828T000000Z
ARG POPPLER_24_PACKAGE=24.02.0-1ubuntu9.9

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PATH=/opt/cr-eib-venv/bin:/opt/lean/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SOURCE_DATE_EPOCH=1787875200 \
    TZ=Etc/UTC

LABEL org.opencontainers.image.source="https://github.com/AHepi/h-EPI" \
      org.opencontainers.image.title="CR-EIB cold-start operational replay" \
      org.opencontainers.image.version="0.2" \
      org.opencontainers.image.description="Pinned linux/amd64 replay environment; not semantic authority"

RUN apt-get --snapshot "${UBUNTU_SNAPSHOT}" update \
    && apt-get --snapshot "${UBUNTU_SNAPSHOT}" install -y --no-install-recommends \
        "libpoppler134=${POPPLER_24_PACKAGE}" \
        "poppler-utils=${POPPLER_24_PACKAGE}" \
        python3 \
        python3-pip \
        python3-venv \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv /opt/cr-eib-venv

COPY requirements-container.txt /tmp/requirements/

RUN /opt/cr-eib-venv/bin/python -m pip install --no-cache-dir --no-deps \
        --only-binary=:all: \
        --require-hashes \
        --requirement /tmp/requirements/requirements-container.txt \
    && /opt/cr-eib-venv/bin/python -m pip check \
    && rm -rf /tmp/requirements

COPY --from=poppler-build /opt/poppler-26.05.0 /opt/poppler-26.05.0
COPY --from=lean-download /opt/lean /opt/lean

RUN ln -s /opt/poppler-26.05.0/bin/pdfinfo /usr/local/bin/pdfinfo \
    && mkdir -p /authority /workspaces/h-EPI \
    && test -z "${LD_PRELOAD:-}" \
    && test -z "${LEAN_FIXED_APP_PATH:-}" \
    && test "$(uname -m)" = x86_64 \
    && pdftotext -v 2>&1 \
        | grep --fixed-strings --line-regexp 'pdftotext version 24.02.0' \
    && pdfinfo -v 2>&1 \
        | grep --fixed-strings --line-regexp 'pdfinfo version 26.05.0' \
    && lean --version \
        | grep --fixed-strings 'Lean (version 4.33.1,' \
        | grep --fixed-strings 'commit 819816b2e0a3bf405af45ae5c7af2491d8f5bee6' \
    && python --version 2>&1 | grep --extended-regexp '^Python 3\.12\.'

WORKDIR /workspaces/h-EPI

CMD ["bash"]
