---
name: Kubeflow lab — estado de migración Ubuntu 20.04 → 24.04 (pausada en paso 10, GPU Operator ~90% productivo)
description: Migración WSL Ubuntu 20.04 → 24.04 con k3s + GPU Operator. Pausada el 2026-05-04 ~17:50 CST. Sistema 90% productivo, falta estabilizar device plugin health-check para WSL2.
type: project
originSessionId: 402ad9a2-dc48-42d6-8f33-db8503dad54a
---
Estado de la migración WSL para el lab de Kubeflow, **pausada el 2026-05-04 ~17:50 CST** para reinicio de PC.

## ✅ Lo que ESTÁ funcionando (probado)

- **Ubuntu-24.04 lado a lado**, default user `jazielflo` UID 1000, systemd PID 1, sudo NOPASSWD
- **Ubuntu-20.04 intacta** y default por ahora (asterisco en `wsl --list -v`). Backup en `C:\Users\Jaziel Flores\Desktop\wsl-backup-2026-05-04.tar.gz` (17 GB)
- **APT IPv4 forzado** en 24.04 (`/etc/apt/apt.conf.d/99force-ipv4`)
- **Configs migradas** a 24.04: .ssh (verificado SSH a github funciona), .gitconfig, .zshrc + oh-my-zsh + p10k, .config, .claude, .kube, .docker, .codex, .gemini, .qwen. Symlinks .aws/.azure → /mnt/c/Users/Jaziel Flores/.aws|.azure recreados. Home en 24.04 = 1.4 GB
- **Shell de jazielflo = /usr/bin/zsh** (`chsh -s` aplicado). `.zshenv` arreglado con guard defensivo para .cargo/env
- **Stack runtimes**: pipx 1.4.3, gh 2.92.0, kubectl v1.31.14 (apt), uv 0.11.8 (~/.local/bin), helm v3.20.2, Node v24.15.0 (vía nvm en ~/.nvm)
- **NVIDIA Container Toolkit 1.19.0** + libnvidia-container-tools + nvidia-container-runtime (en /usr/bin)
- **CDI spec generada en modo WSL** en `/etc/cdi/nvidia.yaml` (apunta a /dev/dxg + /usr/lib/wsl/drivers/...)
- **k3s v1.35.4+k3s1** instalado vía systemd, sin traefik ni servicelb. Auto-detecta nvidia-container-runtime
- **Mount propagation FIX**: `mount --make-rshared /` aplicado y persistido en `/etc/wsl.conf` con `[boot] command="mount --make-rshared / && systemctl restart k3s 2>/dev/null || true"` — crítico WSL2 fix
- **GPU Operator v26.3.1 instalado** con flags WSL: driver.enabled=false, toolkit.enabled=false, cdi.enabled=true, operator.runtimeClass=nvidia, devicePlugin.runtimeClassName=nvidia, mig.strategy=none. Pods en namespace `gpu-operator` Running: gpu-feature-discovery, NFD master/worker/gc, nvidia-dcgm-exporter, nvidia-device-plugin-daemonset, gpu-operator
- **Labels nodo**: nvidia.com/gpu.present=true, feature.node.kubernetes.io/pci-10de.present=true, nvidia.com/gpu.compute.major=12 (Blackwell sm_120), nvidia.com/gpu.count=1
- **GPU registrada**: `kubectl get node msi -o jsonpath='{.status.allocatable.nvidia\.com/gpu}'` = 1
- **`nvidia-cuda-validator: Completed`** ← GPU Operator levantó pod, asignó GPU, ejecutó CUDA, terminó OK. PRUEBA REAL de que el sistema funciona.

## 🟡 Lo PENDIENTE (próxima sesión)

**Issue**: Pods custom con `nvidia.com/gpu: 1` fallan con `Allocate failed: no healthy devices present` — el device plugin del GPU Operator marca la GPU unhealthy en su loop de health-check para WSL2. El `nvidia-cuda-validator` interno SÍ pasa, pero pods user no.

**Fix planeado para próxima sesión** (1 comando, ~5-10 min):
```bash
helm upgrade gpu-operator nvidia/gpu-operator \
  -n gpu-operator \
  --reuse-values \
  --set devicePlugin.env[0].name=FAIL_ON_INIT_ERROR \
  --set devicePlugin.env[0].value="false" \
  --set devicePlugin.env[1].name=DEVICE_LIST_STRATEGY \
  --set devicePlugin.env[1].value="cdi-annotations" \
  --set devicePlugin.env[2].name=PASS_DEVICE_SPECS \
  --set devicePlugin.env[2].value="true"
```

