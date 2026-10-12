# Kubernetes Deployment

## Cluster

- **Tool:** kind v0.30.0
- **Cluster name:** `modelops`
- **Nodes:** 1 control-plane, 2 workers
- **Kubernetes version:** v1.32.0
- **Context:** `kind-modelops`

Create the cluster:

```bash
kind create cluster --config k8s/kind-config.yaml
Delete the cluster:

bash
kind delete cluster --name modelops
Why kindest/node:v1.32.0 is pinned: the v1.34.x node image has a
known CNI bootstrap bug on Docker Desktop for WSL 2. The control-plane
node stays NotReady with the error
Network plugin returns error: cni plugin not initialized, while the
worker nodes reach Ready. The v1.32.0 image does not have the bug.
Track the upstream kind project before upgrading the node image.

Resources
Resource	File	Purpose
Namespace	k8s/namespace.yaml	Isolates ModelOps resources
ConfigMap	k8s/configmap.yaml	Non-sensitive configuration
Secret	kubectl create secret (not committed)	Sensitive values
PersistentVolume	k8s/pv-model.yaml	Model artifact hostPath storage
PersistentVolumeClaim	k8s/pvc-model.yaml	Binds to the PV
Deployment	k8s/deployment.yaml	Serving API pods
Service	k8s/service.yaml	ClusterIP for internal access
Apply order matters: namespace first, then ConfigMap, Secret, PV, PVC,
Deployment, and Service.

bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/pv-model.yaml
kubectl apply -f k8s/pvc-model.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
Probes
Probe	Endpoint	Purpose	Budget
Startup	/health/live	Allows slow model loading	5s initial + 60 × 5s
Liveness	/health/live	Restarts the pod on hang	10s initial + 3 failures × 15s
Readiness	/health/ready	Removes pod from Service until model ready	5s initial + 3 failures × 10s
Why three probes: the startup probe isolates the "model loading"
phase from the "steady-state" phase. Without it, a slow load would
trigger the liveness probe's restart logic before the app finishes
initialising. The readiness probe gates traffic — a pod that cannot
load its model is alive but not useful, and Kubernetes removes it from
the Service endpoints until /health/ready returns 200.

The startup probe's 5-minute budget (60 × 5s) is deliberately generous
for local development. In production with a fast model registry you
would tighten this to 60–90 seconds.

Resource Limits
Resource	Request	Limit
CPU	250m	500m
Memory	256Mi	512Mi
Requests are what the scheduler uses to place pods; limits are the hard
cap. These values match the Terraform Docker container from Phase 6
(cpu_shares=512 ≈ 500m, memory=512 MB ≈ 512Mi).

Model Artifact Handling
The model is mounted read-only from a hostPath PersistentVolume at
/models on each node. For kind, the file must be copied into every
node before the PV can be bound:

bash
for node in modelops-control-plane modelops-worker modelops-worker2; do
  docker exec "$node" mkdir -p /models
  docker cp models/gradient_boosting.joblib "$node:/models/gradient_boosting.joblib"
done
The PVC binds to the PV, and the Deployment mounts it at
/app/models:ro inside the pod.

This is a local-only pattern. hostPath ties the model to specific
nodes. If a pod is scheduled on a node that does not have the file, the
mount will fail. In production, use a CSI-backed PVC (AWS EBS, GCE PD,
Ceph) or an object store (S3, GCS) with an init container that fetches
the artifact from the registry.

Configuration vs Secrets
The ConfigMap (modelops-config) carries non-sensitive runtime
configuration:

Key	Phase 7 value	Notes
MODELOPS_MODEL_URI	"" (empty)	MLflow not deployed in-cluster; skip registry
MODELOPS_MODEL_NAME	modelops-housing-regressor	Used for metadata only
MODELOPS_LOCAL_ARTIFACT_FALLBACK	/app/models/gradient_boosting.joblib	The mounted model
MODELOPS_MLFLOW_TRACKING_URI	"" (empty)	Disables entrypoint's MLflow wait
LOG_LEVEL	INFO	
Both URIs are empty in Phase 7 because MLflow is not deployed in the
cluster. The serving app skips the registry entirely and loads from the
local fallback. Phase 8 will deploy MLflow in-cluster and populate these
values.

The Secret (modelops-secrets) carries sensitive values, created at
apply time from a git-ignored file:

bash
kubectl create secret generic modelops-secrets \
  --from-env-file=k8s/secret.env \
  --namespace=modelops
Neither the Secret YAML nor k8s/secret.env is committed.
k8s/secret.env is in .gitignore. The Deployment consumes the Secret
via envFrom.secretRef.

Base64 is not encryption. Kubernetes Secrets are base64-encoded, not
encrypted. In production, use Sealed Secrets, External Secrets Operator,
or a cloud KMS. For local development, base64 plus the fact that the
value never enters Git is acceptable.

Working with the Deployment
Port-forward to the Service:

bash
kubectl port-forward -n modelops svc/modelops-serving 8081:80
Use port 8081 to avoid the kind cluster's NodePort mapping on 8080.

Hit the endpoints:

bash
curl -s http://127.0.0.1:8081/health/live
curl -s http://127.0.0.1:8081/health/ready
curl -s http://127.0.0.1:8081/v1/model/info
curl -s -X POST http://127.0.0.1:8081/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"features": [8.3252, 41.0, 6.9841, 1.0238, 322.0, 2.5556, 37.88, -122.23]}'
Scale the Deployment:

bash
kubectl scale deployment/modelops-serving --replicas=3 -n modelops
kubectl rollout status deployment/modelops-serving -n modelops
Inspect the rollouts:

bash
kubectl rollout history deployment/modelops-serving -n modelops
kubectl get pods -n modelops -l app=modelops-serving -o wide
The -o wide flag shows which node each pod is scheduled on, useful for
verifying that the scheduler spreads replicas across nodes.

Failure Drills
Four failure drills were performed to validate the deployment's
behaviour under fault conditions. Each drill has a stated outcome and a
recovery procedure.

Drill 1 — Invalid image tag
bash
kubectl set image deployment/modelops-serving \
  serving=modelops-serving:nonexistent-tag \
  -n modelops
Observed behaviour: the Deployment creates a new pod that enters
ImagePullBackOff. With maxSurge: 1, maxUnavailable: 0, the three
existing pods keep running. The rollout is stalled, but the Service is
unaffected and all three original pods continue to serve traffic.

Recovery:

bash
kubectl set image deployment/modelops-serving \
  serving=modelops-serving:<known-good-sha> \
  -n modelops
kubectl rollout status deployment/modelops-serving -n modelops
Lesson: the rolling-update strategy prevents a bad image from taking
down the running service. maxUnavailable: 0 is the guarantee.

Drill 2 — Pod deletion (self-healing)
bash
POD=$(kubectl get pods -n modelops -l app=modelops-serving \
  -o jsonpath='{.items[0].metadata.name}')
kubectl delete pod "$POD" -n modelops
Observed behaviour: the pod enters Terminating and is replaced by
a new pod created by the ReplicaSet controller within ~40 seconds. At
no point do fewer than two pods serve traffic, because the deletion
only affects one of the three replicas.

Lesson: the ReplicaSet reconciles actual state to desired state.
Kubernetes does not need the pod to be restarted — it deletes the old
one and creates a new one.

Drill 3 — Read-only model mount
Attempt to rename the model file inside a pod:

bash
POD=$(kubectl get pods -n modelops -l app=modelops-serving \
  -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n modelops "$POD" -- \
  sh -c 'mv /app/models/gradient_boosting.joblib /app/models/gradient_boosting.joblib.bak'
Observed behaviour: the command fails with

text
mv: cannot move '...' to '...': Read-only file system
The pod runs as UID 1001 and the file on disk is owned by UID 1000 on
the node. Either of these alone would be a soft constraint. The kernel
enforces the read-only constraint at the mount boundary, so the
container cannot mutate the model file under any circumstances.

Lesson: defense in depth. Non-root user and read-only mount. Even
a compromised process inside the container cannot persist a modified
model.

Drill 4 — Rolling update without downtime
bash
# Build and load a new image
./scripts/build_image.sh
kind load docker-image modelops-serving:<new-sha> --name modelops

# Update the Deployment
kubectl set image deployment/modelops-serving \
  serving=modelops-serving:<new-sha> \
  -n modelops

kubectl rollout status deployment/modelops-serving -n modelops
Observed behaviour: the Deployment creates one new pod (surge),
waits for it to become Ready (readiness probe passes), then terminates
one old pod, then repeats. At no point are fewer than 3 endpoints
available in the Service.

Rollback caveat: kubectl rollout undo reverts to the immediately
preceding revision, not the last working revision. After the invalid-
image drill (Drill 1), the preceding revision was itself a deliberately
broken drill. Running kubectl rollout undo there pointed the
Deployment at the broken revision again. The correct recovery was
kubectl set image ... <known-good-tag> — or
kubectl rollout undo --to-revision=N with an explicit target.

This is exactly the class of problem that Phase 8's GitOps model
eliminates: the desired state is a Git commit, and "rollback" is a
git revert, which naturally points at a known-good commit.

CI
The k8s-validate job in .github/workflows/ci.yml runs on every PR
that touches k8s/** or infra/**:

Installs kubeconform v0.6.7

Runs kubeconform -strict -summary -ignore-missing-schemas on each
manifest file

It does not create a cluster or apply manifests. It validates schema
correctness only. Integration testing against a live kind cluster is
deferred to Phase 8 when Argo CD reconciles manifests against the
cluster.

The validation is scoped to the six Kubernetes manifests. The
k8s/kind-config.yaml file is a kind-specific config, not a Kubernetes
manifest, and is excluded from schema validation:

bash
kubeconform \
  -strict \
  -summary \
  -ignore-missing-schemas \
  k8s/namespace.yaml \
  k8s/configmap.yaml \
  k8s/pv-model.yaml \
  k8s/pvc-model.yaml \
  k8s/deployment.yaml \
  k8s/service.yaml
Teardown
bash
# Delete the modelops namespace (removes all namespaced resources)
kubectl delete namespace modelops

# Delete the entire cluster (releases all Docker resources)
kind delete cluster --name modelops
kubectl delete namespace modelops is the standard cleanup for a
single-tenant kind cluster. It removes the Deployment, Service,
ConfigMap, Secret, PVC, and any other namespaced resource. The
PersistentVolume is cluster-scoped, so it must be removed separately:

bash
kubectl delete pv model-artifacts-pv
Limitations
kind is not production. No highly available control plane, no
managed upgrades, no cloud integration, no multi-tenant isolation.

hostPath PV ties the model artifact to specific nodes. The file
must be present on every node the pod can schedule on. In a
multi-node cluster, this becomes a coordination problem.

MLflow is not deployed in-cluster. The serving app runs on the
local fallback model. Phase 8 will deploy MLflow as a Service and
populate the ConfigMap's registry URI.

Secrets are base64-encoded, not encrypted at rest. For local
development this is acceptable; for production use Sealed Secrets or
an external secrets manager.

No NetworkPolicy. All pods in the namespace can communicate
freely. Production would add NetworkPolicy resources to restrict
east-west traffic.

No resource quotas. A single Deployment with a single namespace
cannot starve others, but in a shared cluster you would add a
ResourceQuota and a LimitRange to the namespace.
MDEOF