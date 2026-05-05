#!/bin/bash
set -e
export DEBIAN_FRONTEND=noninteractive

echo "=== 1/6 pipx via apt ==="
sudo -n apt-get install -y -qq pipx 2>&1 | tail -3
pipx --version

echo ""
echo "=== 2/6 GitHub CLI (gh) via repo oficial ==="
sudo -n install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
  | sudo -n tee /etc/apt/keyrings/githubcli-archive-keyring.gpg >/dev/null
sudo -n chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
  | sudo -n tee /etc/apt/sources.list.d/github-cli.list >/dev/null
sudo -n apt-get update -qq 2>&1 | tail -3
sudo -n apt-get install -y -qq gh 2>&1 | tail -3
gh --version | head -1

echo ""
echo "=== 3/6 kubectl via repo oficial Kubernetes 1.31 ==="
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.31/deb/Release.key \
  | sudo -n gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg --yes
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.31/deb/ /' \
  | sudo -n tee /etc/apt/sources.list.d/kubernetes.list >/dev/null
sudo -n apt-get update -qq 2>&1 | tail -3
sudo -n apt-get install -y -qq kubectl 2>&1 | tail -3
kubectl version --client | head -1

echo ""
echo "=== 4/6 uv (Python package manager) ==="
curl -LsSf https://astral.sh/uv/install.sh | sh 2>&1 | tail -5
~/.local/bin/uv --version

echo ""
echo "=== 5/6 helm (script oficial) ==="
curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 -o /tmp/get-helm.sh
chmod +x /tmp/get-helm.sh
sudo -n /tmp/get-helm.sh 2>&1 | tail -3
helm version --short

echo ""
echo "=== 6/6 nvm + Node LTS ==="
curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh -o /tmp/install-nvm.sh
bash /tmp/install-nvm.sh 2>&1 | tail -3
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm install --lts 2>&1 | tail -3
nvm alias default 'lts/*'
nvm use default 2>&1 | tail -1
node --version
npm --version

echo ""
echo "=== RESUMEN ==="
for cmd in pipx gh kubectl uv helm node npm nvm; do
  if command -v "$cmd" >/dev/null 2>&1; then
    v=$($cmd --version 2>&1 | head -1)
    echo "  [ok] $cmd: $v"
  elif [ "$cmd" = "nvm" ] && [ -s "$HOME/.nvm/nvm.sh" ]; then
    echo "  [ok] nvm: instalado en ~/.nvm"
  else
    echo "  [MISSING] $cmd"
  fi
done
echo ""
echo "=== TODO OK ==="
