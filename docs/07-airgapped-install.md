# Air-Gapped Kubeflow Install — Patrón general + ejemplo Charmed Kubeflow

> **Módulo 13 del curso.** Cómo instalar Kubeflow en entornos sin internet:
> bancos, gobierno, salud, defensa, manufacturing OT, plantas industriales.

## ¿Por qué air-gapped?

```mermaid
flowchart LR
    subgraph PUB["Internet público"]
        DH[(Docker Hub)]
        GHCR[(ghcr.io)]
        GCR[(gcr.io)]
        QUAY[(quay.io)]
    end

    subgraph DMZ["DMZ / bastion"]
        MIRROR[Harbor mirror<br/>+ skopeo]
        ART[Artifact storage<br/>S3 / NFS]
    end

    subgraph AG["Red air-gapped (sin internet)"]
        K8S[Kubernetes cluster]
        REG[Container registry<br/>interno]
        K8S --> REG
    end

    DH -.-> MIRROR
    GHCR -.-> MIRROR
    GCR -.-> MIRROR
    QUAY -.-> MIRROR
    MIRROR -.->|"transfer offline<br/>USB / SFTP / data diode"| AG
    MIRROR -.-> ART
    ART -.-> AG

    style PUB fill:#e6f3ff,stroke:#0066cc
    style DMZ fill:#fff5d6,stroke:#cc9900
    style AG fill:#ffcccc,stroke:#cc0000
```

**Casos de uso reales:**

| Sector | Ejemplo |
|---|---|
| **Banca** | Modelos antifraude on-prem, datos no salen del datacenter |
| **Gobierno** | Defensa, inteligencia, plataformas con clasificación |
| **Salud** | HIPAA strict mode, datos de pacientes nunca tocan cloud |
| **Industrial / OT** | Plantas con red OT separada, modelos de mantenimiento predictivo |
| **Soberanía digital** | Países con leyes de residencia de datos (Rusia, China, UE post-Schrems II) |

## Patrón general (4 fases)

```mermaid
flowchart LR
    A[1. Generate artifacts] --> B[2. Transfer offline]
    B --> C[3. Load to internal registry]
    C --> D[4. Install Kubeflow apuntando al registry]

    A -.- A1[skopeo / docker pull<br/>save → tar.gz]
    B -.- B1[USB / SFTP / data diode]
    C -.- C1[skopeo copy → Harbor]
    D -.- D1[kustomize image overrides<br/>OR Helm values]

    style A fill:#cce5ff
    style B fill:#fff5d6
    style C fill:#d6f5d6
    style D fill:#ffe0cc
```

Independiente de la distribución (Kubeflow manifests, Charmed Kubeflow, deployKF),
todas siguen este patrón. Cambian las herramientas, no el flujo.

## Tres opciones para tu curso

| Opción | Pros | Contras |
|---|---|---|
| **Manifests + kustomize image overrides** | Control total, vendor-neutral | Trabajo manual de mirror para ~80 imágenes |
| **Charmed Kubeflow (Canonical)** | Helper scripts oficiales, Juju operators | Lock-in a Juju + Canonical |
| **deployKF** | Optimizado air-gapped, `<tool>.images` overrides | Comunidad pequeña |

Para tu curso recomiendo **enseñar las 3** y dejar que el alumno elija según su empresa.

## Toolkit estándar

```mermaid
flowchart TB
    subgraph TOOLS["Herramientas air-gapped"]
        SK[skopeo<br/>copy entre registries]
        HR[Harbor<br/>registry empresarial]
        DC[docker / podman<br/>pull/save/load]
        TR[Trivy<br/>CVE scanning]
        CO[cosign<br/>firma de imágenes]
        OR[ORAS<br/>OCI artifacts]
    end

    SK -->|"online → offline"| HR
    HR --> TR
    HR --> CO
    DC -->|"alternativa"| HR
    OR -->|"Helm charts as OCI"| HR

    style TOOLS fill:#e6f3ff
```

| Herramienta | Para qué | Por qué importa |
|---|---|---|
| **skopeo** | `skopeo copy docker://src docker://dst` | No requiere docker daemon, paraleliza, mantiene metadata |
| **Harbor** | Registry empresarial con UI, RBAC, scanning | Es el "GitHub para imágenes" de tu cluster |
| **Trivy** | Scan de CVEs en imágenes mirroreadas | Compliance: nada entra al air-gap sin scan |
| **cosign** | Sigmstore signatures | Cadena de confianza: ¿esta imagen es la oficial? |
| **ORAS** | Push Helm charts y artifacts genéricos a Harbor | Charts también pueden vivir en Harbor (no GitHub) |

## Ejemplo concreto: Charmed Kubeflow (CKF) air-gapped

