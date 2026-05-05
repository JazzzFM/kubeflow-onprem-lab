#!/bin/bash
set -e
export DEBIAN_FRONTEND=noninteractive

echo "=== 1. Docker desde 24.04 (Docker Desktop interop) ==="
docker version --format 'Client: {{.Client.Version}}  Server: {{.Server.Version}}' 2>&1 | head -2 || echo "  [WARN] docker no responde"

echo ""
echo "=== 2. GPU vista desde host 24.04 (driver Windows) ==="
nvidia-smi 2>&1 | head -15 || { echo "  [INFO] nvidia-smi no instalado en 24.04, solo en 20.04"; ls /usr/lib/wsl/lib/nvidia-smi 2>&1; }

echo ""
echo "=== 3. Repo NVIDIA Container Toolkit ==="
sudo -n install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | sudo -n gpg --dearmor --yes -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -fsSL https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  | sudo -n tee /etc/apt/sources.list.d/nvidia-container-toolkit.list >/dev/null
echo "  [ok] repo configurado"

echo ""
echo "=== 4. apt update (solo el repo nvidia) ==="
sudo -n apt-get update -qq -o Dir::Etc::sourcelist="sources.list.d/nvidia-container-toolkit.list" \
  -o Dir::Etc::sourceparts="-" -o APT::Get::List-Cleanup="0" 2>&1 | tail -5
echo ""
echo "=== 5. Instalar nvidia-container-toolkit ==="
sudo -n apt-get install -y -qq nvidia-container-toolkit 2>&1 | tail -5

echo ""
echo "=== 6. Versiones ==="
nvidia-ctk --version 2>&1 | head -3
echo ""
echo "Componentes:"
dpkg -l 2>/dev/null | grep -E "^ii.*nvidia-container" | awk '{printf "  %-40s %s\n", $2, $3}'

echo ""
echo "=== 7. Detectar dispositivos GPU ==="
nvidia-ctk system list-devices 2>&1 | head -10 || echo "  (ok si no responde, CDI se configura despues)"

echo ""
echo "=== TODO OK ==="
