# Kubeflow On-Premise — Outline del curso

## Módulos local (k3s en WSL2 / laptop)
1. **Kubernetes desde cero**: kubeadm vs k3s, control plane, worker nodes
2. **CNI y networking**: Flannel, Cilium, NetworkPolicies
3. **Storage**: Longhorn, local-path, persistent volumes
4. **Ingress y service mesh**: MetalLB, Istio fundamentals
5. **GPU en Kubernetes**: NVIDIA Container Toolkit, GPU Operator, RuntimeClass, CDI
6. **Pod lifecycle + GPU passthrough**: demo en vivo con `nvidia-smi`

## Módulos cloud (AWS EKS)
7. **Bootstrap EKS**: eksctl, node groups (CPU + GPU spot), VPC
8. **Kubeflow install**: manifests + kustomize image overrides
9. **Pipelines (KFP v2)**: SDK, components, DAG, scheduling
10. **Notebooks multi-tenant**: profiles, JupyterHub
11. **Training distribuido**: Training Operator (PyTorchJob)
12. **Inference**: KServe + autoscaling

## Módulos avanzados
13. **Image registry on-prem**: Harbor + skopeo mirroring
14. **Auth**: Dex + Keycloak / Cognito OIDC
15. **Observability**: Prometheus + Grafana + DCGM exporter
16. **GitOps**: Argo CD para Kubeflow declarativo
