#!/bin/bash
set -e

echo "=== 1. Instalar k3s (sin traefik, sin servicelb por ahora) ==="
curl -sfL https://get.k3s.io | sudo -n \
  INSTALL_K3S_EXEC="--disable=traefik --disable=servicelb --write-kubeconfig-mode=644" \
  sh - 2>&1 | tail -8

echo ""
echo "=== 2. Esperar a que k3s arranque (max 60s) ==="
for i in $(seq 1 30); do
  if sudo -n /usr/local/bin/kubectl get nodes 2>/dev/null | grep -q Ready; then
    echo "  [ok] k3s Ready en ~$((i*2))s"
    break
  fi
  sleep 2
done

echo ""
echo "=== 3. Estado del cluster ==="
sudo -n /usr/local/bin/kubectl get nodes -o wide 2>&1
sudo -n /usr/local/bin/kubectl get pods -A 2>&1 | head -10

echo ""
echo "=== 4. Configurar kubeconfig para jazielflo ==="
mkdir -p $HOME/.kube
sudo -n cp /etc/rancher/k3s/k3s.yaml $HOME/.kube/config
sudo -n chown $(id -u):$(id -g) $HOME/.kube/config
chmod 600 $HOME/.kube/config
kubectl get nodes 2>&1

echo ""
echo "=== 5. Configurar runtime nvidia en containerd de k3s ==="
sudo -n mkdir -p /var/lib/rancher/k3s/agent/etc/containerd
sudo -n tee /var/lib/rancher/k3s/agent/etc/containerd/config.toml.tmpl >/dev/null <<'TOML'
{{ template "base" . }}

[plugins."io.containerd.grpc.v1.cri".containerd]
  default_runtime_name = "nvidia"

[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.nvidia]
  runtime_type = "io.containerd.runc.v2"

[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.nvidia.options]
  BinaryName = "/usr/bin/nvidia-container-runtime"
  SystemdCgroup = true
TOML
echo "  [ok] config.toml.tmpl escrito"

echo ""
echo "=== 6. Reiniciar k3s para aplicar el template ==="
sudo -n systemctl restart k3s
sleep 5
for i in $(seq 1 20); do
  if kubectl get nodes 2>/dev/null | grep -q Ready; then
    echo "  [ok] k3s Ready tras reinicio"
    break
  fi
  sleep 2
done

echo ""
echo "=== 7. Instalar NVIDIA device plugin (CDI mode) ==="
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.16.2/deployments/static/nvidia-device-plugin.yml 2>&1 | tail -5

echo ""
echo "=== 8. Esperar a que device plugin este Running (max 60s) ==="
for i in $(seq 1 30); do
  status=$(kubectl -n kube-system get pods -l name=nvidia-device-plugin-ds -o jsonpath='{.items[0].status.phase}' 2>/dev/null)
  if [ "$status" = "Running" ]; then
    echo "  [ok] device plugin Running"
    break
  fi
  sleep 2
done

echo ""
echo "=== 9. Verificar GPU registrada en nodes ==="
kubectl describe node | grep -A2 "Capacity\|Allocatable" | head -20
echo ""
kubectl get node -o jsonpath='{range .items[*]}{.status.allocatable.nvidia\.com/gpu}{"\n"}{end}'

echo ""
echo "=== TODO OK ==="