Charmed Kubeflow es la distribución oficial de Canonical. Trae **scripts helper**
para air-gapped — es el camino más rápido si no quieres hacer tú el tooling.

### Fase 1: Generar artefactos (en máquina con internet)

```bash
# Clonar bundle
git clone https://github.com/canonical/bundle-kubeflow.git
cd bundle-kubeflow/scripts/airgapped

# Pre-requisitos
pip3 install -r requirements.txt
sudo apt install pigz
sudo snap install docker yq jq

# Listar todas las imágenes del bundle CKF (ej: 1.8 stable)
./scripts/airgapped/get-all-images.sh \
  releases/1.8/stable/kubeflow/bundle.yaml > images.txt

# Pull al cache local
python3 scripts/airgapped/save-images-to-cache.py images.txt

# Re-tag con dominio del registry interno
python3 scripts/airgapped/retag-images-to-cache.py \
  --new-registry=harbor.airgap.local images.txt

# Empaquetar a tar.gz
python3 scripts/airgapped/save-images-to-tar.py retagged-images.txt
# → genera images.tar.gz (~10-20 GB)

# Empaquetar charms (Juju operators)
BUNDLE_PATH=releases/1.8/stable/kubeflow/bundle.yaml
python3 scripts/airgapped/save-charms-to-tar.py $BUNDLE_PATH
# → genera charms.tar.gz
```

### Fase 2: Transfer offline

```mermaid
flowchart LR
    A[Máquina online] -->|"images.tar.gz<br/>charms.tar.gz<br/>retagged-images.txt"| B[Medio físico]
    B -->|"USB / disco / data diode"| C[Máquina air-gapped]

    style A fill:#cce5ff
    style B fill:#fff5d6
    style C fill:#ffcccc
```

Para entornos con compliance fuerte, el transfer pasa por una **DMZ con scanning**
(antivirus + Trivy + integrity check) antes de tocar el air-gap.

### Fase 3: Cargar al registry interno

```bash
# En la máquina air-gapped
mkdir charms images
tar -xzvf charms.tar.gz --directory charms
tar -xzvf images.tar.gz --directory images

# Cargar imágenes al docker daemon local
for img in images/*.tar; do
  docker load < $img
done

# Push al registry interno (Harbor)
python3 scripts/airgapped/push-images-to-registry.py retagged-images.txt

# Importar también las imágenes base de Juju (charms)
docker pull docker.io/jujusolutions/charm-base:ubuntu-20.04
docker pull docker.io/jujusolutions/charm-base:ubuntu-22.04
docker tag docker.io/jujusolutions/charm-base:ubuntu-20.04 \
  harbor.airgap.local/jujusolutions/charm-base:ubuntu-20.04
docker push harbor.airgap.local/jujusolutions/charm-base:ubuntu-20.04
# (idem para 22.04)
```

### Fase 4: Deploy CKF

```bash
# Setup Juju en air-gapped (ver docs Juju)
juju bootstrap microk8s
juju add-model kubeflow

# Ejecutar el script de deploy
bash deploy-1.8.sh
```

### Configuración de gateway (importante)

Si el cluster no tiene LoadBalancer (típico on-prem con MetalLB no instalado),
cambia el service type:

```bash
# En deploy-1.8.sh, cambia:
juju deploy --trust ./$(charm istio-gateway) istio-ingressgateway \
  --config kind=ingress \
  --config proxy-image=$(img istio/proxyv2) \
  --config gateway_service_type="NodePort"   # ← agregar esto
```

## Alternativa: manifests crudos + skopeo + kustomize

Si no quieres lock-in con Canonical/Juju:

### Listar imágenes de Kubeflow manifests

```bash
git clone -b v1.10.2 https://github.com/kubeflow/manifests.git
cd manifests
kubectl kustomize example | grep "image:" | sort -u | sed 's/.*image: //' > images.txt
# → ~80 imágenes
```

### Mirror con skopeo

```bash
REGISTRY=harbor.airgap.local
while read img; do
  src="docker://$img"
  dst="docker://$REGISTRY/${img#*/}"  # remueve dominio source
  echo "skopeo copy $src $dst"
  skopeo copy --multi-arch=all --src-tls-verify=true --dest-tls-verify=true \
    "$src" "$dst"
done < images.txt
```

### Reescribir manifests con kustomize image overrides

```yaml
# kustomization.yaml (overlay air-gapped)
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../example
images:
  - name: docker.io/istio/proxyv2
    newName: harbor.airgap.local/istio/proxyv2
    newTag: 1.22.1
  - name: gcr.io/ml-pipeline/api-server
    newName: harbor.airgap.local/ml-pipeline/api-server
    newTag: 2.5.0
  # ... resto de imágenes
```

```bash
kubectl kustomize . | kubectl apply --server-side -f -
```

