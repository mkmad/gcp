# App Engine Deployment Example

This folder contains sample Flask apps ready to be deployed to Google App Engine and run locally using Docker Compose.

## Folder Structure for Multiple Apps

```
gcp/app-engine/
  app1/
    app.yaml
    app.py
    requirements.txt
    Dockerfile
    docker-compose.yml
    templates/
      index.html
  app2/
    app.yaml
    app.py
    requirements.txt
    Dockerfile
    docker-compose.yml
    templates/
      index.html
  ...
  README.md
```
- Each subfolder (e.g., `app1/`, `app2/`) is a separate App Engine service (app).
- Each has its own `app.yaml` (with a unique `service:` name).

---

## Local Development (Single App)

1. **Install Docker and Docker Compose** if you haven't already.
2. In the app directory, run:
   ```sh
   cd app1
   docker compose up --build
   ```
3. Visit [http://localhost:8080](http://localhost:8080) (or the port specified in `docker-compose.yml`).

Repeat for other apps (e.g., `app2` runs on port 8081 by default).

---

## Deploying Multiple Apps to Google App Engine

1. **Install the Google Cloud SDK** and authenticate:
   ```sh
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```
2. **Enable App Engine and deploy each app:**
   ```sh
   gcloud app create # Only once per project
   gcloud app deploy app1/app.yaml
   gcloud app deploy app2/app.yaml
   # Add more as needed
   ```
3. Each app will be available at:
   - Default service: `https://<project-id>.appspot.com/`
   - Other apps: `https://<service>-dot-<project-id>.appspot.com/`

---

## Cloning to a New Project (Zero Downtime)

To clone this setup to a new App Engine instance in a new GCP project **without downtime** on the current app:

1. **Create a new GCP project:**
   ```sh
   gcloud projects create NEW_PROJECT_ID
   gcloud config set project NEW_PROJECT_ID
   gcloud app create
   ```
2. **Copy all files from this folder** (`gcp/app-engine/`) to your new repo or directory.
3. **Deploy all apps to the new project:**
   ```sh
   gcloud app deploy app1/app.yaml
   gcloud app deploy app2/app.yaml
   # Add more as needed
   ```
4. **Test the new deployment** at the new App Engine URLs.
5. **Your current App Engine app remains running** in the old project with zero downtime.

---

## Notes
- You can update and deploy each app independently.
- For production, consider using a custom domain and traffic splitting for blue/green deployments if needed.
- This setup uses App Engine Standard. For Flexible, update `app.yaml` and Docker usage accordingly.
