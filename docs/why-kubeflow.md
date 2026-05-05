# ¿Por qué Kubeflow?

Documentación pedagógica para el curso. Las ventajas que justifican adoptar
Kubeflow vs alternativas (scripts standalone, MLflow puro, SageMaker, Vertex AI).

## TL;DR

**Kubeflow es Kubernetes-native ML.** Si tu organización ya corre Kubernetes,
Kubeflow es la forma natural de hacer ML reproducible, multi-tenant, portable
entre clouds y on-premise.

## 1. Reproducibilidad

Cada componente es una imagen Docker + spec declarativa. Mismo código corre:
- En tu laptop (`kfp.local`)
- En staging (k3s en VM)
- En producción (EKS / GKE / AKS / on-prem)

```python
@dsl.component
def train_model(data: Input[Dataset]) -> Output[Model]: ...

@dsl.pipeline(name="prod-training")
def my_pipeline():
    data = ingest()
    model = train_model(data=data.outputs["dataset"])
    deploy(model=model.outputs["model"])
```

Sin Kubeflow tendrías scripts en bash + cron + S3 paths hardcoded. **Kubeflow
te da contratos tipados** (artifacts, metrics, datasets) entre pasos.

## 2. Multi-tenancy real

Equipos distintos pueden usar el mismo cluster sin pisarse:
- **Profiles**: namespaces aislados con cuotas + RBAC
- **Networking policies**: tráfico restringido entre profiles
- **Storage**: PVCs por profile

Sin Kubeflow tendrías que provisar un EKS por equipo. Con Kubeflow, un cluster
sirve a 50 data scientists separados.

## 3. GPU sharing / MIG

Una GPU A100/H100 se puede partir en hasta 7 instancias MIG. Kubeflow + GPU
Operator gestiona la asignación:

```yaml
resources:
  limits:
    nvidia.com/mig-1g.10gb: 1   # solicito 1 instancia MIG de 10 GB
```

Para consumer GPUs (RTX 5080 sin MIG), tienes **time-slicing**:

```yaml
config:
  time-slicing:
    resources:
      - name: nvidia.com/gpu
        replicas: 4   # 4 pods comparten la misma GPU
```

## 4. Tracking automático con ML Metadata

Cada artifact (dataset, modelo, métrica) queda registrado sin código extra:

```python
@dsl.component
def train(data: Input[Dataset]) -> Output[Model]:
    # ... entrenamiento ...
    model.save("/output")
    # KFP automáticamente registra:
    #  - lineage: este Model viene de este Dataset
    #  - producer run: pipeline run-id
    #  - timestamp, user, hash de imagen
```

Equivalente con MLflow puro requiere instrumentación manual con `mlflow.log_*()`.

## 5. Ecosistema integrado

| Componente | Para qué |
|---|---|
| **Pipelines** | Orquestación de workflows ML como DAGs |
| **Notebooks** | JupyterHub multi-tenant con GPU |
| **Katib** | Hyperparameter Optimization (Bayesian, hyperband, etc.) |
| **Training Operator** | PyTorchJob/TFJob para entrenamiento distribuido |
| **KServe** | Serving con autoscale, A/B, canary |
| **Model Registry** | Catálogo de modelos versionados |

Todos hablan entre sí (mismo Kubernetes, misma auth, mismo storage). Sin
Kubeflow tendrías que pegar 6 productos distintos.

## 6. Portabilidad entre clouds y on-prem

| Plataforma | Cómo corre Kubeflow |
|---|---|
| **AWS EKS** | manifests + AWS Load Balancer Controller |
| **GCP GKE** | manifests + GKE managed (también disponible Vertex AI Pipelines basado en KFP) |
| **Azure AKS** | manifests + Azure CNI |
| **On-prem (kubeadm/RKE2)** | manifests + MetalLB + Longhorn |
| **Air-gapped** | Harbor + skopeo mirror |

**Mismo código de pipeline en todos.** Esto es lo que SageMaker / Vertex AI
NO te dan: lock-in al provider.

## 7. Estándares abiertos

- **Pipelines DSL** ahora es estándar de facto (Vertex AI lo adoptó)
- **KServe** = sucesor abierto de SageMaker Endpoints / Vertex Predictions
- **ML Metadata Store** = base de datos común con lineage portable

## ¿Cuándo NO usar Kubeflow?

- Equipo de 2 personas sin infraestructura K8s → MLflow + Airflow es más simple
- Solo necesitas serving (no training) → BentoML, Triton, vLLM standalone
- 100% en AWS sin plan multi-cloud → SageMaker integrado puede ser más rápido

Kubeflow brilla cuando: **>10 personas, K8s ya en uso, multi-cloud o on-prem**.

## Referencias

- [Kubeflow.org](https://www.kubeflow.org/)
- [Kubeflow Pipelines SDK v2](https://www.kubeflow.org/docs/components/pipelines/)
- [Kubeflow vs SageMaker comparison](https://www.kubeflow.org/docs/started/kubeflow-overview/)
- [GPU Operator NVIDIA](https://github.com/NVIDIA/gpu-operator)