Después validar con pod test:
```yaml
apiVersion: v1
kind: Pod
metadata: { name: gpu-test }
spec:
  runtimeClassName: nvidia
  restartPolicy: Never
  containers:
  - name: cuda
    image: nvcr.io/nvidia/cuda:13.0.0-base-ubuntu24.04
    command: ["nvidia-smi"]
    resources: { limits: { nvidia.com/gpu: 1 } }
```

## ⏭ Pasos siguientes después de estabilizar GPU

1. **Paso 10b** (5 min) — helm upgrade con env flags WSL, validar pod gpu-test corre `nvidia-smi` OK
2. **Paso 11** (15-30 min) — Kubeflow lite via manifests: Notebooks + Pipelines + Training Operator + Central Dashboard. Saltar Katib/KServe/Model Registry para empezar
3. **Paso 12** — Argo CD para GitOps (módulo 9 del curso)
4. **Paso 13** — Hardening: cert-manager, Dex con Keycloak, NetworkPolicies, ResourceQuotas
5. **Paso 14** — Cuando llegue módulo multi-nodo: Terraform en AWS con créditos corporativos

## Cluster k3s APAGADO manualmente (2026-05-04 ~17:55 CST)

El usuario pidió apagar el cluster para liberar recursos antes de reiniciar la PC. Estado:
- `systemctl stop k3s` ejecutado → inactive
- **`systemctl disable k3s`** ejecutado → NO arrancará automáticamente al boot
- `[boot] command` en `/etc/wsl.conf` modificado a SOLO `mount --make-rshared /` (ya no reinicia k3s)
- `wsl --terminate Ubuntu-24.04` ejecutado → VM apagada, RAM devuelta a Windows

## Tras reinicio de PC — para retomar

Para volver a levantar el cluster:
```powershell
# Desde Windows
wsl -d Ubuntu-24.04
# Dentro de la 24.04:
sudo systemctl enable --now k3s
# Esperar 30s, luego:
kubectl get nodes
kubectl -n gpu-operator get pods
```

GPU Operator pods se levantan solos cuando k3s arranca (ya están en etcd). NO hay que reinstalar nada.

Para validar GPU registrada tras boot:
```bash
kubectl get node -o jsonpath='{.items[*].status.allocatable.nvidia\.com/gpu}{"\n"}'
# Debe mostrar 1
```

## Archivos importantes en /mnt/c/temp/ (todos persisten)

- setup-2404.sh, install-base-2404.sh, install-base-2404-v2.sh, fix-install-2404.sh, copy-configs-2404.sh, extract-configs-2404.sh, fix-zshenv.sh
- install-runtimes-2404.sh, install-nvidia-toolkit-2404.sh, gen-cdi-wsl.sh
- install-k3s-2404.sh, finish-k3s-v2.sh, recover-k3s.sh
- install-gpu-operator.sh, fix-nfd-wsl.sh, fix-mount-prop.sh
- check-*.sh, diag-*.sh varios para troubleshooting

## Hallazgos para el curso (oro pedagógico nuevo)

- **WSL2 + Kubernetes mount propagation**: rootfs `/` por defecto es `private`. Pods con HostPath y Bidirectional propagation fallan con "path / is mounted on / but it is not a shared or slave mount". Fix: `mount --make-rshared /` + persistir en `[boot] command` de wsl.conf. Material crítico de troubleshooting.
- **Device plugin standalone vs GPU Operator**: en WSL2 el plugin standalone tiene health check problemático. GPU Operator es lo correcto pero requiere flags `--mode=wsl` en CDI y env vars específicos en device plugin para evitar race conditions.
- **K3s v1.35 detecta automáticamente nvidia-container-runtime** si está en PATH (visible en logs: "Found nvidia container runtime at /usr/bin/nvidia-container-runtime"). NO se debe sobrescribir el config.toml.tmpl manualmente — eso rompe k3s.
- **Pods fantasma en kubelet**: tras restarts, kubectl puede mostrar pods Running que en realidad no existen en runtime. Síntoma: `kubectl logs/exec` falla con "pod does not exist" aunque `get pods` los muestra. Solución: force delete del pod, dejar que el DS recree.
- **K3s 9 RuntimeClass por defecto**: nvidia, nvidia-experimental, crun, lunatic, slight, spin, wasmedge, wasmer, wasmtime, wws. K3s viene "Wasm-ready" out of the box.
- **NFD en WSL2**: no detecta GPU automáticamente porque busca dispositivos PCI nvidia que no existen (vive en /dev/dxg). Solución: etiquetar nodo manualmente con `nvidia.com/gpu.present=true`.
