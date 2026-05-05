# Hallazgos del lab — mayo 2026

## 1. gcr.io/ml-pipeline está deprecated

Google retiró el registry `gcr.io/ml-pipeline/` durante 2025. Las imágenes
de Kubeflow Pipelines (frontend, api-server, persistence-agent, etc.) ya
no se pueden pull desde ese path en manifests v1.9.0.

**Verificación:**
```bash
curl -fsS https://gcr.io/v2/ml-pipeline/frontend/tags/list
# {"child":[],"manifest":{},"tags":[]}   ← repo vaciado
```

**Solución para producción on-prem:** Harbor + skopeo mirroring.

## 2. WSL2 + Istio: mount propagation

Pods que usan `mountPropagation: Bidirectional` (cert-manager validators,
Istio sidecar injector) fallan con:
> `path "/" is mounted on "/" but it is not a shared or slave mount`

**Fix persistente** en `/etc/wsl.conf`:
```ini
[boot]
command="mount --make-rshared /"
```

## 3. NVIDIA Container Toolkit modo WSL

CDI spec generada con `--mode=wsl`:
```bash
sudo nvidia-ctk cdi generate --output=/etc/cdi/nvidia.yaml --mode=wsl
```
Mapea `/dev/dxg` y librerías de `/usr/lib/wsl/drivers/...` (no `/dev/nvidia*`
porque el driver vive en Windows host).

## 4. Device plugin con CDI mismatch

El `nvidia-device-plugin` del GPU Operator pide vendor `k8s.device-plugin.nvidia.com/gpu`
pero `nvidia-ctk` en WSL no genera UUID-named devices (solo `name: all`).

**Workaround:** `DEVICE_LIST_STRATEGY=envvar` (vía Helm values al GPU Operator)
para bypassear CDI y usar `NVIDIA_VISIBLE_DEVICES`. Validado funcionando.

## 5. Versionado Kubeflow 2026

Kubeflow cambió a versionado **calendar-based** (Año.Mes.Parche):

| Versión | Fecha | Estado |
|---|---|---|
| 26.03 | mar 2026 | Latest stable |
| v1.11.0 | dic 2025 | Estable |
| v1.10.2 | jul 2025 | LTS |
| v1.9.0 | 2024 | Roto (gcr.io retirado) |

## 6. Recursos para Kubeflow Lite

WSL2 con 11 GB RAM no es viable para Kubeflow completo (control plane pide
~16 GB). Para lab on-prem real, mínimo 32 GB RAM (laptop) o 64 GB (server).

Estrategia: **local para conceptos K8s + GPU, AWS EKS para Kubeflow real**.
