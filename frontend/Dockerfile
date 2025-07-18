FROM node:20

RUN --mount=type=cache,target=/var/lib/apt,id=node20_apt_cache <<APT bash
    set -e
#    apt update
#    apt install -y --no-install-recommends ca-certificates
    cat>/etc/apt/sources.list.d/debian.sources<<EOF
Types: deb
URIs: https://mirrors.tuna.tsinghua.edu.cn/debian
Suites: bookworm bookworm-updates
Components: main
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg

Types: deb
URIs: http://deb.debian.org/debian-security
Suites: bookworm-security
Components: main
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg
EOF
    apt update
APT

WORKDIR /app

# Copy package files first for better layer caching
COPY package*.json ./

# Install build dependencies for node-gyp
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    make \
    g++ \
    build-essential \
    pkg-config \
    libcairo2-dev \
    libpango1.0-dev \
    libjpeg-dev \
    libgif-dev \
    librsvg2-dev \
    && rm -rf /var/lib/apt/lists/*

RUN npm install --registry=https://registry.npmmirror.com

# Copy the frontend code
COPY . .

ENV NEXT_PUBLIC_VERCEL_ENV production

RUN npm run build

EXPOSE 3000

# Default command is dev, but can be overridden in docker-compose
CMD ["npm", "start"]