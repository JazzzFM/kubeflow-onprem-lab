#!/bin/bash
set -e
echo "=== Generar CDI spec en modo WSL ==="
sudo -n nvidia-ctk cdi generate --output=/etc/cdi/nvidia.yaml --mode=wsl 2>&1 | tail -10

echo ""
echo "=== Spec generada ==="
ls -la /etc/cdi/
echo ""
echo "=== Primeros 30 lineas de /etc/cdi/nvidia.yaml ==="
head -30 /etc/cdi/nvidia.yaml 2>/dev/null

echo ""
echo "=== nvidia-ctk cdi list ==="
nvidia-ctk cdi list 2>&1 | head -5

echo ""
echo "=== Validar spec ==="
nvidia-ctk cdi validate --input-file=/etc/cdi/nvidia.yaml 2>&1 | head -5 || echo "(validate no disponible o passed)"

echo ""
echo "=== TODO OK ==="
