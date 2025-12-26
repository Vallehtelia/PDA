#!/bin/bash

# Download Qwen2.5-0.5B-Instruct GGUF model for Orja assistant

set -e

MODEL_NAME="Qwen2.5-0.5B-Instruct-Q4_K_M.gguf"
MODEL_DIR="models"

echo "Downloading Qwen2.5-0.5B-Instruct model..."

if ! command -v huggingface-cli &> /dev/null; then
    echo "Installing huggingface-hub..."
    pip install huggingface_hub
fi

mkdir -p "$MODEL_DIR"

echo "Downloading model file..."
huggingface-cli download bartowski/Qwen2.5-0.5B-Instruct-GGUF "$MODEL_NAME" --local-dir "$MODEL_DIR" --local-dir-use-symlinks False

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
    echo "Error: Model download failed"
    exit 1
fi

