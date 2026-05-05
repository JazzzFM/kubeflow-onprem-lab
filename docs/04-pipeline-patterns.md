# Patrones de Pipelines MLOps

5 patrones reales que enseñamos en el curso. **Código KFP SDK v2** ejecutable.

## Patrón 1: Training pipeline básico

El "hello world" de MLOps: pipeline que entrena, evalúa, registra.

```mermaid
flowchart LR
    A[fetch_data] --> B[split_train_test]
    B --> C[train]
    B --> D[validate_data]
    C --> E[evaluate]
    D --> E
    E --> F{accuracy<br/>≥ threshold}
    F -- "sí" --> G[register_model]
    F -- "no" --> H[fail + alert]

    style F fill:#ffe0cc
    style G fill:#d6f5d6
    style H fill:#ffcccc
```

```python
from kfp import dsl

@dsl.component(packages_to_install=["scikit-learn", "pandas"])
def fetch_data(output_dataset: dsl.Output[dsl.Dataset]):
    import pandas as pd
    from sklearn.datasets import load_iris
    iris = load_iris(as_frame=True)
    df = iris.frame
    df.to_parquet(output_dataset.path)

@dsl.component(packages_to_install=["scikit-learn", "pandas"])
def train(
    dataset: dsl.Input[dsl.Dataset],
    model: dsl.Output[dsl.Model],
) -> float:
    import pandas as pd, joblib
    from sklearn.ensemble import RandomForestClassifier
    df = pd.read_parquet(dataset.path)
    X, y = df.drop("target", axis=1), df["target"]
    clf = RandomForestClassifier(n_estimators=100).fit(X, y)
    joblib.dump(clf, model.path)
    return float(clf.score(X, y))

@dsl.pipeline(name="basic-training")
def pipeline(min_accuracy: float = 0.9):
    data = fetch_data()
    train_step = train(dataset=data.outputs["output_dataset"])
    with dsl.If(train_step.output >= min_accuracy):
        register_model(model=train_step.outputs["model"])
```

## Patrón 2: Pipeline con artifacts y lineage

Cada output queda registrado en ML Metadata Store con su input lineage.

```mermaid
flowchart LR
    D1[(Dataset v1)] --> T1[Train run 42]
    T1 --> M1[(Model v3)]
    M1 --> D[Deploy]
    D --> S[Serving]
    S -.->|"métricas"| MLMD[(ML Metadata)]
    M1 -.-> MLMD
    D1 -.-> MLMD
    T1 -.-> MLMD

    classDef artifact fill:#fff5d6
    classDef process fill:#cce5ff
    class D1,M1 artifact
    class T1,D,S process
```

KFP automáticamente registra:
- **Provenance**: este Model viene de este Dataset y este pipeline run
- **Reproducibility**: hash de imagen + parámetros + código
- **Lineage queries**: "qué modelos usaron Dataset v1" → query en MLMD

## Patrón 3: Retraining condicional

Reentrenar **solo cuando** los datos drift o métrica baja:

```mermaid
flowchart TB
    START([Trigger:<br/>cron diario]) --> FETCH[fetch_new_data]
    FETCH --> COMPARE[compare_distribution<br/>vs training data]
    COMPARE --> DRIFT{drift<br/>score > 0.1?}
    DRIFT -- "no" --> END1([no-op])
    DRIFT -- "sí" --> RETRAIN[retrain_model]
    RETRAIN --> EVAL[evaluate]
    EVAL --> BETTER{better<br/>than current?}
    BETTER -- "no" --> END2([keep old model])
    BETTER -- "sí" --> CANARY[deploy_canary<br/>10% traffic]
    CANARY --> MONITOR[monitor_canary<br/>1h]
    MONITOR --> SAFE{p99 latency<br/>+ error rate OK?}
    SAFE -- "sí" --> PROMOTE[promote to 100%]
    SAFE -- "no" --> ROLLBACK[rollback]

    classDef start fill:#cce5ff
    classDef decision fill:#ffe0cc
    classDef action fill:#d6f5d6
    classDef terminal fill:#fff5d6
    class START start
    class DRIFT,BETTER,SAFE decision
    class FETCH,COMPARE,RETRAIN,EVAL,CANARY,MONITOR,PROMOTE,ROLLBACK action
    class END1,END2 terminal
```

