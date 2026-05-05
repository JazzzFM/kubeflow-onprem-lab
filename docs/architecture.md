# Arquitectura del lab

Diagrama detallado de cómo se conectan las capas, desde el host Windows hasta
los pods con GPU.

## Stack vertical (de hardware a workload)

```
┌─────────────────────────────────────────────────────────────────────┐
│ HARDWARE                                                            │
│   MSI Vector 16 HX AI A2XWIG                                        │
│   Intel Core Ultra 9 275HX (24 cores, 0 SMT)                        │
│   16 GB DDR5-5600 (ampliable a 96 GB)                               │
│   NVIDIA GeForce RTX 5080 Laptop GPU (Blackwell, 16 GB VRAM)        │
│   954 GB NVMe Micron 2500                                           │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ WINDOWS HOST                                                        │
│   Windows 11 Home Build 26200                                       │
│   NVIDIA Driver 591.44 (CUDA 13.1)                                  │
│   WSL 2.5.10 + Hyper-V                                              │
│   Docker Desktop                                                    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │  /dev/dxg paravirtual
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ WSL2 GUEST (Ubuntu 24.04)                                           │
│   Kernel 6.6.87 microsoft-WSL2                                      │
│   /etc/wsl.conf:                                                    │
│     [user] default=jazielflo                                        │
│     [boot] command="mount --make-rshared /"                         │
│     [boot] systemd=true                                             │
│   PID 1 = systemd                                                   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ k3s v1.35.4 (single-node)                                           │
│   /usr/local/bin/k3s server                                         │
│   embedded containerd                                               │
│   embedded etcd (kine sqlite)                                       │
│   --disable=traefik --disable=servicelb                             │
│   Auto-detecta /usr/bin/nvidia-container-runtime                    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ NVIDIA stack en cluster                                             │
│   nvidia-container-toolkit 1.19.0  (host)                           │
│   /etc/cdi/nvidia.yaml             (CDI spec mode=wsl)              │
│   GPU Operator (Helm)                                               │
│     ├─ gpu-feature-discovery        (etiqueta nodo)                 │
│     ├─ nvidia-device-plugin         (registra nvidia.com/gpu)       │
│     ├─ nvidia-dcgm-exporter         (metrics Prometheus)            │
│     └─ nvidia-operator-validator    (health check periódico)        │
│   RuntimeClass nvidia → /usr/bin/nvidia-container-runtime           │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ WORKLOAD (pods con GPU)                                             │
│   Pod gpu-test                                                      │
│     runtimeClassName: nvidia                                        │
│     resources.limits.nvidia.com/gpu: 1                              │
│     image: nvcr.io/nvidia/cuda:13.0.0-base-ubuntu24.04              │
│     command: nvidia-smi                                             │
│   Output: ve la RTX 5080 dentro del container                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Flujo de una petición de GPU

```
1. kubectl apply -f gpu-test-pod.yaml
                │
                ▼
2. API server valida + persiste en etcd
                │
                ▼
3. Scheduler ve `runtimeClassName: nvidia` y `nvidia.com/gpu: 1`
                │
                ▼
4. Scheduler busca nodo con `nvidia.com/gpu: 1` allocatable
   (registrado por nvidia-device-plugin)
                │
                ▼
5. Kubelet recibe el pod, contacta containerd
                │
                ▼
6. Containerd usa runtime "nvidia" (handler del RuntimeClass)
                │
                ▼
7. nvidia-container-runtime invoca nvidia-cdi-hook
                │
                ▼
8. CDI hook lee /etc/cdi/nvidia.yaml + monta:
   - /dev/dxg (paravirtual GPU)
   - /usr/lib/wsl/drivers/.../libcuda.so.1
   - /usr/lib/wsl/drivers/.../nvidia-smi
                │
                ▼
9. Container arranca → ejecuta nvidia-smi
                │
                ▼
10. nvidia-smi llama libcuda → /dev/dxg → Hyper-V → driver Windows → GPU
```

## Por qué cada capa importa para el curso

- **WSL2**: enseña a alumnos que GPU passthrough en WSL es diferente al
  bare-metal (DXG vs nvidia0).
- **systemd en WSL**: necesario para k3s + Helm + servicios. Habilitarlo es
  paso 0 obligatorio.
- **CDI vs device plugin antiguo**: estándar moderno. Manifest declarativo
  vs hooks imperativos.
- **GPU Operator**: meta-installer que evita instalar 5 componentes a mano.
  Production pattern.
- **RuntimeClass**: permite pods CPU-only y GPU coexistiendo. Patrón clave
  para multi-tenancy.
