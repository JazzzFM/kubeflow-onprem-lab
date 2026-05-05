# Glosario MLOps + Kubeflow

Términos clave del ecosistema. Útil para estudiantes que vienen de DevOps puro.

## A

**Artifact** — Archivo persistente producido por un step del pipeline (dataset,
modelo, métricas). En KFP cada artifact tiene tipo (`Dataset`, `Model`, `Metrics`)
y URI (S3, GCS, file:).

**Argo Workflows** — Motor de workflows DAG sobre Kubernetes. Es el "motor"
que ejecuta las pipelines KFP. KFP genera YAML de Argo internamente.

## B

**Batch inference** — Predecir miles/millones de registros offline (ej. cron
diario) vs predicción en tiempo real (request-response).

## C

**Canary deployment** — Liberar nueva versión a % pequeño de tráfico antes
de promover. KServe lo hace declarativo con `canaryTrafficPercent: 10`.

**CDI (Container Device Interface)** — Estándar OCI para que runtimes
(containerd, CRI-O) descubran GPUs sin shims propietarios. Reemplaza
device plugins legacy en K8s ≥ 1.27.

**Component (KFP)** — Función Python con `@dsl.component`. Se empaqueta como
imagen Docker, recibe inputs/outputs tipados, ejecutable en cualquier KFP server.

## D

**Data drift** — Cuando la distribución de los datos en producción cambia
respecto a los datos de training. Causa que modelos "buenos" empeoren con
el tiempo. Detectores: Alibi Detect, EvidentlyAI.

**DAG (Directed Acyclic Graph)** — Estructura de la pipeline: pasos con
dependencias, sin ciclos. KFP infiere el DAG de las llamadas `step.after()`
o `consumer(producer.outputs[...])`.

**DCGM (Data Center GPU Manager)** — SDK de NVIDIA para métricas detalladas
de GPU. `dcgm-exporter` expone como Prometheus.

**Dex** — Identity provider open-source. Kubeflow lo usa para auth (LDAP,
OIDC, GitHub, SAML).

**DSL (Domain-Specific Language)** — En KFP: el conjunto de decoradores
(`@dsl.component`, `@dsl.pipeline`, `dsl.If`) que define pipelines en Python.

## G

**GPU Operator** — Helm chart de NVIDIA que despliega: device plugin, DCGM
exporter, driver (opcional), container toolkit (opcional), MIG manager,
gpu-feature-discovery. Estándar de facto para GPU en K8s.

## H

**HPO (Hyperparameter Optimization)** — Búsqueda automática de mejores
hiperparámetros. Algoritmos: random, grid, Bayesian, Hyperband, BOHB.
**Katib** lo implementa en Kubeflow.

## I

**InferenceService (KServe CRD)** — Recurso Kubernetes que define un modelo
desplegado. Specs: `predictor`, `transformer`, `explainer`. Trae autoscaling
y traffic split out-of-the-box.

## K

**Katib** — Componente de Kubeflow para HPO + Neural Architecture Search.
Soporta: random, grid, Bayesian, hyperband, CMA-ES, PBT, Tune (Ray).

**KFP (Kubeflow Pipelines)** — Subsistema de Kubeflow para orquestación de
workflows ML como DAGs. SDK Python + UI + scheduler. Latest: v2.16.

**KServe** — Plataforma de serving de modelos sobre Kubernetes. Sucesor
abierto de SageMaker Endpoints / Vertex Predictions. Soporta: TF, PyTorch,
sklearn, ONNX, custom. Autoscale-to-zero, canary, A/B, transformers.

**Kubernetes-native ML** — Filosofía: todo se modela como CRD + controller.
Ejemplo: `PyTorchJob` es un CRD que el Training Operator reconcilia.

## L

**Lineage** — Trazabilidad de un artifact: de qué inputs salió, qué pipeline
run lo produjo, qué runs lo consumieron. ML Metadata Store lo registra
automáticamente.

## M

**MIG (Multi-Instance GPU)** — Tecnología NVIDIA (A100, H100, A30) que parte
1 GPU física en hasta 7 instancias aisladas. Cada pod recibe una "GPU virtual"
exclusiva. Consumer GPUs (RTX 4090, 5080) **NO soportan MIG**.

**ML Metadata (MLMD)** — Base de datos (sqlite/MySQL) que registra artifacts,
executions, contexts. Permite queries de lineage. Embebido en KFP.

**Model Registry** — Catálogo central de modelos versionados. Kubeflow Model
Registry (v0.2+) lo provee. Alternativas: MLflow Model Registry, SageMaker
Model Registry.

## N

**Notebook Controller** — Operator de Kubeflow que gestiona pods de Jupyter
con perfiles, GPU, persistent volumes. Multi-tenancy real.

## P

**PipelineTask** — Una invocación de componente dentro de una pipeline.
Se obtiene haciendo `task = my_component(arg=...)`. Tiene `task.outputs`,
`task.after()`.

**Profile (Kubeflow)** — Recurso CRD que crea: namespace + RBAC bindings +
quotas + network policies + Istio AuthorizationPolicy. Equivalente a un
"workspace" de un equipo.

**PyTorchJob / TFJob** — CRDs de Training Operator para entrenamiento
distribuido. El operator se encarga de setear `MASTER_ADDR`, `WORLD_SIZE`,
`RANK` en cada pod.

## R

**RuntimeClass** — Recurso K8s que asocia un nombre (`nvidia`) con un handler
de containerd (`nvidia-container-runtime`). Pods declaran `runtimeClassName`
para usar GPU.

## S

**Spark Operator** — Operator de Kubernetes para Spark on K8s. Útil para
feature engineering escalable como steps de pipelines KFP.

## T

**Time-slicing** — Estrategia donde múltiples pods comparten una misma GPU
(serializado en el driver). Útil en consumer GPUs sin MIG. Configurable
en GPU Operator.

**Training Operator** — Componente Kubeflow que gestiona PyTorchJob, TFJob,
MPIJob, MXNetJob, XGBoostJob. Reconcilia pods, restart policy, gang scheduling.

**Trigger** — Evento que arranca una pipeline: cron, push a Git, llegada de
nuevos datos en S3. KFP los implementa con Argo Events o crons externos.

## V

**Volcano** — Scheduler para batch jobs en K8s. Útil con Training Operator
para gang scheduling (todos los pods del job arrancan juntos o no arrancan).

## Acrónimos rápidos

| Sigla | Expansión |
|---|---|
| MLOps | Machine Learning Operations |
| KFP | Kubeflow Pipelines |
| HPO | Hyperparameter Optimization |
| MIG | Multi-Instance GPU |
| CDI | Container Device Interface |
| MLMD | ML Metadata Store |
| OIDC | OpenID Connect |
| RBAC | Role-Based Access Control |
| CRD | Custom Resource Definition |
| HPA | Horizontal Pod Autoscaler |
| PVC | PersistentVolumeClaim |
| DSL | Domain-Specific Language |
| DCGM | Data Center GPU Manager |
| GFD | GPU Feature Discovery |
