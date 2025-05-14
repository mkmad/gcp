# Multi Environment POC

This project demonstrates a multi-environment setup using a single GCP project with Cloud Run and Cloud SQL.

## Architecture Overview

- Single GCP Project for all environments (dev, staging)
- Single Firebase/Identity Platform configuration
- PostgreSQL Cloud SQL instances for each environment
- Cloud Run services for each environment (frontend and backend)

## Project Structure

```
poc/
├── backend/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── contexts/
│   │   ├── App.js
│   │   └── firebase.js
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── infrastructure/
│   └── init.sql
├── scripts/
│   └── deploy.sh
└── README.md
``` 

## Setup Instructions

### 1. GCP Project Setup

```bash
# Set your project ID
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    sql-component.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com \
    identitytoolkit.googleapis.com
```

### 2. Create Cloud SQL Instances

```bash
# Create dev instance
gcloud sql instances create dev \
    --database-version=POSTGRES_13 \
    --tier=db-f1-micro \
    --region=us-central1

# Create staging instance
gcloud sql instances create staging \
    --database-version=POSTGRES_13 \
    --tier=db-f1-micro \
    --region=us-central1

# Create databases and users for each environment
for ENV in dev staging; do
    # Create database
    gcloud sql databases create app_db --instance=$ENV

    # Create user and store password in Secret Manager
    DB_PASS=$(openssl rand -base64 24)
    gcloud sql users create app_user \
        --instance=$ENV \
        --password=$DB_PASS

    # Store database credentials in Secret Manager
    gcloud secrets create db-credentials-$ENV --replication-policy="automatic"
    echo '{
        "DB_USER": "app_user",
        "DB_PASS": "'$DB_PASS'",
        "DB_NAME": "app_db",
        "DB_HOST": "'$ENV'.${PROJECT_ID}.cloudsql.google.com"
    }' | gcloud secrets versions add db-credentials-$ENV --data-file=-
done
```

### 3. Setup Firebase/Identity Platform

1. Go to Firebase Console
2. Create a new project using your GCP project
3. Enable Authentication
4. Add your application and get the configuration
5. Store Firebase configuration in Secret Manager:

```bash
# Create a secret for Firebase config
gcloud secrets create firebase-config --replication-policy="automatic"

# Add Firebase configuration (replace with your values)
echo '{
  "apiKey": "your-api-key",
  "authDomain": "your-project.firebaseapp.com",
  "projectId": "your-project-id",
  "storageBucket": "your-project.appspot.com",
  "messagingSenderId": "your-messaging-sender-id",
  "appId": "your-app-id"
}' | gcloud secrets versions add firebase-config --data-file=-
```

### 4. Deploy Services

The project includes a deployment script that handles both frontend and backend deployments. To deploy to an environment:

```bash
# Navigate to the scripts directory
cd scripts

# Deploy to dev environment
./deploy.sh dev

# Deploy to staging environment
./deploy.sh staging
```

The deployment script will:
1. Build and deploy the backend service
2. Build and deploy the frontend service
3. Set up environment variables from Secret Manager
4. Display the service URLs and next steps

### 5. Initialize Databases

Use the `infrastructure/init.sql` script to initialize the database schema in both environments:

```bash
# For dev environment
gcloud sql connect dev --user=app_user < infrastructure/init.sql

# For staging environment
gcloud sql connect staging --user=app_user < infrastructure/init.sql
```

## Environment Variables

Backend environment variables (automatically set from Secret Manager during deployment):
```
# Set by deploy script
ENVIRONMENT=dev|staging

# Retrieved from db-credentials-{env} secret
DB_USER=app_user
DB_PASS=generated_password
DB_NAME=app_db
DB_HOST=instance_connection_name
```

Frontend environment variables (automatically set from Secret Manager during deployment):
```
ENVIRONMENT=dev|staging
REACT_APP_API_URL=backend_service_url
FIREBASE_CONFIG=firebase-config
```

## Solution to Multi-Environment Issues

1. **User Separation**: Users are tracked with an environment field in the database
2. **Role Management**: Roles are environment-specific through the database
3. **Data Isolation**: Each environment has its own Cloud SQL instance
4. **Authentication**: Single Identity Platform configuration with environment-aware backend logic
5. **Frontend/Backend Separation**: Separate Cloud Run services for frontend and backend

## Testing

1. Deploy both frontend and backend services using the deployment script
2. Create a test user through Firebase Authentication
3. Access the frontend application URL
4. Log in with the test user
5. Verify that the dashboard shows the correct environment and user data
6. Test protected endpoints through the UI

## Local Development

1. Set up environment variables in `.env` file:

   ```bash
   # Backend .env
   ENVIRONMENT=dev
   # Get these values from Secret Manager
   DB_USER=$(gcloud secrets versions access latest --secret=db-credentials-dev | jq -r .DB_USER)
   DB_PASS=$(gcloud secrets versions access latest --secret=db-credentials-dev | jq -r .DB_PASS)
   DB_NAME=$(gcloud secrets versions access latest --secret=db-credentials-dev | jq -r .DB_NAME)
   DB_HOST=$(gcloud secrets versions access latest --secret=db-credentials-dev | jq -r .DB_HOST)

   # Frontend .env
   ENVIRONMENT=dev
   REACT_APP_API_URL=http://localhost:5000
   # Get Firebase config from Secret Manager
   FIREBASE_CONFIG=$(gcloud secrets versions access latest --secret=firebase-config)
   ```

2. Install dependencies:
   ```bash
   # Backend
   cd backend
   pip install -r requirements.txt
   
   # Frontend
   cd frontend
   npm install
   ```

3. Run the services:
   ```bash
   # Backend
   cd backend
   python app.py
   
   # Frontend
   cd frontend
   npm start
   ```
