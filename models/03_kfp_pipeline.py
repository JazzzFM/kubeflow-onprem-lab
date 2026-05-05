"""
Demo 3: Kubeflow Pipelines SDK v2 — pipeline local con `kfp local`.
Empaqueta GBC + CNN como componentes y los orquesta como pipeline.
Ejecuta SIN cluster K8s usando SubprocessRunner.
"""
import json
from pathlib import Path
from kfp import dsl, local
from typing import NamedTuple

# Inicializar runner local (sin cluster)
local.init(runner=local.SubprocessRunner(use_venv=False))

# -----------------------------------------------------------------------------
# Componente 1: Gradient Boosting Classifier (ML clásico)
# -----------------------------------------------------------------------------
@dsl.component
def train_gradient_boosting(
    n_estimators: int = 200,
    max_depth: int = 3,
    test_size: float = 0.25,
) -> NamedTuple("GBCResult", [("accuracy", float), ("training_time_sec", float)]):
    """Entrena Gradient Boosting Classifier sobre dataset Wine."""
    import time
    from collections import namedtuple
    from sklearn.datasets import load_wine
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score

    print(f"[GBC] Entrenando con n_estimators={n_estimators}, max_depth={max_depth}")
    data = load_wine()
    X_train, X_test, y_train, y_test = train_test_split(
        data.data, data.target, test_size=test_size, random_state=42, stratify=data.target
    )
    clf = GradientBoostingClassifier(n_estimators=n_estimators, max_depth=max_depth, random_state=42)
    t0 = time.time()
    clf.fit(X_train, y_train)
    t = time.time() - t0
    acc = accuracy_score(y_test, clf.predict(X_test))
    print(f"[GBC] accuracy={acc:.4f} time={t:.2f}s")
    Out = namedtuple("GBCResult", ["accuracy", "training_time_sec"])
    return Out(accuracy=float(acc), training_time_sec=float(t))


# -----------------------------------------------------------------------------
# Componente 2: CNN PyTorch sobre MNIST (Deep Learning + GPU)
# -----------------------------------------------------------------------------
@dsl.component
def train_cnn_pytorch(
    epochs: int = 2,
    batch_size: int = 128,
    lr: float = 1e-3,
) -> NamedTuple("CNNResult", [("accuracy", float), ("training_time_sec", float), ("device", str), ("gpu_name", str)]):
    """Entrena LeNet-5 sobre MNIST con PyTorch. Usa GPU si disponible."""
    import time
    from collections import namedtuple
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    import torch.optim as optim
    from torch.utils.data import DataLoader
    from torchvision import datasets, transforms

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A"
    print(f"[CNN] device={device} gpu={gpu_name}")

    class LeNet5(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv1 = nn.Conv2d(1, 6, 5, padding=2)
            self.conv2 = nn.Conv2d(6, 16, 5)
            self.fc1, self.fc2, self.fc3 = nn.Linear(400, 120), nn.Linear(120, 84), nn.Linear(84, 10)

        def forward(self, x):
            x = F.max_pool2d(F.relu(self.conv1(x)), 2)
            x = F.max_pool2d(F.relu(self.conv2(x)), 2)
            return self.fc3(F.relu(self.fc2(F.relu(self.fc1(x.flatten(1))))))

    transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))])
    train_ds = datasets.MNIST("/tmp/mnist", train=True, download=True, transform=transform)
    test_ds = datasets.MNIST("/tmp/mnist", train=False, download=True, transform=transform)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=2)
    test_loader = DataLoader(test_ds, batch_size=256, shuffle=False, num_workers=2)

    model = LeNet5().to(device)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    t0 = time.time()
    for epoch in range(epochs):
        model.train()
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            F.cross_entropy(model(x), y).backward()
            optimizer.step()
    train_time = time.time() - t0

    model.eval()
    correct = 0
    with torch.no_grad():
        for x, y in test_loader:
            x, y = x.to(device), y.to(device)
            correct += model(x).argmax(1).eq(y).sum().item()
    acc = correct / len(test_ds)
    print(f"[CNN] accuracy={acc:.4f} time={train_time:.2f}s device={device}")
    Out = namedtuple("CNNResult", ["accuracy", "training_time_sec", "device", "gpu_name"])
    return Out(accuracy=float(acc), training_time_sec=float(train_time), device=str(device), gpu_name=str(gpu_name))


# -----------------------------------------------------------------------------
# Componente 3: Comparar resultados (orquestación entre los 2)
# -----------------------------------------------------------------------------
@dsl.component
def compare_models(
    gbc_acc: float, gbc_time: float,
    cnn_acc: float, cnn_time: float, cnn_device: str, cnn_gpu: str,
) -> str:
    """Genera reporte comparativo de los 2 modelos."""
    report = f"""
============================================================
PIPELINE KFP — REPORTE COMPARATIVO
============================================================

[1] Gradient Boosting Classifier (sklearn, CPU)
    - Accuracy:      {gbc_acc:.4f}
    - Training time: {gbc_time:.2f}s
    - Dataset:       Wine (178 samples, 13 features)

[2] LeNet-5 CNN (PyTorch, {cnn_device})
    - Accuracy:      {cnn_acc:.4f}
    - Training time: {cnn_time:.2f}s
    - Device:        {cnn_device}
    - GPU:           {cnn_gpu}
    - Dataset:       MNIST (60k train, 10k test)
============================================================
""".strip()
    print(report)
    return report


# -----------------------------------------------------------------------------
# Pipeline orquestada: GBC -> CNN -> Reporte
# -----------------------------------------------------------------------------
@dsl.pipeline(
    name="ml-dl-demo-pipeline",
    description="Demo: ML clásico (GBC) + DL (CNN-GPU) + reporte comparativo",
)
def ml_dl_pipeline(epochs: int = 2):
    gbc = train_gradient_boosting(n_estimators=200, max_depth=3)
    cnn = train_cnn_pytorch(epochs=epochs, batch_size=128)
    cnn.after(gbc)  # asegurar orden secuencial
    compare_models(
        gbc_acc=gbc.outputs["accuracy"],
        gbc_time=gbc.outputs["training_time_sec"],
        cnn_acc=cnn.outputs["accuracy"],
        cnn_time=cnn.outputs["training_time_sec"],
        cnn_device=cnn.outputs["device"],
        cnn_gpu=cnn.outputs["gpu_name"],
    )


if __name__ == "__main__":
    print("=" * 60)
    print("DEMO 3: KUBEFLOW PIPELINES SDK v2 — local execution")
    print("=" * 60)
    print("\nEjecutando pipeline 'ml-dl-demo-pipeline' con SubprocessRunner...")
    print("(misma pipeline que correra en EKS manana, sin cluster local)\n")

    pipeline_run = ml_dl_pipeline(epochs=2)

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETED")
    print("=" * 60)

    # Guardar outputs como JSON para el daily
    out_dir = Path("/mnt/c/temp/lab-models/outputs")
    out_dir.mkdir(exist_ok=True, parents=True)
    summary = {
        "pipeline": "ml-dl-demo-pipeline",
        "framework": "kfp.local.SubprocessRunner",
        "kfp_sdk_version": __import__("kfp").__version__,
        "components": ["train_gradient_boosting", "train_cnn_pytorch", "compare_models"],
        "execution_mode": "local (sin cluster K8s)",
        "next_step": "ejecutar misma pipeline en EKS con kfp.Client.create_run_from_pipeline_func()",
    }
    (out_dir / "kfp_pipeline_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\nResumen guardado: {out_dir}/kfp_pipeline_summary.json")
