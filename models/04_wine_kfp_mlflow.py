"""
Demo 4: Pipeline end-to-end estilo Canonical wine-quality, ejecutable localmente.

Equivalente a https://charmed-kubeflow.io/docs/build-your-first-ml-model
pero ejecutado con `kfp.local` + MLflow standalone (sin CKF, sin Juju, sin KServe).
Cuando llegue EKS / CKF, el MISMO código corre cambiando solo `local.init` → `kfp.Client(host=...)`.

Pipeline: download → preprocess → train (ElasticNet) → evaluate
Tracking: MLflow local con backend sqlite.
"""
import json
from pathlib import Path
from kfp import dsl, local
from kfp.dsl import Input, Output, Dataset, Model, Metrics

# Runner local (sin cluster K8s, sin CKF)
local.init(runner=local.SubprocessRunner(use_venv=False))

WINE_URL = "https://raw.githubusercontent.com/canonical/kubeflow-examples/main/e2e-wine-kfp-mlflow/winequality-red.csv"
OUT = Path("/mnt/c/temp/lab-models/outputs")
OUT.mkdir(exist_ok=True, parents=True)


@dsl.component
def download_dataset(url: str, dataset: Output[Dataset]) -> None:
    """Descarga wine-quality CSV desde URL."""
    import requests, pandas as pd
    from io import StringIO
    print(f"[download] fetching {url}")
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    df = pd.read_csv(StringIO(r.text), header=0, sep=";")
    df.to_csv(dataset.path, index=False)
    print(f"[download] saved {len(df)} rows × {len(df.columns)} cols → {dataset.path}")


@dsl.component
def preprocess_dataset(input_dataset: Input[Dataset], output_dataset: Output[Dataset]) -> None:
    """Normaliza nombres de columnas y guarda como parquet (Canonical pattern)."""
    import pandas as pd
    df = pd.read_csv(input_dataset.path, header=0)
    df.columns = [c.lower().replace(" ", "_") for c in df.columns]
    df.to_parquet(output_dataset.path)
    print(f"[preprocess] columns: {list(df.columns)}")
    print(f"[preprocess] {len(df)} rows → parquet")


@dsl.component
def train_elasticnet(
    dataset: Input[Dataset],
    model: Output[Model],
    metrics: Output[Metrics],
    alpha: float = 0.5,
    l1_ratio: float = 0.5,
) -> str:
    """Entrena ElasticNet y trackea con MLflow local (backend sqlite)."""
    import os, json, joblib
    import numpy as np, pandas as pd
    from sklearn.linear_model import ElasticNet
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

    # MLflow opcional (usar si está instalado)
    try:
        import mlflow
        from mlflow.tracking import MlflowClient
        mlflow.set_tracking_uri(f"sqlite:///{os.environ.get('HOME','/tmp')}/mlflow.db")
        mlflow.set_experiment("wine-quality-elasticnet")
        mlflow_available = True
    except ImportError:
        mlflow_available = False
        print("[train] MLflow no instalado, saltando tracking remoto")

    df = pd.read_parquet(dataset.path)
    target = "quality"
    X = df.drop(columns=[target])
    y = df[target]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

    print(f"[train] alpha={alpha} l1_ratio={l1_ratio}")
    print(f"[train] train={len(Xtr)} test={len(Xte)} features={X.shape[1]}")

    if mlflow_available:
        mlflow.sklearn.autolog()
        with mlflow.start_run(run_name="elasticnet-local"):
            mlflow.set_tag("origin", "kfp.local")
            clf = ElasticNet(alpha=alpha, l1_ratio=l1_ratio, random_state=42)
            clf.fit(Xtr, ytr)
            pred = clf.predict(Xte)
            mse = mean_squared_error(yte, pred)
            mae = mean_absolute_error(yte, pred)
            r2 = r2_score(yte, pred)
            mlflow.log_metric("mse", mse)
            mlflow.log_metric("mae", mae)
            mlflow.log_metric("r2", r2)
            run_id = mlflow.active_run().info.run_id
            tracking_uri = mlflow.get_tracking_uri()
    else:
        clf = ElasticNet(alpha=alpha, l1_ratio=l1_ratio, random_state=42)
        clf.fit(Xtr, ytr)
        pred = clf.predict(Xte)
        mse = mean_squared_error(yte, pred)
        mae = mean_absolute_error(yte, pred)
        r2 = r2_score(yte, pred)
        run_id = "no-mlflow"
        tracking_uri = "n/a"

    joblib.dump(clf, model.path)
    metrics.log_metric("mse", float(mse))
    metrics.log_metric("mae", float(mae))
    metrics.log_metric("r2", float(r2))

    print(f"[train] MSE={mse:.4f} MAE={mae:.4f} R²={r2:.4f}")
    print(f"[train] mlflow_run_id={run_id} tracking_uri={tracking_uri}")
    return run_id


