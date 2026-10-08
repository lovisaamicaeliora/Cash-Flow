#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

if ! command -v buildozer >/dev/null 2>&1; then
  echo "Buildozer belum terinstall. Jalankan:"
  echo "python3 -m pip install buildozer cython"
  exit 1
fi

buildozer android debug
