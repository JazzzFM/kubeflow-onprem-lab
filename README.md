# Kubeflow On-Premise Lab

[![Kubernetes](https://img.shields.io/badge/Kubernetes-k3s%20v1.35-326CE5?logo=kubernetes)](https://k3s.io)
[![Kubeflow](https://img.shields.io/badge/Kubeflow-1.10.2%20%2F%2026.03-1A73E8)](https://kubeflow.org)
[![NVIDIA](https://img.shields.io/badge/NVIDIA-GPU%20Operator-76B900?logo=nvidia)](https://github.com/NVIDIA/gpu-operator)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.11%20CUDA%2013-EE4C2C?logo=pytorch)](https://pytorch.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> Laboratorio de referencia para curso **Kubeflow + MLOps on-premise** con NVIDIA GPU.
> Stack base validado en WSL2 Ubuntu 24.04 con NVIDIA RTX 5080 (Blackwell sm_120).

---

## ¿Qué hay aquí?

Un cluster Kubernetes auto-contenido con GPU passthrough y demos ML/DL listos
para enseñar el camino completo: **Kubernetes → GPU → ML clásico → Deep Learning →
Kubeflow Pipelines**.

```
                    ┌─────────────────────────────────────────────┐
                    │  Windows 11 + RTX 5080 Laptop (16 GB VRAM)  │
                    │ ┌─────────────────────────────────────────┐ │
                    │ │  WSL2 Ubuntu 24.04 (11 GB / 20 cores)   │ │
                    │ │ ┌─────────────────────────────────────┐ │ │
                    │ │ │ k3s v1.35.4  (single-node)          │ │ │
                    │ │ │   ├─ NVIDIA Container Toolkit        │ │ │
                    │ │ │   ├─ NVIDIA GPU Operator (CDI)       │ │ │
                    │ │ │   ├─ RuntimeClass: nvidia            │ │ │
                    │ │ │   └─ Pods con nvidia.com/gpu: 1      │ │ │
                    │ │ └─────────────────────────────────────┘ │ │
                    │ │           │                              │ │
                    │ │           ▼                              │ │
                    │ │  ┌────────────────────────────────────┐  │ │
                    │ │  │ Demos del curso                    │  │ │
                    │ │  │  • GBC (sklearn)  ─── 95.56% acc   │  │ │
                    │ │  │  • CNN (PyTorch)  ─── 98.60% acc   │  │ │
                    │ │  │  • KFP Pipeline (SDK v2 local)     │  │ │
                    │ │  └────────────────────────────────────┘  │ │
                    │ └─────────────────────────────────────────┘ │
                    └─────────────────────────────────────────────┘
                                    ▲
                                    │
                                    │  misma pipeline corre en
                                    ▼
                    ┌─────────────────────────────────────────────┐
                    │  AWS EKS  (módulos avanzados del curso)     │
                    │   3 control plane + node group GPU          │
                    │   Kubeflow 1.10.2 completo                  │
                    └─────────────────────────────────────────────┘
```

## Quickstart

**Pre-requisitos**: WSL2 con Ubuntu 24.04, Docker Desktop, NVIDIA driver en Windows ≥ 580.

```bash
# 1. Setup base (usuario, systemd, paquetes)
sudo bash scripts/01-setup-user-systemd.sh
bash scripts/02-install-runtimes.sh

# 2. NVIDIA Container Toolkit + CDI mode WSL
bash scripts/03-nvidia-toolkit.sh
bash scripts/04-cdi-wsl.sh

# 3. k3s + GPU Operator
bash scripts/05-install-k3s.sh
bash scripts/06-gpu-operator.sh

# 4. Validar GPU en pod
kubectl apply -f manifests/gpu-test-pod.yaml
kubectl logs gpu-test
# Salida: nvidia-smi mostrando RTX 5080 dentro del container

# 5. Demos ML/DL
cd models
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
python 01_gradient_boosting.py     # ML clásico, ~1s
python 02_cnn_pytorch.py           # DL en GPU, ~12s
python 03_kfp_pipeline.py          # Pipeline KFP SDK local
```

## ¿Por qué Kubeflow? Ventajas que enseña este lab

Lee **[docs/why-kubeflow.md](docs/why-kubeflow.md)** para el detalle. Resumen:

- **Reproducibilidad:** componentes con `@dsl.component` → mismo código corre local
  (laptop), staging (k3s) y producción (EKS).
- **Multi-tenancy:** Profiles aíslan equipos sin instalar clusters separados.
- **GPU sharing/MIG:** asignación dinámica de GPU por pod.
- **Tracking:** ML Metadata + ML Pipelines UI registran cada run sin instrumentar
  el código.
- **Ecosistema:** Pipelines + Notebooks + Katib (HPO) + KServe (serving) +
  Training Operator (distribuido) en una sola superficie.

## Resultados del lab (2026-05-05)

| Demo | Framework | Hardware | Accuracy | Tiempo |
|---|---|---|---|---|
| Gradient Boosting | scikit-learn | CPU (Ultra 9 275HX) | **0.9556** | 0.244 s |
| LeNet-5 CNN | PyTorch 2.11 + CUDA 13.0 | **RTX 5080 sm_120** | **0.9860** | 11.73 s |
| KFP Pipeline | KFP SDK v2 + `kfp.local` | mismos componentes orquestados | composite | ~1 min |

Detalle completo en [`docs/results-2026-05-05.md`](docs/results-2026-05-05.md).

## Estructura del repo

```
.
├── README.md                          ← este archivo
├── LICENSE                            ← MIT
├── scripts/         (7 archivos)      ← bootstrap del cluster
│   ├── 01-setup-user-systemd.sh
│   ├── 02-install-runtimes.sh
│   ├── 03-nvidia-toolkit.sh
│   ├── 04-cdi-wsl.sh
│   ├── 05-install-k3s.sh
│   ├── 06-gpu-operator.sh
│   └── 07-fix-mount-rshared.sh
├── manifests/       (2 archivos)      ← YAML de Kubernetes
│   ├── runtime-class-nvidia.yaml
│   └── gpu-test-pod.yaml
├── models/          (3 demos)         ← código del curso
│   ├── 01_gradient_boosting.py
│   ├── 02_cnn_pytorch.py
│   ├── 03_kfp_pipeline.py
│   ├── requirements.txt
│   ├── run-all.sh
│   └── run-kfp.sh
├── docs/            (4 archivos)      ← documentación
│   ├── why-kubeflow.md
│   ├── architecture.md
│   ├── findings.md
│   ├── curso-outline.md
│   └── results-2026-05-05.md
└── memory/          (snapshot)        ← estado proyecto
```

## Hallazgos clave para el curso

Detalle en [`docs/findings.md`](docs/findings.md):

1. `gcr.io/ml-pipeline/` está **deprecated** por Google → manifests v1.9.0 rotos.
2. WSL2 + Istio requiere `mount --make-rshared /` persistido en `/etc/wsl.conf`.
3. NVIDIA Container Toolkit en WSL2 usa **CDI + `/dev/dxg`** (no `/dev/nvidia*`).
4. Device plugin con `DEVICE_LIST_STRATEGY=envvar` evita mismatch de UUID-CDI en WSL.
5. Kubeflow cambió a **versionado calendar-based** (Año.Mes.Parche).

## Roadmap del curso

| Módulo | Tema | Plataforma |
|---|---|---|
| 1-2 | Kubernetes básico + CNI/Networking | Local (k3s) |
| 3-4 | Storage + Ingress | Local |
| 5-6 | GPU + RuntimeClass + CDI | Local |
| 7-9 | KFP SDK v2 + Pipelines + Notebooks | Local + EKS |
| 10-11 | Training Operator + Katib HPO | EKS |
| 12 | KServe + Inference autoscaling | EKS |
| 13-14 | Harbor + skopeo + air-gapped | Local + EKS |
| 15-16 | Auth Dex/OIDC + Observability DCGM | EKS |

## Contribuciones

Issues y PRs bienvenidos. Este repo es la base del curso, así que se actualiza
cada vez que descubrimos algo nuevo en clase.
