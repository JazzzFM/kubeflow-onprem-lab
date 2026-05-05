#!/bin/bash
set -e
cd /mnt/c/temp/lab-models

if [ ! -d .venv ]; then
  echo "ERROR: venv no existe (run-all.sh debe ejecutarse primero)"
  exit 1
fi

echo "=== Activar venv + instalar kfp SDK ==="
source .venv/bin/activate
~/.local/bin/uv pip install --quiet kfp 2>&1 | tail -5
python -c "import kfp; print(f'kfp version: {kfp.__version__}')"

echo ""
echo "=== Ejecutar pipeline KFP local ==="
python 03_kfp_pipeline.py 2>&1 | tee outputs/kfp_pipeline.log | tail -50

echo ""
echo "=== Outputs ==="
ls -la outputs/
