# GitOps with Argo CD

## Overview

Argo CD watches the Git repository and reconciles the cluster to
match the desired state declared in `charts/modelops-serving` with
`values-prod.yaml`.

## Repository Structure
charts/
└── modelops-serving/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
├── ci/
└── templates/
gitops/
└── argocd-app.yaml

text

## Sync Policy

| Setting | Value | Effect |
|---------|-------|--------|
| `automated.prune` | `true` | Resources removed from Git are deleted from the cluster |
| `automated.selfHeal` | `true` | Manual cluster changes are reverted to match Git |
| `syncOptions.CreateNamespace` | `false` | The namespace is managed separately |
| `syncOptions.PruneLast` | `true` | Pruning happens after the sync completes |

## Release Workflow

1. Developer merges a pull request to `main`.
2. CI validates the Helm chart (`helm lint`, `helm template`, `kubeconform`).
3. A new image is built and tagged with the commit SHA.
4. `values-prod.yaml` is updated with the new image tag and committed.
5. Argo CD detects the commit and reconciles the cluster.
6. Health checks confirm the release.

## Rollback

```bash
# Option 1: Git revert (recommended)
git revert <commit-sha> --no-edit
git push origin main

# Option 2: Argo CD rollback
argocd app rollback modelops-serving <history-id>
Sync vs. Health
Status	Meaning
Synced	Cluster matches Git
OutOfSync	Cluster differs from Git
Healthy	Resources are working
Degraded	Resources are broken
Progressing	Resources are being updated
An application can be Synced but Degraded (bad config in Git)
or OutOfSync but Healthy (manual cluster change not yet reconciled).

Verified Drills
The following drills were executed successfully on 2026-10-13:

Drift correction (selfHeal)
bash
kubectl scale deployment modelops-serving -n modelops --replicas=0
# After ~30 seconds, Argo CD reverted it to 1
kubectl get deployment modelops-serving -n modelops
# NAME               READY   UP-TO-DATE   AVAILABLE
# modelops-serving   1/1     1            1
Prune (recreate deleted resources)
bash
kubectl delete configmap modelops-serving-config -n modelops
# After ~30 seconds, Argo CD recreated it
kubectl get configmap modelops-serving-config -n modelops
# NAME                      DATA   AGE
# modelops-serving-config   5      69s
Git-driven release
Changed replicaCount: 1 → 2 in values-prod.yaml, committed,
pushed. Argo CD reconciled within 3 minutes. Deployment scaled to 2/2.

Rollback via git revert
Reverted the replica-count commit. Argo CD reconciled back to 1 replica.

Local Access
bash
# Argo CD UI
kubectl port-forward svc/argocd-server -n argocd 8090:443
# https://localhost:8090, admin / <initial password>

# Serving API
kubectl port-forward -n modelops svc/modelops-serving 8081:80
curl http://127.0.0.1:8081/health/ready
Limitations
Argo CD runs in the same kind cluster it manages. In production,
Argo CD would run in a separate management cluster.

The hostPath PV is node-local; replicaCount is limited to 1
because the ReadOnlyMany access mode does not reliably share
across nodes on kind.

The kind worker nodes' networking (CNI/kube-proxy) is unstable
under WSL 2. To work around this, the control-plane node's
NoSchedule taint was removed so pods can schedule on it.

Secrets are not managed by Argo CD. Use Sealed Secrets or
External Secrets Operator in production.
MDEOF