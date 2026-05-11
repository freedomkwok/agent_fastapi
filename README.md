# agent_fastapi

FastAPI wrapper for `imp_agent_core` agents.

## Run locally

The app uses the same local A2A path as `imp_agent_core/agents/zep_agent/run_local.py`.
Configure the `imp_agent_core` environment first, then start the API:

```bash
uv sync --extra dev
uv run uvicorn agent_fastapi.main:app --reload --host 0.0.0.0 --port 8080
```

## Debug in VS Code

Use one of the configs in `.vscode/launch.json`:

- `Agent FastAPI: launch uvicorn` starts the API under the debugger.
- `Agent FastAPI: attach debugpy 5678` attaches to an already running debugpy listener.

For attach debugging, start the server first:

```bash
uv run --extra dev python -m debugpy --listen 5678 -m uvicorn agent_fastapi.main:app --reload --host 0.0.0.0 --port 8080
```

Then run `Agent FastAPI: attach debugpy 5678` from VS Code. Set breakpoints in
`agent_fastapi/main.py`, `agent_fastapi/zep_agent_runner.py`, or the linked
`../imp_agent_core/agents/zep_agent` files.

## Chat

If `graph_id` is omitted, the API uses `mirofish_53c089d117c649c7` by default.
Set `ZEP_AGENT_DEFAULT_GRAPH_ID` to change that default for the server process.

```bash
curl -X POST http://localhost:8080/chat \
  -H 'content-type: application/json' \
  -d '{
    "message": "韩立喜欢的人喜欢韩立吗？on graph mirofish_53c089d117c649c7",
    "graph_id": "mirofish_53c089d117c649c7"
  }'
```

## Docker image

Build from the parent `imp` directory because this service depends on sibling
packages (`imp_agent_core` and `llm_inference_core`):

```bash
cd /path/to/imp
docker build -f agent_fastapi/Dockerfile -t agent-fastapi:latest .
```

Tag and push for your registry:

```bash
docker tag agent-fastapi:latest <registry>/agent-fastapi:<tag>
docker push <registry>/agent-fastapi:<tag>
```

## Kubernetes

Update `agent_fastapi/k8s/deployment.yaml` with your pushed image name, then
apply the manifests:

```bash
kubectl apply -f agent_fastapi/k8s/configmap.example.yaml
kubectl apply -f agent_fastapi/k8s/secret.example.yaml
kubectl apply -f agent_fastapi/k8s/deployment.yaml
kubectl apply -f agent_fastapi/k8s/service.yaml
```

For real deployments, create the secret from your environment instead of using
the empty example values:

```bash
kubectl create secret generic agent-fastapi-secrets \
  --from-literal=OPENAI_API_KEY="$OPENAI_API_KEY" \
  --from-literal=ZEP_API_KEY="$ZEP_API_KEY"
```
