#!/bin/bash
set -e

echo "=== 1. Eliminar device plugin standalone (conflicto con GPU Operator) ==="
kubectl delete -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.16.2/deployments/static/nvidia-device-plugin.yml --ignore-not-found 2>&1 | tail -3
sleep 3

echo ""
echo "=== 2. Limpiar pod de prueba viejo ==="
kubectl delete pod gpu-test --ignore-not-found --grace-period=0 --force 2>&1 | head -1

echo ""
echo "=== 3. Repo Helm NVIDIA ==="
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia 2>&1 | head -3
helm repo update 2>&1 | tail -3

echo ""
echo "=== 4. Instalar GPU Operator (flags WSL-aware) ==="
helm install gpu-operator nvidia/gpu-operator \
  -n gpu-operator --create-namespace \
  --set driver.enabled=false \
  --set toolkit.enabled=false \
  --set cdi.enabled=true \
  --set cdi.default=false \
  --set operator.runtimeClass=nvidia \
  --set devicePlugin.runtimeClassName=nvidia \
  --set mig.strategy=none \
  --set nfd.enabled=true \
  --wait --timeout=10m 2>&1 | tail -10

echo ""
echo "=== 5. Pods en gpu-operator namespace ==="
kubectl -n gpu-operator get pods 2>&1

echo ""
echo "=== 6. GPU registrada? ==="
sleep 10
kubectl get node -o jsonpath='{range .items[*]}{.metadata.name}: nvidia.com/gpu = {.status.allocatable.nvidia\.com/gpu}{"\n"}{end}'

echo ""
echo "=== TODO OK ==="
