# MLOps con Kubeflow

Este documento explica **qué es MLOps**, qué problemas resuelve, y por qué
Kubeflow es la implementación Kubernetes-native de referencia. **No teoría ML**.

## ML refresher en 2 minutos

Para los que vienen de DevOps/Platform sin background ML:

```mermaid
flowchart LR
    A[Datos] --> B[Modelo<br/>train]
    B --> C[Modelo<br/>predict]
    C --> D[Decisión<br/>de negocio]

    style A fill:#fff5d6
    style B fill:#cce5ff
    style C fill:#d6f5d6
    style D fill:#ffe0cc
```

- **Train** = aprender de datos históricos (proceso pesado, GPU, horas/días)
- **Inference (predict)** = usar el modelo aprendido para nuevas predicciones (rápido, ms)
- **Métricas** = números que miden qué tan bueno es (accuracy, F1, RMSE, etc.)
- **Drift** = los datos cambian con el tiempo, el modelo deja de servir → reentrenar

Eso es todo lo que necesitas para empezar el curso.

## ¿Qué es MLOps?

**MLOps = DevOps aplicado a sistemas de Machine Learning.** Pero ML tiene
características que DevOps tradicional no maneja bien:

```mermaid
flowchart TB
    subgraph DEVOPS["DevOps tradicional"]
        D1[Código → CI → Tests → Deploy]
        D2[Artifacts: imágenes Docker]
        D3[Monitoring: latencia, errores]
    end

    subgraph MLOPS["MLOps suma"]
        M1[Datos → Pipeline → Train → Eval → Register → Deploy]
        M2[Artifacts: datos + modelo + métricas + lineage]
        M3[Monitoring: + data drift + model drift + métrica de negocio]
        M4[Reproducibilidad: misma pipeline + mismos datos = mismo modelo]
        M5[Multi-tenancy: 50 data scientists, 1 cluster]
    end

    DEVOPS -.->|"añade"| MLOPS

    style DEVOPS fill:#cce5ff
    style MLOPS fill:#d6f5d6
```

## El gap que resuelve Kubeflow

Sin Kubeflow, el flujo típico de una empresa con ML:

```mermaid
flowchart LR
    A[Notebook<br/>local] -->|"copy/paste<br/>al server"| B[Script<br/>cron]
    B -->|"S3 manual"| C[Modelo<br/>en producción]
    C -->|"alertas que<br/>nadie ve"| D[Drift<br/>silencioso]

    style A fill:#cce5ff
    style B fill:#ffe0cc
    style C fill:#ffcccc
    style D fill:#ff6666
```

Problemas:
- **Reproducibilidad**: ¿qué versión de datos? ¿qué semilla random?
- **Lineage**: ¿este modelo sirvió cuál cliente? ¿qué dataset entrenó?
- **Multi-tenancy**: 10 data scientists pisándose la GPU
- **Deployment**: ¿cómo escalo? ¿cómo hago canary?
- **Drift**: ¿el modelo sigue siendo bueno? ¿cuándo reentreno?

Con Kubeflow:

```mermaid
flowchart LR
    subgraph KF["Kubeflow"]
        N[Notebook<br/>profile aislado]
        N -->|"@dsl.component"| P[Pipeline<br/>versionada en Git]
        P -->|"executes"| T[Training<br/>distribuido]
        T -->|"métricas + lineage<br/>auto-trackeado"| R[Model<br/>Registry]
        R -->|"KServe<br/>declarativo"| S[Serving<br/>autoscale + canary]
        S -.->|"DCGM + Prometheus"| M[Monitoring<br/>+ drift detection]
        M -.->|"trigger retrain"| P
    end

    style N fill:#cce5ff
    style P fill:#cce5ff
    style T fill:#cce5ff
    style R fill:#d6f5d6
    style S fill:#d6f5d6
    style M fill:#ffe0cc
```

## Las 7 ventajas que enseñamos en el curso

### 1. Reproducibilidad por contrato

Cada componente declara sus inputs/outputs como tipos:

```python
@dsl.component
def train(
    dataset: Input[Dataset],     # input artifact
    epochs: int = 10,             # parámetro
) -> NamedTuple("Result", [
    ("model", Output[Model]),     # output artifact
    ("accuracy", float),          # métrica
]): ...
```

Esto es **un contrato versionable en Git**. Mismo input → mismo output.

### 2. Lineage automático con ML Metadata

