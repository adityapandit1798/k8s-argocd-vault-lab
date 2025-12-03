# Kubernetes + Argo CD + Vault Learning Lab

> A hands-on lab to learn **Kubernetes**, **GitOps with Argo CD**, and **secrets management with HashiCorp Vault** — all from your local machine using **KIND**.

> 💡 **Why KIND?**  
> KIND (Kubernetes in Docker) lets you run a real Kubernetes cluster on your laptop using Docker containers as "nodes". It’s perfect for learning because:
> - No cloud costs
> - Full Kubernetes API compliance
> - Fast cluster creation/deletion
> - Used by Kubernetes developers themselves!

---

## 🎯 Goals

1. ✅ **Learn Kubernetes** by deploying a real app with Deployments, Services, etc.
2. ✅ **Understand GitOps** — using **Argo CD** to sync your cluster from Git
3. ✅ **Secure secrets** using **HashiCorp Vault** (no hardcoded secrets in manifests or Git!)

> 🔐 **Why Vault?**  
> Kubernetes Secrets are **base64-encoded, not encrypted**, and stored in etcd.  
> Vault encrypts secrets at rest, enforces access policies, and provides audit logs.

---

## 🛠️ Tech Stack

- **App**: Python Flask (`Hello World` + `/health`)
- **Container**: Docker (for packaging the app)
- **Kubernetes**: [`kind`](https://kind.sigs.k8s.io/) (local cluster)
- **GitOps**: [Argo CD](https://argo-cd.readthedocs.io/) (declarative sync from Git)
- **Secrets**: HashiCorp Vault (secure, dynamic secret injection)
- **Host**: Ubuntu VM (local or cloud)

---

## 🚀 Step-by-Step Setup

### 1. Create Flask App & Docker Image

> 🧠 **Why a Flask app?**  
> It’s simple, stateless, has clear HTTP endpoints, and uses environment variables — perfect for learning secret injection later.

**App code** (`app/app.py`):
```python
from flask import Flask
import os
app = Flask(__name__)

@app.route('/')
def hello():
    # Reads ENV from environment — will later come from Vault!
    return f"Hello from Flask! Environment: {os.getenv('ENV', 'dev')}"

@app.route('/health')
def health():
    return {"status": "ok"}, 200

if __name__ == '__main__':
    # Listen on all interfaces (required in containers)
    app.run(host='0.0.0.0', port=8080)
```

**Dockerfile** (`app/Dockerfile`):
```dockerfile
FROM python:3.11-slim          # Small base image
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
CMD ["python", "app.py"]       # Run the app
```

**Build & push**:
```bash
cd app
docker build -t panditaditya1798/argo-k8s:v1 .
docker push panditaditya1798/argo-k8s:v1
```

> 🔐 **Never commit secrets!** This image has no secrets yet — we’ll inject them later via Vault.

---

### 2. Create Local Kubernetes Cluster with KIND

> 🧠 **Why KIND over Minikube/EKS?**  
> - KIND uses Docker (you already have it)
> - Faster startup
> - Better for CI/testing
> - Multi-node support (though we use single-node here)

```bash
# Install KIND (requires Go 1.17+)
go install sigs.k8s.io/kind@v0.30.0

# Create a cluster named "argocd-lab"
kind create cluster --name argocd-lab

# Verify kubectl is talking to the right cluster
kubectl cluster-info --context kind-argocd-lab
kubectl get nodes  # Should show 1 control-plane node
```

---

### 3. Install Argo CD

> 🧠 **What is Argo CD?**  
> Argo CD is a **GitOps continuous delivery tool** for Kubernetes.  
> It watches your Git repo and **automatically syncs** your cluster to match the desired state in Git.

```bash
# Create namespace for Argo CD
kubectl create namespace argocd

# Install Argo CD (official manifest)
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

> ⏳ Wait for all pods to be `Running`:
```bash
kubectl -n argocd get pods -w
```

Get the **initial admin password** (auto-generated):
```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

**Port-forward the UI** (run in one terminal and leave it running):
```bash
# --address 0.0.0.0 allows access from your laptop (not just localhost)
kubectl port-forward --address 0.0.0.0 svc/argocd-server -n argocd 8081:80
```

> 🌐 **Access UI at**: `http://<VM_IP>:8081`  
> - **Username**: `admin`  
> - **Password**: `<from command above>`

> 💡 **Why port 80 (not 443)?**  
> Argo CD’s dev setup serves HTTP on port 80 via `port-forward`, avoiding TLS cert errors.

---

### 4. Deploy App via GitOps (Argo CD)

> 🧠 **GitOps Principle**:  
> **Git is the single source of truth**. Any change in Git → Argo CD syncs it to the cluster.  
> No manual `kubectl apply`!

#### Manifests (`k8s/`)

**`k8s/deployment.yaml`**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flask-demo
spec:
  replicas: 2
  selector:
    matchLabels:
      app: flask-demo
  template:
    metadata:
      labels:
        app: flask-demo
    spec:
      containers:
      - name: flask
        image: panditaditya1798/argo-k8s:v1
        ports:
        - containerPort: 8080
        env:
        - name: ENV
          value: "k8s-argocd"   # Will later be replaced by Vault!
```

**`k8s/service.yaml`**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: flask-demo-svc
spec:
  selector:
    app: flask-demo          # Matches pod labels
  ports:
    - protocol: TCP
      port: 80               # Service port
      targetPort: 8080       # Pod port
  type: LoadBalancer         # In KIND, this stays in <pending> — use port-forward to access
```

**Commit & push to Git**:
```bash
git add k8s/
git commit -m "feat: add k8s manifests for Flask app"
git push origin main
```

> 🧠 **Why commit to Git?**  
> Argo CD **only deploys from Git**. No Git = no deployment!

#### Create Argo CD Application (via UI)

In Argo CD UI (`http://<VM_IP>:8081`):

| Field | Value | **Why?** |
|------|--------|--------|
| App Name | `flask-demo` | Human-readable name |
| Project | `default` | Built-in project |
| Sync Policy | **Manual** | Safer for learning (you control syncs) |
| Repository URL | `https://github.com/adityapandit1798/k8s-argocd-vault-lab.git` | Your repo |
| Path | `k8s` | Folder containing YAML manifests |
| Cluster | `https://kubernetes.default.svc` | Your local KIND cluster |
| Namespace | `default` | Where to deploy your app |

✅ Click **Create** → **Sync** → Watch your app deploy!

---

### 5. Verify Deployment

```bash
# Check pods are running
kubectl get pods -l app=flask-demo

# Check service exists
kubectl get svc flask-demo-svc

# Access app via port-forward (since LoadBalancer = <pending> in KIND)
kubectl port-forward svc/flask-demo-svc 8082:80
```

In another terminal:
```bash
curl http://localhost:8082
# Output: Hello from Flask! Environment: k8s-argocd
```

✅ **Success!** Your app is deployed via **GitOps**!

---

## 🔒 Vault Integration: Secure Secret Injection

> 🧠 **Problem**:  
> The `ENV` value is hardcoded in `deployment.yaml` — **not secure!**  
> We want to inject `DB_PASSWORD` and other secrets **at runtime** from Vault.

### How Vault + Kubernetes Works (High-Level)

1. **Vault runs in your cluster** (in `vault` namespace)
2. Your app uses a **Kubernetes ServiceAccount** (`flask-app`)
3. A **Vault Agent sidecar** is auto-injected into your pod
4. The sidecar:
   - Authenticates to Vault using the pod’s ServiceAccount token
   - Fetches secrets from Vault
   - Writes them to a **shared in-memory volume** (`/vault/secrets/`)
5. Your app reads secrets from that file at startup

> 🔐 **Security Benefits**:
> - No secrets in Git or manifests
> - Secrets never touch disk (`emptyDir` with `medium: Memory`)
> - Least-privilege access (Vault policies)
> - Full audit trail

### Steps We Took (Recap)

1. **Deploy Vault in dev mode** (for learning):
   ```yaml
   args:
   - "server"
   - "-dev"                     # Auto-unsealed, in-memory storage
   - "-dev-root-token-id=root"  # Insecure but easy for labs
   - "-dev-listen-address=0.0.0.0:8200"
   ```
2. **Enable Kubernetes auth in Vault**:
   ```bash
   vault auth enable kubernetes
   vault write auth/kubernetes/config \
       kubernetes_host="https://kubernetes.default.svc" \
       kubernetes_ca_cert=@/tmp/ca.crt
   ```
   → This lets Vault **trust your KIND cluster**.
3. **Create Vault policy + role**:
   ```hcl
   # Only allow reading secret/data/flask-app
   path "secret/data/flask-app" { capabilities = ["read"] }
   ```
   ```bash
   vault write auth/kubernetes/role/flask-app \
       bound_service_account_names=flask-app \
       bound_service_account_namespaces=default \
       policies=flask-app-policy
   ```
4. **Store secret in Vault**:
   ```bash
   vault kv put secret/flask-app DB_PASSWORD=supersecretpass ENV=k8s-vault
   ```
5. **Update Deployment with Vault annotations**:
   ```yaml
   spec:
     serviceAccountName: flask-app  # ← Critical!
     template:
       metadata:
         annotations:
           vault.hashicorp.com/agent-inject: "true"
           vault.hashicorp.com/role: "flask-app"
           vault.hashicorp.com/agent-inject-secret-flask.txt: "secret/data/flask-app"
           vault.hashicorp.com/agent-inject-template-flask.txt: |
             {{- with secret "secret/data/flask-app" -}}
             export DB_PASSWORD="{{ .Data.data.DB_PASSWORD }}"
             export ENV="{{ .Data.data.ENV }}"
             {{- end }}
       spec:
         containers:
         - volumeMounts:
           - name: vault-secrets
             mountPath: /vault/secrets
         volumes:
         - name: vault-secrets
           emptyDir:
             medium: Memory  # ← Secrets stay in RAM only!
   ```
6. **Update Flask app to read secrets**:
   ```python
   secrets_file = '/vault/secrets/flask.txt'
   if os.path.exists(secrets_file):
       with open(secrets_file) as f:
           for line in f:
               if line.startswith('export '):
                   key, val = line.replace('export ', '').strip().split('=', 1)
                   os.environ[key] = val.strip('"')
   ```
7. **Rebuild image (`:v2`), push, commit, sync via Argo CD**

✅ Result:
```bash
curl http://localhost:8082
# Output: Hello from Flask! Environment: k8s-vault | DB: supersecretpass
```

> 🎉 **No secrets in Git!** All secrets come from Vault at runtime.

---

## 📚 What’s Next?

### 🔒 Phase 2: Vault Hardening
- Switch from `-dev` mode → **production Vault** (HA, TLS, persistent storage)
- Use **Vault CSI Provider** (alternative to sidecar)
- Try **dynamic database credentials**

### 🌐 Phase 3: Advanced k8s Features
- **ConfigMaps** (for non-secret config)
- **Liveness/Readiness Probes** (health checks)
- **Ingress with NGINX** (HTTP routing)
- **RBAC** (least-privilege pod permissions)

### 🔄 Phase 4: Argo CD Best Practices
- **Auto-sync** (enable in App settings)
- **App-of-Apps** (manage multiple apps)
- **Kustomize/Helm** instead of raw YAML

---

## 💡 Tips

- Always run `kubectl port-forward` in its own terminal.
- Use `--address 0.0.0.0` to allow access from your laptop.
- **Never store secrets in Git** — always use Vault or similar.
- KIND is for **learning** — use EKS/GKE/AKS for production.
- **Vault Agent Sidecar** is just one pattern — **CSI Secrets Provider** is another (mounts secrets as files without sidecar).

---

## 🙌 Done By
Aditya Pandit  
GitHub: [@adityapandit1798](https://github.com/adityapandit1798)
