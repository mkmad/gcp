#!/bin/bash

# Exit on error
set -e

# Check if environment argument is provided
if [ -z "$1" ]; then
    echo "Usage: ./deploy.sh <environment> [firebase-config-file]"
    echo "Example: ./deploy.sh dev path/to/firebase-config.json"
    exit 1
fi

# Set variables
ENV=$1
FIREBASE_CONFIG_FILE=$2
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
BACKEND_SERVICE="api-${ENV}"
FRONTEND_SERVICE="frontend-${ENV}"
SERVICE_ACCOUNT_NAME="cloud-run-service-account"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "🚀 Starting deployment for environment: ${ENV}"
echo "Project ID: ${PROJECT_ID}"
echo "Region: ${REGION}"

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    sql-component.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com \
    identitytoolkit.googleapis.com \
    iam.googleapis.com

# Setup service account and IAM permissions
echo "🔐 Setting up service account and permissions..."
if ! gcloud iam service-accounts describe "${SERVICE_ACCOUNT_EMAIL}" >/dev/null 2>&1; then
    echo "Creating service account: ${SERVICE_ACCOUNT_NAME}"
    gcloud iam service-accounts create "${SERVICE_ACCOUNT_NAME}" \
        --display-name="Cloud Run Service Account"
fi

echo "Granting Secret Manager Secret Accessor role to service account: ${SERVICE_ACCOUNT_EMAIL}"
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/secretmanager.secretAccessor" \
    --condition=None

echo "✅ Service account and permissions configured"

# Check if Cloud SQL instance exists
echo "🔍 Checking Cloud SQL instance..."
if ! gcloud sql instances describe $ENV >/dev/null 2>&1; then
    echo "Creating Cloud SQL instance: $ENV"
    gcloud sql instances create $ENV \
        --database-version=POSTGRES_13 \
        --tier=db-f1-micro \
        --region=$REGION
    echo "✅ Cloud SQL instance created"
else
    echo "✅ Cloud SQL instance already exists"
fi

# Setup database and credentials if they don't exist
echo "🔧 Checking database setup..."

# Check if database exists
if ! gcloud sql databases list --instance=$ENV | grep -q "app_db"; then
    echo "Creating database app_db..."
    gcloud sql databases create app_db --instance=$ENV
else
    echo "Database app_db already exists"
fi

# Check if secret exists
if ! gcloud secrets describe db-credentials-${ENV} >/dev/null 2>&1; then
    echo "Creating database user and credentials..."
    # Create user and store password in Secret Manager
    DB_PASS=$(openssl rand -base64 24)
    
    # Check if user exists
    if ! gcloud sql users list --instance=$ENV | grep -q "app_user"; then
        gcloud sql users create app_user \
            --instance=$ENV \
            --password=$DB_PASS
    else
        # Update existing user's password
        gcloud sql users set-password app_user \
            --instance=$ENV \
            --password=$DB_PASS
    fi

    # Store database credentials in Secret Manager
    gcloud secrets create db-credentials-${ENV} --replication-policy="automatic"
    echo '{
        "DB_USER": "app_user",
        "DB_PASS": "'$DB_PASS'",
        "DB_NAME": "app_db",
        "DB_HOST": "'$ENV'.${PROJECT_ID}.cloudsql.google.com"
    }' | gcloud secrets versions add db-credentials-${ENV} --data-file=-
    
    echo "✅ Database credentials created and stored in Secret Manager"
else
    echo "✅ Database credentials already exist in Secret Manager"
fi

# Run init.sql
echo "🔧 Running init.sql..."
# Get database credentials from Secret Manager
DB_PASS=$(gcloud secrets versions access latest --secret="db-credentials-${ENV}" | jq -r .DB_PASS)
DB_USER=$(gcloud secrets versions access latest --secret="db-credentials-${ENV}" | jq -r .DB_USER)
DB_HOST=$(gcloud secrets versions access latest --secret="db-credentials-${ENV}" | jq -r .DB_HOST)

# Create a temporary .pgpass file for passwordless connection
echo "${DB_HOST}:5432:app_db:${DB_USER}:${DB_PASS}" > ~/.pgpass
chmod 600 ~/.pgpass

# Run the initialization script
PGPASSFILE=~/.pgpass gcloud sql connect ${ENV} --user=${DB_USER} --database=app_db < ../infrastructure/init.sql

# Clean up
rm ~/.pgpass