@dsl.component
def evaluate_and_report(
    model: Input[Model],
    metrics: Input[Metrics],
    run_id: str,
) -> str:
    """Genera reporte final + simula 'deploy decision' (sin KServe local)."""
    import json
    print("=" * 60)
    print("PIPELINE WINE QUALITY — REPORTE END-TO-END")
    print("=" * 60)
    print(f"Model artifact: {model.path}")
    print(f"MLflow run_id: {run_id}")
    metric_data = json.loads(json.dumps(metrics.metadata)) if metrics.metadata else {}
    print(f"Metrics: {metric_data}")
    print("")
    print("--- Decisión de deployment ---")
    print("[skip] KServe deploy: requiere cluster Kubeflow real (no kfp.local).")
    print("       Próximo paso EKS → habilitar componente deploy_to_kserve.")
    print("=" * 60)
    return f"deployed=false (local mode), run_id={run_id}"


@dsl.pipeline(
    name="wine-quality-elasticnet-pipeline",
    description="End-to-end estilo Canonical wine-quality. Local execution con kfp.local.",
)
def wine_pipeline(url: str = WINE_URL, alpha: float = 0.5, l1_ratio: float = 0.5):
    download = download_dataset(url=url)
    preprocess = preprocess_dataset(input_dataset=download.outputs["dataset"])
    train = train_elasticnet(
        dataset=preprocess.outputs["output_dataset"],
        alpha=alpha,
        l1_ratio=l1_ratio,
    )
    evaluate_and_report(
        model=train.outputs["model"],
        metrics=train.outputs["metrics"],
        run_id=train.outputs["Output"],
    )


if __name__ == "__main__":
    print("=" * 60)
    print("DEMO 4: WINE QUALITY PIPELINE (Canonical-style, kfp.local)")
    print("=" * 60)
    print("\nEquivalente a https://charmed-kubeflow.io/docs/build-your-first-ml-model")
    print("Sin CKF/Juju/KServe — corre como subprocess. Misma pipeline va a EKS.\n")
    pipeline_run = wine_pipeline(alpha=0.5, l1_ratio=0.5)
    print("\n[OK] Pipeline ejecutada localmente.")
    summary = {
        "pipeline": "wine-quality-elasticnet-pipeline",
        "based_on": "https://charmed-kubeflow.io/docs/build-your-first-ml-model",
        "execution_mode": "kfp.local.SubprocessRunner (sin cluster K8s)",
        "components": ["download_dataset", "preprocess_dataset", "train_elasticnet", "evaluate_and_report"],
        "dataset": "winequality-red.csv (Canonical kubeflow-examples)",
        "model": "ElasticNet (sklearn)",
        "tracking": "MLflow opcional (sqlite local)",
        "next_step_eks": "habilitar componente deploy_to_kserve + cambiar a kfp.Client(host='kfp.eks.example.com')",
    }
    OUT.mkdir(exist_ok=True, parents=True)
    (OUT / "wine_pipeline_summary.json").write_text(json.dumps(summary, indent=2))
