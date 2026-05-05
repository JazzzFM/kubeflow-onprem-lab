#!/bin/bash
set -e

echo "=== Setup base de Ubuntu-24.04 ==="

# 1. Crear usuario jazielflo con UID 1000
useradd -m -u 1000 -s /bin/bash -G sudo,adm jazielflo
echo "  [ok] usuario jazielflo creado con UID 1000"

# 2. Sudo sin password
SUDOERS_LINE='jazielflo ALL=(ALL) NOPASSWD:ALL'
echo "$SUDOERS_LINE" > /etc/sudoers.d/jazielflo
chmod 0440 /etc/sudoers.d/jazielflo
echo "  [ok] sudoers configurado"

# 3. /etc/wsl.conf con usuario default + systemd
cat > /etc/wsl.conf <<WSLCONF
[user]
default=jazielflo

[boot]
systemd=true

[network]
generateHosts=true
generateResolvConf=true

[interop]
enabled=true
appendWindowsPath=true
WSLCONF
echo "  [ok] /etc/wsl.conf escrito"

echo ""
echo "=== Validacion ==="
id jazielflo
echo ""
cat /etc/wsl.conf
echo ""
echo "=== OS ==="
grep -E "^(NAME|VERSION_ID|VERSION_CODENAME)=" /etc/os-release
