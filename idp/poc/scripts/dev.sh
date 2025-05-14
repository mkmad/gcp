#!/bin/bash

# Exit on error
set -e

# Function to cleanup Docker containers and exit
cleanup() {
    echo -e "\n🧹 Cleaning up..."
    docker compose down
    echo "✅ Cleanup complete"
    exit 0
}

# Trap SIGTERM and SIGINT (ctrl+c)
trap cleanup SIGTERM SIGINT

# Default environment
ENV=${1:-dev}

# Check if init.sql exists
if [ ! -f "../infrastructure/init.sql" ]; then
    echo "❌ Error: init.sql not found in infrastructure directory"
    exit 1
fi

echo "🚀 Starting local development environment"
echo "Environment: ${ENV}"

# Extract Firebase config from firebase.json
PROJECT_ID=$(jq -r .project_id ../backend/firebase-service-account.json)

# Create root .env file for docker-compose
echo "📝 Creating root .env file for docker-compose..."
cat > "../.env" << EOF
# Environment
ENV=${ENV}

# Firebase config
FIREBASE_API_KEY=AIzaSyBXBOSMiFmBJ1MZOAzzvFhBwxkbdmU_h0s
FIREBASE_AUTH_DOMAIN=${PROJECT_ID}.firebaseapp.com
FIREBASE_PROJECT_ID=${PROJECT_ID}
FIREBASE_STORAGE_BUCKET=${PROJECT_ID}.firebasestorage.app
FIREBASE_MESSAGING_SENDER_ID=664105001492
FIREBASE_APP_ID=1:664105001492:web:3c2e26ed3fb6eb049bfd01
FIREBASE_MEASUREMENT_ID=G-20DLDQSH91
EOF

# Create frontend .env file if it doesn't exist
if [ ! -f "../frontend/.env" ]; then
    echo "📝 Creating frontend .env file..."
    cat > "../frontend/.env" << EOF
# Environment
REACT_APP_ENV=${ENV}
REACT_APP_API_URL=http://localhost:8080

# Firebase config
REACT_APP_FIREBASE_API_KEY=\${FIREBASE_API_KEY}
REACT_APP_FIREBASE_AUTH_DOMAIN=\${FIREBASE_AUTH_DOMAIN}
REACT_APP_FIREBASE_PROJECT_ID=\${FIREBASE_PROJECT_ID}
REACT_APP_FIREBASE_STORAGE_BUCKET=\${FIREBASE_STORAGE_BUCKET}
REACT_APP_FIREBASE_MESSAGING_SENDER_ID=\${FIREBASE_MESSAGING_SENDER_ID}
REACT_APP_FIREBASE_APP_ID=\${FIREBASE_APP_ID}
REACT_APP_FIREBASE_MEASUREMENT_ID=\${FIREBASE_MEASUREMENT_ID}
EOF
    
    echo "✅ Created frontend/.env template"
fi

# Check if docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    exit 1
fi

# Function to check if containers are running
check_containers() {
    local service=$1
    local count=$(docker compose ps --status running $service | grep -c $service || true)
    if [ "$count" -eq 0 ]; then
        return 1
    else
        return 0
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local service=$1
    local max_attempts=300
    local attempt=1
    
    echo "⏳ Waiting for $service to be ready..."
    while ! check_containers $service; do
        if [ $attempt -eq $max_attempts ]; then
            echo "❌ Timeout waiting for $service"
            cleanup
        fi
        sleep 2
        attempt=$((attempt + 1))
    done
    echo "✅ $service is ready"
}

# Function to verify database initialization
verify_database() {
    echo "🔍 Verifying database initialization..."
    
    # Wait a bit for init.sql to complete
    sleep 5
    
    # Check if tables exist
    TABLES=$(docker compose exec -T db psql -U postgres -d idp_poc -t -c "
        SELECT COUNT(*) FROM (
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename IN ('users', 'roles', 'user_roles', 'resources')
        ) t;")
    
    if [ "$TABLES" -eq "4" ]; then
        echo "✅ Database initialized successfully"
        
        # Check if default roles were created
        ROLES=$(docker compose exec -T db psql -U postgres -d idp_poc -t -c "SELECT COUNT(*) FROM roles;")
        if [ "$ROLES" -eq "3" ]; then
            echo "✅ Default roles created"
        else
            echo "⚠️  Default roles not found"
            echo "🔄 Reinitializing database..."
            docker compose exec -T db psql -U postgres -d idp_poc < ../infrastructure/init.sql
        fi
    else
        echo "⚠️  Database tables not found"
        echo "🔄 Reinitializing database..."
        docker compose exec -T db psql -U postgres -d idp_poc < ../infrastructure/init.sql
    fi
}

# Start services with docker compose
echo "🐳 Starting Docker services..."
docker compose up --build -d

# Wait for services to be ready
wait_for_service "db"
verify_database
wait_for_service "backend"
wait_for_service "frontend"

# Get service URLs
FRONTEND_URL="http://localhost:3000"
BACKEND_URL="http://localhost:8080"

echo "✨ Development environment is ready!"
echo "Frontend URL: ${FRONTEND_URL}"
echo "Backend URL: ${BACKEND_URL}"
echo ""
echo "📝 Development Tips:"
echo "1. View logs with: docker compose logs -f"
echo "2. Stop services with: docker compose down"
echo "3. Rebuild services with: docker compose up --build"
echo "4. Access database with: docker compose exec db psql -U postgres -d idp_poc"
echo ""
echo "🔍 Monitoring containers..."
docker compose ps

# Keep script running to handle signals
echo -e "\n👀 Watching for changes... Press Ctrl+C to stop"
while true; do
    sleep 1
done 