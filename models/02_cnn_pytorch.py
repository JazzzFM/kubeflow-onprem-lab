"""
Demo 2: CNN classica (LeNet-5) en PyTorch — Deep Learning con GPU.
Dataset: MNIST (60k train, 10k test).
Valida CUDA, entrena 3 epochs, mide tiempo + GPU memory.
"""
import json, time
from pathlib import Path
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

print("=" * 60)
print("DEMO 2: CNN CON PYTORCH + GPU (LeNet-5 sobre MNIST)")
print("=" * 60)

print(f"\nPyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA version (PyTorch built with): {torch.version.cuda}")
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"GPU compute capability: sm_{torch.cuda.get_device_capability(0)[0]}{torch.cuda.get_device_capability(0)[1]}")
    device = torch.device("cuda")
else:
    print("[WARN] CUDA no disponible, usando CPU")
    device = torch.device("cpu")
print(f"Device: {device}\n")

# LeNet-5 modernizado
class LeNet5(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 6, kernel_size=5, padding=2)
        self.conv2 = nn.Conv2d(6, 16, kernel_size=5)
        self.fc1 = nn.Linear(16 * 5 * 5, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, 10)

    def forward(self, x):
        x = F.max_pool2d(F.relu(self.conv1(x)), 2)
        x = F.max_pool2d(F.relu(self.conv2(x)), 2)
        x = x.flatten(1)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.fc3(x)

print("Cargando MNIST (descarga ~10 MB la primera vez)...")
transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))])
train_ds = datasets.MNIST("/tmp/mnist", train=True, download=True, transform=transform)
test_ds = datasets.MNIST("/tmp/mnist", train=False, download=True, transform=transform)
train_loader = DataLoader(train_ds, batch_size=128, shuffle=True, num_workers=2)
test_loader = DataLoader(test_ds, batch_size=256, shuffle=False, num_workers=2)
print(f"  [ok] train={len(train_ds)} test={len(test_ds)}")

model = LeNet5().to(device)
print(f"\nModelo: LeNet-5 ({sum(p.numel() for p in model.parameters()):,} parámetros)")
optimizer = optim.Adam(model.parameters(), lr=1e-3)

n_epochs = 3
print(f"\nEntrenando {n_epochs} epochs...")
t0 = time.time()
epoch_data = []
for epoch in range(n_epochs):
    model.train()
    ep_t0 = time.time()
    losses = []
    for batch_idx, (x, y) in enumerate(train_loader):
        x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
        optimizer.zero_grad()
        out = model(x)
        loss = F.cross_entropy(out, y)
        loss.backward()
        optimizer.step()
        losses.append(loss.item())
    # eval
    model.eval()
    correct = 0
    with torch.no_grad():
        for x, y in test_loader:
            x, y = x.to(device), y.to(device)
            pred = model(x).argmax(dim=1)
            correct += pred.eq(y).sum().item()
    acc = correct / len(test_ds)
    ep_time = time.time() - ep_t0
    avg_loss = sum(losses) / len(losses)
    print(f"  epoch {epoch+1}/{n_epochs} — loss={avg_loss:.4f} test_acc={acc:.4f} time={ep_time:.2f}s")
    epoch_data.append({"epoch": epoch + 1, "loss": round(avg_loss, 4), "test_acc": round(acc, 4), "time_sec": round(ep_time, 2)})

total_time = time.time() - t0
print(f"\n[OK] Total training time: {total_time:.2f}s")
gpu_mem_mb = None
if torch.cuda.is_available():
    gpu_mem_mb = round(torch.cuda.max_memory_allocated() / 1024**2, 1)
    print(f"GPU max memory used: {gpu_mem_mb} MiB")

results = {
    "model": "LeNet-5",
    "framework": "pytorch",
    "pytorch_version": torch.__version__,
    "cuda_available": torch.cuda.is_available(),
    "cuda_version": torch.version.cuda if torch.cuda.is_available() else None,
    "device": str(device),
    "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    "gpu_compute_capability": f"sm_{torch.cuda.get_device_capability(0)[0]}{torch.cuda.get_device_capability(0)[1]}" if torch.cuda.is_available() else None,
    "dataset": "MNIST",
    "n_train": len(train_ds),
    "n_test": len(test_ds),
    "n_params": sum(p.numel() for p in model.parameters()),
    "epochs": n_epochs,
    "batch_size": 128,
    "optimizer": "Adam",
    "lr": 1e-3,
    "epoch_results": epoch_data,
    "final_accuracy": round(epoch_data[-1]["test_acc"], 4),
    "total_training_time_sec": round(total_time, 2),
    "gpu_max_memory_mib": gpu_mem_mb,
}
out = Path("/mnt/c/temp/lab-models/outputs/cnn_results.json")
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(results, indent=2))
print(f"\nResultado guardado en: {out}")
print("\n[OK] Demo 2 completado")
