# Kubernetes Deployment Strategies Demo

This repository provides a simplified demonstration of common Kubernetes deployment strategies:

* **Rolling Update**
* **Canary Deployment**
* **Blue-Green Deployment**

## Prerequisites

* **Kubernetes Cluster:** Minikube, Docker Desktop, or a cloud provider.
* **kubectl:** Kubernetes command-line tool.

## Project Structure
```
your-project-root/
├── deployment/
│   ├── deployment.yaml         # Initial deployment (version v1)
│   ├── service.yaml            # Service definition
│   ├── canary-deployment.yaml  # Canary deployment (version v2)
│   ├── blue-deployment.yaml    # Blue deployment (for blue-green)
│   └── green-deployment.yaml   # Green deployment (for blue-green)
```

## YAML Files

### `deployment.yaml` (Initial Deployment)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
        version: v1  
    spec:
      containers:
      - name: my-app
        image: your-image-repository/my-app:v1
        ports:
        - containerPort: 8080
```


### `service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app-service
spec:
  selector:
    app: my-app
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
  type: LoadBalancer # or NodePort if using Minikube/Docker Desktop
```

### `canary.yaml`

```yaml
# (Mostly the same as deployment.yaml, but change the following:)
  template:
    metadata:
      labels:
        app: my-app
        version: v2 
  replicas: 1  # Adjust for desired canary traffic percentage
```

### `blue.yaml`

```yaml
# (Same as deployment.yaml, but change the following:)
  template:
    metadata:
      labels:
        app: my-app
        version: blue 
```

### `green.yaml`

```yaml
# (Same as deployment.yaml, but change the following:)
  template:
    metadata:
      labels:
        app: my-app
        version: green 
```

## Deployment Strategies

### Rolling Update
- Apply Initial Deployment: `kubectl apply -f deployment.yaml -f service.yaml`
- Update Image/Configuration: Modify deployment.yaml (e.g., change image or version).
- Re-apply: `kubectl apply -f deployment.yaml`

## Canary Deployment
- Apply Initial Deployment: (Same as rolling update)
- Apply Canary Deployment: `kubectl apply -f canary-deployment.yaml`
- No changes are needed in `service.yaml`
- Monitor: Observe the performance of the canary version.
- Replace (Optional): If successful, scale up the canary and/or remove the initial deployment.

## Blue-Green Deployment
- Apply Blue Deployment: `kubectl apply -f blue-deployment.yaml`
- Switch Traffic:
    - Modify service.yaml to select version: `blue`
    ```yaml
    apiVersion: v1
    kind: Service
    metadata:
    name: my-app-service
    spec:
    selector:
        app: my-app
        version: blue   # Selector for blue deployment
    ports:
        - protocol: TCP
        port: 80
        targetPort: 8080
    type: LoadBalancer # or NodePort
    ```
    - `kubectl apply -f service.yaml`

- Apply Green Deployment: `kubectl apply -f green-deployment.yaml`
- Switch Traffic:
    - Modify service.yaml to select version: `green`.
        ```yaml
        apiVersion: v1
        kind: Service
        metadata:
        name: my-app-service
        spec:
        selector:
            app: my-app
            version: green  # Selector for green deployment
        ports:
            - protocol: TCP
            port: 80
            targetPort: 8080
        type: LoadBalancer # or NodePort
        ```    
    - `kubectl apply -f service.yaml`