## Verificación post-install

Checklist que entregamos a alumnos:

```mermaid
flowchart TB
    Q1{¿Pods en Running?}
    Q2{¿Imágenes resuelven<br/>al registry interno?}
    Q3{¿Hay egress hacia<br/>internet?}
    Q4{¿Pipelines KFP<br/>completan SUCCESS?}
    Q5{¿KServe sirve<br/>InferenceService?}
    Q6{¿Auth Dex<br/>funcionando?}

    Q1 -- "no" --> F1[describe pod<br/>buscar ImagePullBackOff]
    Q1 -- "sí" --> Q2
    Q2 -- "no" --> F2[fix kustomize image<br/>o Juju config]
    Q2 -- "sí" --> Q3
    Q3 -- "sí" --> F3[problema! NO debe<br/>haber internet]
    Q3 -- "no" --> Q4
    Q4 -- "no" --> F4[ver MLMD logs,<br/>revisar S3 alternativo]
    Q4 -- "sí" --> Q5
    Q5 -- "no" --> F5[KServe storageUri<br/>al MinIO interno]
    Q5 -- "sí" --> Q6
    Q6 -- "no" --> F6[Dex config con OIDC<br/>al IDP interno]
    Q6 -- "sí" --> OK[✓ Air-gap operativo]

    classDef ok fill:#d6f5d6
    classDef fix fill:#ffe0cc
    classDef fail fill:#ffcccc
    class OK ok
    class F1,F2,F4,F5,F6 fix
    class F3 fail
```

## Hallazgos comunes (troubleshooting)

| Síntoma | Causa probable | Solución |
|---|---|---|
| `ImagePullBackOff` con DNS error | Cluster tiene DNS público hardcoded | Apuntar CoreDNS al DNS interno |
| `x509: certificate signed by unknown authority` | Registry con cert self-signed no confiado | Importar cert al containerd `/etc/containerd/certs.d/` |
| Pipelines fallan al subir artifacts | MinIO/S3 tiene endpoint externo | Configurar KFP `pipelineRoot: minio.internal` |
| Helm install cuelga | `helm` intenta resolver `helm.sh` (Hub público) | Usar OCI charts: `helm install oci://harbor/charts/...` |
| KServe no encuentra modelo | `storageUri` apunta a S3 público | Re-publicar modelo a MinIO/S3 interno |

## Reglas de oro para producción air-gapped

`★ ───────────────────────────────────────────────`
1. **Mirror todo**, no solo Kubeflow. Imágenes base (Ubuntu, alpine), Helm
   charts, modelos pre-entrenados, datasets de fine-tuning.
2. **Versiona el mirror**. Una imagen "latest" en el espejo no es la misma que
   "latest" upstream — reproducibilidad necesita tags fijos.
3. **Scan en CI**. Trivy + cosign verify ANTES de publicar a Harbor producción.
4. **Plan de actualización**. Cada release de Kubeflow trae imágenes nuevas →
   proceso recurrente de mirror, no one-shot.
5. **Caché de pip/conda interno**. Si tus pipelines hacen `pip install` en
   componentes, necesitas un PyPI mirror (devpi, Artifactory).
6. **Document network egress = 0**. Auditar con Falco o Cilium NetworkPolicy
   en `default deny`.
`─────────────────────────────────────────────────`

## Material para el curso

Lo que entregamos a alumnos en este módulo:

- Script `mirror.sh` que hace `skopeo copy` para todas las imágenes Kubeflow
  v1.10.2 (~80) al Harbor del lab.
- `kustomization.yaml` overlay con todos los image overrides ya listos.
- `docker-compose.yml` para correr Harbor + Trivy + cosign localmente como
  simulación del air-gap.
- Checklist de verificación post-install en formato Markdown.
- Demo en vivo: tomar un pipeline KFP, identificar las imágenes que necesita,
  mirrorearlas, ejecutar offline.

## Referencias

- [Charmed Kubeflow — air-gapped install](https://charmed-kubeflow.io/docs/install-airgapped) — fuente de este doc
- [Kubeflow Manifests](https://github.com/kubeflow/manifests) — instalación vendor-neutral
- [deployKF — Air-gapped Clusters and Private Registries](https://www.deploykf.org/guides/platform/offline/)
- [Harbor docs](https://goharbor.io/docs/)
- [skopeo](https://github.com/containers/skopeo)
- [HPE Ezmeral — Kubeflow in an Air-Gapped Environment](https://docs.ezmeral.hpe.com/runtime-enterprise/52/reference/kubernetes/kubernetes-administrator/kubeflow/Kubeflow_in_an_AirGapped_Environment.html)
- [Mirroring images for offline K8s clusters](https://oneuptime.com/blog/post/2026-01-19-kubernetes-mirror-images-offline/view)