# Setup Firebase configuration if it doesn't exist
echo "🔧 Checking Firebase configuration..."
if ! gcloud secrets describe firebase-config >/dev/null 2>&1; then
    if [ -z "$FIREBASE_CONFIG_FILE" ]; then
        echo "❌ Error: Firebase configuration not found in Secret Manager"
        echo "Usage: ./deploy.sh <environment> <firebase-config-file>"
        echo "Please provide the path to your Firebase configuration JSON file"
        exit 1
    fi

    if [ ! -f "$FIREBASE_CONFIG_FILE" ]; then
        echo "❌ Error: Firebase configuration file not found at: $FIREBASE_CONFIG_FILE"
        exit 1
    fi

    echo "Creating Firebase configuration from file: $FIREBASE_CONFIG_FILE"
    gcloud secrets create firebase-config --replication-policy="automatic"
    gcloud secrets versions add firebase-config --data-file="$FIREBASE_CONFIG_FILE"
    echo "✅ Firebase configuration stored in Secret Manager"
else
    echo "✅ Firebase configuration already exists"
fi

# Build and deploy backend
echo "📦 Building backend..."
cd ../backend
gcloud builds submit --tag gcr.io/${PROJECT_ID}/api-backend

echo "🚀 Deploying backend service: ${BACKEND_SERVICE}"
gcloud run deploy ${BACKEND_SERVICE} \
    --image gcr.io/${PROJECT_ID}/api-backend \
    --platform managed \
    --region ${REGION} \
    --service-account ${SERVICE_ACCOUNT_EMAIL} \
    --set-env-vars="ENVIRONMENT=${ENV}" \
    --set-secrets="/secrets/db-credentials.json=db-credentials-${ENV}:latest" \
    --allow-unauthenticated

# Get the backend URL
BACKEND_URL=$(gcloud run services describe ${BACKEND_SERVICE} \
    --platform managed \
    --region ${REGION} \
    --format 'value(status.url)')
echo "✅ Backend deployed at: ${BACKEND_URL}"

# Build and deploy frontend
echo "📦 Building frontend..."
cd ../frontend
gcloud builds submit --tag gcr.io/${PROJECT_ID}/frontend

echo "🚀 Deploying frontend service: ${FRONTEND_SERVICE}"
gcloud run deploy ${FRONTEND_SERVICE} \
    --image gcr.io/${PROJECT_ID}/frontend \
    --platform managed \
    --region ${REGION} \
    --service-account ${SERVICE_ACCOUNT_EMAIL} \
    --set-env-vars="ENVIRONMENT=${ENV},REACT_APP_API_URL=${BACKEND_URL}" \
    --set-secrets="/secrets/firebase-config.json=firebase-config:latest" \
    --allow-unauthenticated

# Get the frontend URL
FRONTEND_URL=$(gcloud run services describe ${FRONTEND_SERVICE} \
    --platform managed \
    --region ${REGION} \
    --format 'value(status.url)')
echo "✅ Frontend deployed at: ${FRONTEND_URL}"

echo "✨ Deployment complete!"
echo "Backend URL: ${BACKEND_URL}"
echo "Frontend URL: ${FRONTEND_URL}"

# Get database connection info for initialization
DB_HOST=$(gcloud secrets versions access latest --secret="db-credentials-${ENV}" | jq -r .DB_HOST)
DB_NAME=$(gcloud secrets versions access latest --secret="db-credentials-${ENV}" | jq -r .DB_NAME)
DB_USER=$(gcloud secrets versions access latest --secret="db-credentials-${ENV}" | jq -r .DB_USER)

# Check if database needs initialization
echo ""
echo "Checking if database needs initialization..."
if ! gcloud sql connect ${ENV} --user=${DB_USER} -d ${DB_NAME} --quiet --command="\dt" 2>/dev/null | grep -q "roles"; then
    echo "⚠️ Database tables not found. Please initialize the database:"
    echo "   gcloud sql connect ${ENV} --user=${DB_USER} < ../infrastructure/init.sql"
else
    echo "✅ Database tables already exist"
fi

# Add some helpful next steps
echo ""
echo "Next steps:"
echo "1. Add a test user with admin role:"
echo "   curl -X POST \"${BACKEND_URL}/api/admin/users\" \\"
echo "     -H \"Authorization: Bearer \${FIREBASE_TOKEN}\" \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"email\": \"test@example.com\", \"role\": \"admin\"}'"
echo ""
echo "2. Visit the frontend application:"
echo "   ${FRONTEND_URL}" 