```python
@dsl.pipeline(name="retraining-pipeline")
def retraining(drift_threshold: float = 0.1):
    new_data = fetch_new_data()
    drift = compare_distribution(
        new_data=new_data.outputs["dataset"],
        baseline=baseline_data,
    )
    with dsl.If(drift.output > drift_threshold):
        new_model = retrain_model(new_data=new_data.outputs["dataset"])
        eval_result = evaluate(model=new_model.outputs["model"])
        with dsl.If(eval_result.output > current_baseline_score):
            deploy_canary(model=new_model.outputs["model"], traffic=0.1)
```

## Patrón 4: Batch inference

No siempre necesitas serving en tiempo real. Para predicciones batch
(scoring nocturno de millones de filas):

```mermaid
flowchart LR
    CRON([cron 02:00 AM]) --> KFP[Pipeline KFP]
    KFP --> READ[read_partition<br/>desde S3/HDFS]
    READ --> BATCH[batch_predict<br/>distribuido]
    BATCH --> WRITE[write_predictions<br/>parquet]
    WRITE --> NOTIFY[Slack/email<br/>completion]
    BATCH -.->|"GPU spot"| G[g5.12xlarge<br/>4× A10G]

    style G fill:#fff5d6
```

```python
@dsl.component(packages_to_install=["pyarrow", "torch"])
def batch_predict(
    input_partition: dsl.Input[dsl.Dataset],
    model: dsl.Input[dsl.Model],
    output_predictions: dsl.Output[dsl.Dataset],
) -> NamedTuple("Stats", [("rows_predicted", int), ("avg_latency_ms", float)]):
    # ... inferencia en batches de 10k filas con GPU
    ...
```

Ventaja vs SageMaker BatchTransform: **mismo código que el training pipeline**,
no API diferente. Reusas componentes.

## Patrón 5: Distributed training con PyTorchJob

Modelos grandes → varias GPUs → varios nodos:

```mermaid
flowchart TB
    subgraph KF["Kubeflow Training Operator"]
        K[PyTorchJob CRD]
    end

    subgraph N1["Node 1 (master)"]
        M[pod master<br/>rank=0]
    end

    subgraph N2["Node 2 (worker)"]
        W1[pod worker-0<br/>rank=1]
    end

    subgraph N3["Node 3 (worker)"]
        W2[pod worker-1<br/>rank=2]
    end

    subgraph N4["Node 4 (worker)"]
        W3[pod worker-2<br/>rank=3]
    end

    K -->|"creates"| M
    K -->|"creates"| W1
    K -->|"creates"| W2
    K -->|"creates"| W3
    M <-->|"NCCL all-reduce"| W1
    M <-->|"NCCL all-reduce"| W2
    M <-->|"NCCL all-reduce"| W3
    W1 <--> W2
    W2 <--> W3

    classDef master fill:#d6f5d6
    classDef worker fill:#cce5ff
    class M master
    class W1,W2,W3 worker
```

```yaml
apiVersion: kubeflow.org/v1
kind: PyTorchJob
metadata:
  name: distributed-resnet
spec:
  pytorchReplicaSpecs:
    Master:
      replicas: 1
      template:
        spec:
          runtimeClassName: nvidia
          containers:
            - name: pytorch
              image: my-registry/resnet-train:v3
              resources:
                limits: { nvidia.com/gpu: 1 }
    Worker:
      replicas: 3
      template:
        spec:
          runtimeClassName: nvidia
          containers:
            - name: pytorch
              image: my-registry/resnet-train:v3
              resources:
                limits: { nvidia.com/gpu: 1 }
```

Training Operator se encarga de:
- Setear `MASTER_ADDR`, `MASTER_PORT`, `WORLD_SIZE`, `RANK` en cada pod
- Reiniciar workers si crashean (fault tolerance)
- Limpiar al terminar

Sin Training Operator harías esto a mano con StatefulSet + headless service +
script bash de bootstrap. **3-5× más código.**

## Resumen de patrones

| Patrón | Cuándo usarlo | Componente Kubeflow clave |
|---|---|---|
| Training básico | Onboarding, ML clásico | KFP Pipelines |
| Lineage | Compliance, debugging "qué modelo sirvió X cliente" | ML Metadata + KFP |
| Retraining condicional | Producción real, ahorro de cómputo | KFP + dsl.If + Cron |
| Batch inference | Predicciones nocturnas, no real-time | KFP + (opcional) Spark Operator |
| Distributed training | Modelos > 1 GPU | Training Operator (PyTorchJob/TFJob) |

Cada patrón se mapea a 1-2 módulos del curso. Ver [`00-curso-outline.md`](00-curso-outline.md).
