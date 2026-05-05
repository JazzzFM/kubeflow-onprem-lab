---
name: Kubeflow on-prem training lab
description: User is building a production-grade on-prem Kubeflow lab with NVIDIA GPU support, intended as the basis for instructor-led courses. Strategy is local-first with AWS burst.
type: project
originSessionId: 402ad9a2-dc48-42d6-8f33-db8503dad54a
---
User is building an on-prem Kubeflow environment with NVIDIA GPU support to use as the reference platform for courses he will teach.

**Why:** The lab must mirror what students would meet in real enterprises — not a toy install. He will explain each component to learners, so design decisions need to be defensible and replicable.

**Hardware available (laptop = primary lab):**
- MSI Vector 16 HX AI A2XWIG (2025)
- Intel Core Ultra 9 275HX, 24 cores
- **16 GB DDR5-5600** (2× 8 GB Samsung, 2 SO-DIMM slots — ampliable hasta 96 GB)
- NVIDIA RTX 5080 Laptop GPU, 16 GB VRAM (Blackwell, sm_120)
- 954 GB NVMe Micron 2500
- Windows 11 Home build 26200, WSL 2.5.10, Ubuntu 20.04 (planeado migrar a 24.04)

**Cloud available:** AWS with company credits. Strategy is **local-first, AWS only for what does not fit locally** (multi-node, big distributed training, scale-out demos).

**How to apply:**
- Default stack to recommend on-prem: kubeadm or RKE2 + containerd + Cilium/Calico + MetalLB + Longhorn or Rook-Ceph + cert-manager + NVIDIA GPU Operator + Kubeflow manifests + Dex/OIDC + kube-prometheus-stack.
- For the laptop's 16 GB constraint, recommend k3s + Kubeflow lite (Notebooks + Pipelines + Training Operator) — not full Kubeflow.
- AWS modules should teach kubeadm-on-EC2 OR EKS, with strict teardown discipline (Spot, tagged resources, autoshutdown). Treat credits as finite even if "the company has them."
- When walking through any step, frame it as "what to teach here" — common student questions, pitfalls, troubleshooting heuristics.
- Avoid WSL2/minikube/kind shortcuts unless explicitly framed as "demo on a laptop" variant.
- Treat Kubeflow 1.9+ (manifests-based) as current; `kfctl` is deprecated.
