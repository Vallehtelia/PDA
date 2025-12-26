#!/bin/bash
set -e

MODEL_NAME="SmolLM2-360M-Instruct-Q4_K_M.gguf"
REPO_ID="bartowski/SmolLM2-360M-Instruct-GGUF"
MODEL_DIR="models"

echo "Downloading SmolLM2-360M-Instruct model..."

# Ensure hf CLI exists (huggingface_hub v1.x)
if ! command -v hf &> /dev/null; then
  echo "Installing/Updating huggingface_hub (includes 'hf' CLI)..."
  pip install -U huggingface_hub
  hash -r
fi

mkdir -p "$MODEL_DIR"

# Optional: slow connections
export HF_HUB_DOWNLOAD_TIMEOUT="${HF_HUB_DOWNLOAD_TIMEOUT:-60}"

echo "Downloading model file with hf..."
hf download "$REPO_ID" "$MODEL_NAME" --local-dir "$MODEL_DIR"

MODEL_PATH="$MODEL_DIR/$MODEL_NAME"

if [ -f "$MODEL_PATH" ]; then
  echo ""
  echo "Model downloaded successfully!"
  echo "Model location: $MODEL_PATH"
  echo ""
  echo "Update your config/config.yaml with:"
  echo "llm:"
  echo "  llama_cpp:"
  echo "    model_path: $MODEL_PATH"
else
  echo "ERROR: Model file not found at $MODEL_PATH"
  echo "Listing models dir:"
  ls -la "$MODEL_DIR" || true
  exit 1
fi