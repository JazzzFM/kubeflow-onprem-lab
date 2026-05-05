#!/bin/bash
set -e
cd /mnt/c/temp/lab-models
source .venv/bin/activate
echo "=== Instalar mlflow + requests + pyarrow (si faltan) ==="
~/.local/bin/uv pip install --quiet mlflow requests pyarrow 2>&1 | tail -3
echo "=== Ejecutar pipeline wine quality ==="
python /home/jazielflo/Courses/kubeflow-onprem-lab/models/04_wine_kfp_mlflow.py 2>&1 | tee outputs/wine_pipeline.log | tail -50
echo ""
echo "=== Resumen ==="
cat outputs/wine_pipeline_summary.json 2>/dev/null
