# Kubeflow On-Premise Lab

Lab de referencia para curso de Kubeflow + MLOps on-prem con NVIDIA GPU.
**Stack base validado**: WSL2 Ubuntu 24.04 + k3s v1.35.4 + NVIDIA GPU Operator + RTX 5080.

## Estructura

```
.
├── scripts/        # bash scripts para bootstrap del cluster (WSL → k3s → GPU)
├── models/         # demos ML/DL del curso (sklearn, PyTorch, KFP SDK)
├── manifests/      # YAML de Kubernetes (RuntimeClass, pods test, etc.)
├── docs/           # hallazgos, troubleshooting, decisiones arquitectónicas
└── memory/         # estado del proyecto guardado
```

## Demos del curso

| Script | Tipo | Dataset | Accuracy | Tiempo |
|---|---|---|---|---|
| `models/01_gradient_boosting.py` | ML clásico (CPU) | Wine | 0.96 | <1s |
| `models/02_cnn_pytorch.py` | Deep Learning (GPU) | MNIST | ~0.99 | ~30s en RTX 5080 |
| `models/03_kfp_pipeline.py` | KFP SDK v2 (local) | ambos | composite | ~1 min |

## Setup local (WSL2)

```bash
# 1. Instalar dependencias del sistema
sudo bash scripts/01-base-packages.sh

# 2. Setup k3s + GPU
bash scripts/02-install-k3s.sh
bash scripts/03-nvidia-toolkit.sh
bash scripts/04-gpu-operator.sh

# 3. Validar GPU en pod
kubectl apply -f manifests/gpu-test-pod.yaml
kubectl logs gpu-test

# 4. Correr demos
cd models
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
python 01_gradient_boosting.py
python 02_cnn_pytorch.py
python 03_kfp_pipeline.py
```

## Hallazgos clave (mayo 2026)

- `gcr.io/ml-pipeline/` está **deprecated** por Google. Manifests Kubeflow v1.9.0 ya no funcionan out-of-the-box.
- Versión recomendada: **Kubeflow 1.10.2** (LTS) o **26.03** (calendar-based).
- WSL2 con 11 GB RAM **no es viable** para Kubeflow completo. Usar AWS EKS para módulos avanzados.
- En WSL2 hay que aplicar `mount --make-rshared /` en `/etc/wsl.conf` para que webhooks Istio funcionen.

Ver `docs/findings.md` para el detalle completo.

## License

MIT (TBD)
