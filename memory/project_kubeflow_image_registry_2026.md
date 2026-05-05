---
name: Kubeflow image registry — estado 2026 y estrategia para curso on-prem
description: Hallazgos sobre el problema de imágenes en gcr.io/ml-pipeline (deprecated), versiones actuales de Kubeflow, y estrategia recomendada para producción on-premise/air-gapped.
type: project
originSessionId: 402ad9a2-dc48-42d6-8f33-db8503dad54a
---
Hallazgos críticos sobre el estado del ecosistema Kubeflow en mayo 2026, descubiertos durante la instalación local con Kubeflow 1.9.0. **Material clave para el curso on-premise**.

## Problema raíz: registry gcr.io/ml-pipeline en sunset

- Google **deprecó `gcr.io/ml-pipeline/`** durante 2025. Las imágenes (frontend, api-server, persistence-agent, etc.) ya no están disponibles en ese path.
- `curl gcr.io/v2/ml-pipeline/frontend/tags/list` devuelve `{"tags":[]}` → repositorio vacío.
- Manifests de Kubeflow v1.9.0 NO fueron actualizados antes del sunset → instalaciones nuevas se rompen out-of-the-box.
- **Issue #11600 en kubeflow/pipelines** confirma el problema. Cerrado pero sin documentación clara de la migración. Issue similar #7904, #10856.

## Imágenes que SÍ funcionan (verificado con `crictl pull`)
- `mysql:8.0.26` desde Docker Hub
- `quay.io/argoproj/workflow-controller:v3.4.16`
- `minio/minio:RELEASE.2024-08-17T01-24-54Z`
- `nvcr.io/nvidia/cuda:13.0.0-base-ubuntu24.04`

## Imágenes que NO se pudieron resolver (requieren auth o ya no existen):
- `gcr.io/ml-pipeline/*` (deprecated)
- `ghcr.io/kubeflow/kfp/frontend:2.2.0` → 403 Forbidden
- `ghcr.io/kubeflow-pipelines/frontend:2.2.0` → 403 Forbidden
- `ghcr.io/kubeflow/kfp-frontend:2.2.0` → 403 Forbidden
- `quay.io/kubeflow/kfp-frontend:2.2.0` → 403 Forbidden

## Versiones actuales (mayo 2026)

Kubeflow cambió a **versionado calendar-based (Año.Mes.Parche)**:

| Versión | Fecha | Notas |
|---|---|---|
| **26.03** | mar 2026 | Última estable, calendar-based |
| v1.11.0 | dic 2025 | Pre-sunset semver |
| v1.10.2 | jul 2025 | LTS estable |
| v1.10.1 | may 2025 | LTS estable |
| v1.9.0 | 2024 | **2 versiones atrás, gcr.io ya retirado** |

**Recomendación curso**: instalar **v1.10.2** o **26.03** para evitar el problema. NO usar v1.9.0 con manifests originales.

KFP standalone latest: **v2.15.0** (vía `github.com/kubeflow/pipelines/manifests/kustomize/env/dev?ref=2.15.0`).

## Para curso on-premise/air-gapped — strategy recomendada

**Stack productivo enseñable:**
1. **Harbor** como private registry (Helm install, TLS, Trivy scanning)
2. **Skopeo** para mirroring desde registries upstream (`skopeo copy docker://gcr.io/... docker://harbor.local/...`)
3. **Kustomize image transformer** para reescribir paths: `images:` block en `kustomization.yaml` apunta a registry interno
4. **deployKF** (alternativa managed): tiene `<tool>.images` overrides nativos para offline; mejor experiencia que manifests crudos para air-gapped

**Lección de oro para el curso:** "Kubeflow on-prem requiere que TÚ controles el registry. Nunca asumas que los upstream registries seguirán existiendo. Mirror everything a Harbor desde día 1."

**Ejemplo de lab módulo**: tomar la lista de imágenes de Kubeflow (~80), mirroring con skopeo a Harbor local, instalar manifests con kustomize image overrides. Pesado pero realista.

## Recursos clave

- [kubeflow/manifests releases](https://github.com/kubeflow/manifests/releases)
- [Kubeflow 1.10 release notes](https://www.kubeflow.org/docs/kubeflow-platform/releases/kubeflow-1.10/)
- [KFP standalone install](https://www.kubeflow.org/docs/components/pipelines/operator-guides/installation/)
- [Issue #11600 - missing ml-pipeline images](https://github.com/kubeflow/pipelines/issues/11600)
- [Issue #1033 - kustomize image registry transformer](https://github.com/kubeflow/manifests/issues/1033)
- [deployKF air-gapped guide](https://www.deploykf.org/guides/platform/offline/)
- [HPE Ezmeral - Kubeflow Air-Gapped](https://docs.ezmeral.hpe.com/runtime-enterprise/52/reference/kubernetes/kubernetes-administrator/kubeflow/Kubeflow_in_an_AirGapped_Environment.html)

## Implicación para próxima sesión

Después de validar Notebook con GPU en este lab actual (con Kubeflow 1.9.0 sin KFP):
1. Considerar reinstalar con **v1.10.2** o **26.03** (siguen versiones más estables y con imágenes vivas)
2. Para enseñar producción real: dedicar módulo entero a **Harbor + skopeo mirroring** — es el patrón que enfrentarán en la empresa
3. Mostrar a alumnos el comando `skopeo list-tags` para detectar registries muertos antes de instalar