```mermaid
flowchart LR
    D1[Dataset v1] --> T1[train run 42]
    T1 --> M1[Model v3]
    M1 --> S1[Serving deployment]
    S1 -.->|"sirvió<br/>requests x→y"| L1[(MLMD)]

    classDef artifact fill:#fff5d6
    classDef process fill:#cce5ff
    class D1,M1 artifact
    class T1,S1 process
```

Sin escribir código de tracking, ML Metadata Store registra:
- De qué dataset salió este modelo
- Quién lo entrenó (qué pipeline run)
- Qué versiones de imagen se usaron
- Qué requests sirvió en producción

Equivalente con MLflow puro requiere instrumentación manual.

### 3. Multi-tenancy con Profiles

```mermaid
flowchart TB
    CL["Cluster Kubeflow"]
    CL --> P1["Profile: equipo-fraude<br/>namespace + RBAC + quotas"]
    CL --> P2["Profile: equipo-recom<br/>namespace + RBAC + quotas"]
    CL --> P3["Profile: equipo-vision<br/>namespace + RBAC + quotas + GPU"]

    P1 -.-> N1[Notebooks personales]
    P1 -.-> KF1[Pipelines del equipo]
    P3 -.-> G3["GPU MIG slice 10GB"]

    style CL fill:#cce5ff
```

50 data scientists, 1 cluster, aislados. Sin Kubeflow tendrías 50 EKS o
1 caos compartido.

### 4. GPU sharing

GPUs caras → necesitas compartirlas. Kubeflow + GPU Operator soporta:

| Estrategia | Cuándo | Compatible con |
|---|---|---|
| **MIG** (Multi-Instance GPU) | Producción, 1 GPU → 7 slices | A100, H100, A30 |
| **Time-slicing** | Dev, varias replicas comparten 1 GPU | Cualquier GPU |
| **GPU exclusive** | Training pesado | Default, 1 pod = 1 GPU |

Tu lab con RTX 5080 (sin MIG) usa time-slicing para múltiples notebooks.

### 5. KServe — serving production-grade

Sin Kubeflow:
```bash
# Tu colega: "deployar el modelo"
docker build → push registry → write deploy.yaml →
write service.yaml → write hpa.yaml → write ingress.yaml →
write monitoring → escalar manual
```

Con KServe:
```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: lenet-mnist
spec:
  predictor:
    pytorch:
      storageUri: s3://models/lenet-v3
    minReplicas: 1
    maxReplicas: 100
    canaryTrafficPercent: 10
```

Eso es todo. KServe maneja: autoscale (scale-to-zero), canary, A/B,
HTTP+gRPC endpoint, batching, transformers pre/post.

### 6. Pipelines portables entre clouds y on-prem

```mermaid
flowchart LR
    PIPE[Tu pipeline.py]
    PIPE -->|"kfp.local"| L[laptop]
    PIPE -->|"kfp.Client(EKS)"| E[AWS EKS]
    PIPE -->|"kfp.Client(GKE)"| G[GCP GKE]
    PIPE -->|"kfp.Client(AKS)"| A[Azure AKS]
    PIPE -->|"kfp.Client(on-prem)"| O[k3s on-prem]

    style PIPE fill:#d6f5d6
```

**Mismo código** en todos. Esto es lo que SageMaker / Vertex AI **no te dan**:
no hay lock-in.

### 7. Estándares abiertos

- **KFP DSL v2** = estándar de facto (Vertex AI Pipelines lo adoptó como SDK)
- **KServe** = sucesor de SageMaker Endpoints / Vertex Predictions
- **ML Metadata Store** = lineage portable entre orquestadores

## ¿Cuándo NO usar Kubeflow?

Honestidad para el curso:

| Situación | Mejor alternativa |
|---|---|
| Equipo de 2 personas, sin K8s | MLflow + Airflow + scripts |
| Solo serving (no training pipelines) | BentoML, Triton, vLLM standalone |
| 100% AWS, sin plan multi-cloud | SageMaker Pipelines (más rápido onboarding) |
| Equipo sin DevOps culture | Databricks ML / Vertex AI managed |

**Kubeflow brilla cuando**: 10+ personas, K8s ya en uso, multi-cloud o on-prem,
o requirement de soberanía de datos.

## Lectura recomendada

- [Designing MLOps Systems](https://www.oreilly.com/library/view/designing-machine-learning/9781098115777/) — Chip Huyen
- [ML Engineering for Production](https://www.coursera.org/specializations/machine-learning-engineering-for-production-mlops) — Andrew Ng
- [Kubeflow.org docs](https://www.kubeflow.org/)
- [KFP SDK v2 reference](https://kubeflow-pipelines.readthedocs.io/en/latest/)
