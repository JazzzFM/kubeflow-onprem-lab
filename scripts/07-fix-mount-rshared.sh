#!/bin/bash
echo "=== 1. Estado actual del mount / ==="
findmnt -o TARGET,PROPAGATION / 2>&1

echo ""
echo "=== 2. Hacer / shared (mount propagation) ==="
sudo -n mount --make-rshared /
findmnt -o TARGET,PROPAGATION / 2>&1

echo ""
echo "=== 3. Persistir en /etc/wsl.conf ==="
if ! grep -q "make-rshared" /etc/wsl.conf 2>/dev/null; then
  sudo -n tee -a /etc/wsl.conf >/dev/null <<'WSLCONF'

[boot]
command="mount --make-rshared / && systemctl restart k3s 2>/dev/null || true"
WSLCONF
  echo "  [ok] agregado a wsl.conf"
else
  echo "  [skip] ya existe en wsl.conf"
fi
sudo -n grep -A2 boot /etc/wsl.conf

echo ""
echo "=== 4. Force delete pods atascados (validator + dependientes) ==="
kubectl -n gpu-operator delete pod \
  -l app=nvidia-operator-validator \
  --force --grace-period=0 2>&1 | head -3
kubectl -n gpu-operator delete pod \
  -l app=gpu-feature-discovery \
  --force --grace-period=0 2>&1 | head -3
kubectl -n gpu-operator delete pod \
  -l app=nvidia-device-plugin-daemonset \
  --force --grace-period=0 2>&1 | head -3
kubectl -n gpu-operator delete pod \
  -l app=nvidia-dcgm-exporter \
  --force --grace-period=0 2>&1 | head -3

echo ""
echo "=== 5. Esperar pods Running (max 4 min) ==="
for i in $(seq 1 60); do
  count=$(kubectl -n gpu-operator get pods --no-headers 2>/dev/null | wc -l)
  ready=$(kubectl -n gpu-operator get pods --no-headers 2>/dev/null | awk '{print $3}' | grep -cE 'Running|Completed' || echo 0)
  if [ $((i % 5)) -eq 0 ]; then
    echo "  [$((i*4))s] pods=$count, in_running_or_completed=$ready"
  fi
  if [ "$count" -ge 5 ] && [ "$ready" -ge "$count" ]; then
    echo "  [ok] todos los pods listos"
    break
  fi
  sleep 4
done

echo ""
echo "=== 6. Estado final ==="
kubectl -n gpu-operator get pods 2>&1
echo ""
echo "=== 7. GPU registrada? ==="
kubectl get node -o jsonpath='{range .items[*]}{.metadata.name}: nvidia.com/gpu = {.status.allocatable.nvidia\.com/gpu}{"\n"}{end}'
