# Kubernetes + Argo CD + Vault Learning Lab

> A hands-on lab to learn **Kubernetes**, **GitOps with Argo CD**, and eventually **secrets management with HashiCorp Vault** — all from your local machine using **KIND**.

---

## 🎯 Goals

1. ✅ Learn Kubernetes basics by deploying a real app.
2. ✅ Understand **GitOps** using **Argo CD**.
3. 🔜 Secure secrets with **HashiCorp Vault** (next phase!).

---

## 🛠️ Tech Stack

- **App**: Python Flask (`Hello World` + `/health`)
- **Container**: Docker
- **Kubernetes**: [`kind`](https://kind.sigs.k8s.io/) (Kubernetes in Docker)
- **GitOps**: [Argo CD](https://argo-cd.readthedocs.io/)
- **Host**: Ubuntu VM (local or cloud)

---

## 🚀 Step-by-Step Setup

### 1. Create Flask App & Docker Image

App code:
```python
# app/app.py
from flask import Flask
import os
app = Flask(__name__)
@app.route('/')
def hello():
    return f"Hello from Flask! Environment: {os.getenv('ENV', 'dev')}"
@app.route('/health')
def health():
    return {"status": "ok"}, 200
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

Dockerfile:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
CMD ["python", "app.py"]
```

Build & push:
```bash
cd app
docker build -t panditaditya1798/argo-k8s:v1 .
docker push panditaditya1798/argo-k8s:v1
```

> 🔐 **Never commit secrets!** We’ll use Vault later.

---

### 2. Create Local Kubernetes Cluster with KIND

Install KIND (if not done):
```bash
go install sigs.k8s.io/kind@v0.30.0
```

Create cluster:
```bash
kind create cluster --name argocd-lab
kubectl cluster-info --context kind-argocd-lab
```

Verify:
```bash
kubectl get nodes  # Should show 1 node
```

---

### 3. Install Argo CD

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

Wait for all pods to be `Running`:
```bash
kubectl -n argocd get pods -w
```

Get admin password:
```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

Port-forward UI (run in one terminal):
```bash
kubectl port-forward --address 0.0.0.0 svc/argocd-server -n argocd 8081:80
```

Access Argo CD UI at:
```
http://<VM_IP>:8081
```
> Replace `<VM_IP>` with your VM’s IP (e.g., `192.168.192.143`).

Login with:
- **Username**: `admin`
- **Password**: `<output from command above>`

---

### 4. Deploy App via GitOps (Argo CD)

#### Manifests (`k8s/`)

`k8s/deployment.yaml`:
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
          value: "k8s-argocd"
```

`k8s/service.yaml`:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: flask-demo-svc
spec:
  selector:
    app: flask-demo
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
  type: LoadBalancer
```

Commit & push:
```bash
git add k8s/
git commit -m "feat: add k8s manifests for Flask app"
git push origin main
```

#### Create Argo CD Application

In Argo CD UI (`http://<VM_IP>:8081`):

- **App Name**: `flask-demo`
- **Project**: `default`
- **Sync Policy**: Manual
- **Repository URL**: `https://github.com/adityapandit1798/k8s-argocd-vault-lab.git`
- **Revision**: `HEAD`
- **Path**: `k8s`
- **Cluster**: `https://kubernetes.default.svc`
- **Namespace**: `default`

Click **Create** → **Sync**.

✅ App deploys automatically from Git!

---

### 5. Verify Deployment

Check resources:
```bash
kubectl get pods -l app=flask-demo
kubectl get svc flask-demo-svc
```

Access app locally on VM:
```bash
kubectl port-forward svc/flask-demo-svc 8082:80
```

Then (in another terminal):
```bash
curl http://localhost:8082
# Output: Hello from Flask! Environment: k8s-argocd
```

Or access remotely via VM IP + NodePort (if needed).

---

## 📚 What’s Next?

### 🔒 Phase 2: Integrate HashiCorp Vault
- Deploy Vault in KIND
- Store secrets (e.g., `DB_PASSWORD`)
- Inject into Flask app **without hardcoding**
- Use **Vault Agent Sidecar** or **CSI Secrets Provider**

### 🌐 Phase 3: Advanced k8s Features
- ConfigMaps & Secrets
- Liveness/Readiness Probes
- Ingress (with NGINX)
- RBAC, Namespaces, Resource Quotas

### 🔄 Phase 4: Auto-Sync & App-of-Apps
- Enable **auto-sync** in Argo CD
- Manage **multiple apps** with **AppProject**
- Use **Kustomize** or **Helm**

---

## 💡 Tips

- Always keep `kubectl port-forward` running in its own terminal.
- Use `--address 0.0.0.0` to allow external access from your laptop.
- Never store secrets in Git — Vault is the answer!
- KIND is perfect for local learning; switch to EKS/GKE later for production practice.

---

## 🙌 Done By
Aditya Pandit  
GitHub: [@adityapandit1798](https://github.com/adityapandit1798)

> “GitOps is not just a tool — it’s a workflow.” 🔄
```
