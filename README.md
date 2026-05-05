# Kubeflow MLOps Lab — On-Premise

[![Kubernetes](https://img.shields.io/badge/Kubernetes-k3s%20v1.35-326CE5?logo=kubernetes)](https://k3s.io)
[![Kubeflow](https://img.shields.io/badge/Kubeflow-1.10.2%20%2F%2026.03-1A73E8)](https://kubeflow.org)
[![NVIDIA](https://img.shields.io/badge/NVIDIA-GPU%20Operator-76B900?logo=nvidia)](https://github.com/NVIDIA/gpu-operator)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.11%20CUDA%2013-EE4C2C?logo=pytorch)](https://pytorch.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> Lab de referencia para curso **MLOps con Kubeflow on-premise**.
> Asumimos conocimiento previo de ML/DL — el foco es **operacionalizar modelos en producción**:
> reproducibilidad, multi-tenancy, GPU sharing, CI/CD, deployment, observability.

---

## ¿Qué problema resuelve este curso?

```mermaid
flowchart LR
    DS[Data Scientist<br/>Notebook ad-hoc]
    PROD[Producción<br/>Latencia, escala, governance]

    DS -->|"manual scripts<br/>imágenes diferentes<br/>data drift<br/>sin lineage"| GAP[GAP de MLOps]
    GAP -->|"Kubeflow"| PROD

    style GAP fill:#ffcccc,stroke:#cc0000
    style DS fill:#cce5ff
    style PROD fill:#ccffcc
```

El **gap** entre un notebook que "funciona en mi máquina" y un servicio de inferencia
que aguanta 10k req/s con SLOs es **MLOps**. Kubeflow es la implementación
**Kubernetes-native** de ese pipeline completo.

## Stack del lab

```mermaid
flowchart TB
    subgraph WIN["Windows 11 Host (RTX 5080 16GB)"]
        DRV["NVIDIA Driver 591.44<br/>CUDA 13.1"]
        DXG["/dev/dxg<br/>(paravirtual)"]
    end

    subgraph WSL["WSL2 Ubuntu 24.04 + systemd"]
        subgraph K3S["k3s v1.35.4 (single-node)"]
            CTR["containerd<br/>+ nvidia-container-runtime"]
            CDI["/etc/cdi/nvidia.yaml"]
            GPUOP["GPU Operator<br/>(device plugin, DCGM, GFD)"]
            RT["RuntimeClass: nvidia"]
        end

        subgraph KF["Kubeflow Lite (módulos 7-12)"]
            KFP["Pipelines (KFP SDK v2)"]
            JUP["Notebooks"]
            TRO["Training Operator"]
            CD["Central Dashboard"]
        end

        K3S -.-> KF
    end

    subgraph EKS["AWS EKS (módulos 10-16)"]
        FULL["Kubeflow 1.10.2 completo<br/>+ KServe + Katib + Multi-tenant"]
    end

    DRV -.-> DXG
    DXG -.-> CTR
    CDI -.-> CTR
    CTR -.-> RT
    KF -. "misma pipeline<br/>kfp.Client(host=...)" .-> EKS

    classDef cloud fill:#e6f3ff,stroke:#0066cc
    classDef gpu fill:#e6ffe6,stroke:#009900
    class WIN,DRV,DXG gpu
    class EKS,FULL cloud
```

## ¿Qué cubre este lab?

| Capa MLOps | Componente Kubeflow | En este repo |
|---|---|---|
| **Compute** (Kubernetes + GPU) | k3s + GPU Operator | ✅ scripts/ + manifests/ |
| **Pipeline orchestration** | Kubeflow Pipelines (KFP) | ✅ models/03_kfp_pipeline.py |
| **Notebooks multi-tenant** | JupyterHub / Notebook Controller | ⏭ módulo 5 (EKS) |
| **Hyperparameter tuning** | Katib | ⏭ módulo 8 (EKS) |
| **Distributed training** | Training Operator (PyTorchJob, TFJob) | ⏭ módulo 9 (EKS) |
| **Model serving** | KServe | ⏭ módulo 10 (EKS) |
| **Lineage & metadata** | ML Metadata Store | ⏭ con KFP |
| **CI/CD declarativo** | Argo CD + Argo Workflows | ⏭ módulo 12 |
| **Observability** | DCGM exporter + Prometheus | ⏭ módulo 11 |

## Ciclo MLOps que enseñamos

```mermaid
flowchart LR
    A[Data] --> B[Notebook<br/>experimentación]
    B --> C[Pipeline<br/>train + eval]
    C --> D{Métrica<br/>OK?}
    D -- "no" --> B
    D -- "sí" --> E[Model<br/>Registry]
    E --> F[KServe<br/>deployment]
    F --> G[Monitoring<br/>+ drift]
    G -.-> A

    style A fill:#fff5d6
    style B fill:#cce5ff
    style C fill:#cce5ff
    style E fill:#d6f5d6
    style F fill:#d6f5d6
    style G fill:#ffe0cc
```

Este es el ciclo **completo** del curso. Cada flecha es un módulo.

## Quickstart

**Pre-requisitos:** WSL2 con Ubuntu 24.04, Docker Desktop, NVIDIA driver Windows ≥ 580.

```bash
# 1. Bootstrap del cluster local
sudo bash scripts/01-setup-user-systemd.sh
bash scripts/02-install-runtimes.sh
bash scripts/03-nvidia-toolkit.sh
bash scripts/04-cdi-wsl.sh
bash scripts/05-install-k3s.sh
bash scripts/06-gpu-operator.sh

# 2. Validar GPU passthrough en pod
kubectl apply -f manifests/gpu-test-pod.yaml
kubectl logs gpu-test
# → nvidia-smi mostrando RTX 5080 dentro del container

# 3. Demos del curso (ya con resultados validados)
cd models
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
python -m ensurepip   # KFP local lo necesita
python 03_kfp_pipeline.py   # ML clásico + DL + KFP DAG en uno
```

Ver [`docs/01-getting-started.md`](docs/01-getting-started.md) para el tutorial completo.

## Resultados validados (2026-05-05)

| Componente | Métrica | Tiempo |
|---|---|---|
| GBC (sklearn, CPU) | accuracy 0.9556 | 0.24 s |
| LeNet-5 (PyTorch + RTX 5080) | accuracy 0.9860 | 11.7 s (cold) / 4.7 s (warm) |
| Pipeline KFP (3 componentes en DAG) | status SUCCESS | ~5 s overhead |

Detalle en [`docs/results-2026-05-05.md`](docs/results-2026-05-05.md).

## Documentación

| Archivo | Para qué |
|---|---|
| [`00-curso-outline.md`](docs/00-curso-outline.md) | 16 módulos del curso, qué se enseña dónde |
| [`01-getting-started.md`](docs/01-getting-started.md) | Tutorial paso a paso, ~30 min al primer pipeline |
| [`02-mlops-with-kubeflow.md`](docs/02-mlops-with-kubeflow.md) | Qué es MLOps, ciclo de vida, dónde encaja Kubeflow |
| [`03-architecture.md`](docs/03-architecture.md) | Stack vertical, flujo de petición GPU |
| [`04-pipeline-patterns.md`](docs/04-pipeline-patterns.md) | 5 patrones MLOps reales con código |
| [`05-comparison.md`](docs/05-comparison.md) | Kubeflow vs SageMaker MLOps / Vertex AI / MLflow+Airflow |
| [`06-glossary.md`](docs/06-glossary.md) | Términos clave del ecosistema |
| [`findings.md`](docs/findings.md) | Hallazgos: gcr.io deprecation, mount-rshared, CDI WSL |
| [`results-2026-05-05.md`](docs/results-2026-05-05.md) | Resultados del lab con números reales |

## Estructura del repo

```
.
├── README.md                    ← este archivo
├── LICENSE                      ← MIT
├── scripts/                     ← bootstrap del cluster (7 archivos)
├── manifests/                   ← YAML de Kubernetes
├── models/                      ← demos del curso (GBC + CNN + KFP pipeline)
├── docs/                        ← documentación pedagógica (9 archivos)
└── memory/                      ← snapshot del estado del proyecto
```

## Asumimos que ya sabes

Este lab es para audiencia **MLOps / Platform / DevOps**. No enseñamos:
- Cómo funciona gradient descent o backpropagation
- Cómo elegir hiperparámetros desde principios
- Estadística inferencial

Sí enseñamos:
- Cómo empaquetar tu modelo como componente reproducible
- Cómo orquestar entrenamientos en Kubernetes
- Cómo servir el modelo con autoscaling
- Cómo monitorear drift y latencia
- Cómo hacer CI/CD declarativo de pipelines ML

Si necesitas el repaso de ML, lee [docs/02-mlops-with-kubeflow.md → "ML refresher en 2 minutos"](docs/02-mlops-with-kubeflow.md#ml-refresher-en-2-minutos).
