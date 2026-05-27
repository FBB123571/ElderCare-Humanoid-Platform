#!/usr/bin/env bash
# GitHub 直连推送（绕过本机 127.0.0.1 代理，避免 Proxy CONNECT timeout）
set -euo pipefail
cd "$(dirname "$0")/.."

export NO_PROXY='*'
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY all_proxy

git -c http.proxy= -c https.proxy= push origin "${1:-main}"
