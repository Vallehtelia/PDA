#!/bin/bash
set -e

echo "Installing llama.cpp for Orja assistant..."

echo "Installing system dependencies..."
sudo apt update
sudo apt install -y git cmake build-essential libopenblas-dev pkg-config || true

# Try to install curl dev (preferred). If it fails, we'll build with LLAMA_CURL=OFF.
if sudo apt install -y libcurl4-openssl-dev; then
  CURL_FLAG=""
  echo "libcurl dev installed: building with CURL support."
else
  CURL_FLAG="-DLLAMA_CURL=OFF"
  echo "WARNING: libcurl dev not available. Building with -DLLAMA_CURL=OFF"
fi

echo "Cloning llama.cpp..."
if [ ! -d "vendor/llama.cpp" ]; then
  git clone https://github.com/ggerganov/llama.cpp vendor/llama.cpp
else
  echo "llama.cpp already exists, updating..."
  (cd vendor/llama.cpp && git pull)
fi

echo "Building llama.cpp with OpenBLAS..."
cd vendor/llama.cpp
rm -rf build
mkdir -p build
cd build

cmake -B . -DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS ${CURL_FLAG} ..
cmake --build . --config Release -j "$(nproc)"

echo ""
echo "llama.cpp build complete!"
echo "Binary location: $(pwd)/bin/llama-cli"
echo ""
echo "Update your config/config.yaml with:"
echo "llm:"
echo "  llama_cpp:"
echo "    bin_path: $(pwd)/bin/llama-cli"