#!/bin/bash
set -e
cd /mnt/c/temp/lab-models
mkdir -p outputs

echo "=== 1. Crear venv con uv (Python 3.12) ==="
if [ ! -d .venv ]; then
  ~/.local/bin/uv venv --python 3.12 .venv 2>&1 | tail -3
fi

echo ""
echo "=== 2. Instalar dependencias ==="
source .venv/bin/activate
~/.local/bin/uv pip install --quiet \
  scikit-learn numpy pandas \
  torch torchvision \
  2>&1 | tail -5
echo "  [ok] deps instaladas"

echo ""
echo "=== 3. Run Demo 1: Gradient Boosting (CPU) ==="
python 01_gradient_boosting.py 2>&1 | tee outputs/gbc.log | tail -25

echo ""
echo "=== 4. Run Demo 2: CNN PyTorch (GPU) ==="
python 02_cnn_pytorch.py 2>&1 | tee outputs/cnn.log | tail -30

echo ""
echo "=== 5. Resumen ==="
echo "Outputs en: $(pwd)/outputs/"
ls -la outputs/
