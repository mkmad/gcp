# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the app for production
RUN npm run build

# Development stage
FROM node:18-alpine as development

# Define build arguments
ARG REACT_APP_FIREBASE_API_KEY
ARG REACT_APP_FIREBASE_AUTH_DOMAIN
ARG REACT_APP_FIREBASE_PROJECT_ID
ARG REACT_APP_FIREBASE_STORAGE_BUCKET
ARG REACT_APP_FIREBASE_MESSAGING_SENDER_ID
ARG REACT_APP_FIREBASE_APP_ID

# Set environment variables
ENV REACT_APP_FIREBASE_API_KEY=$REACT_APP_FIREBASE_API_KEY \
    REACT_APP_FIREBASE_AUTH_DOMAIN=$REACT_APP_FIREBASE_AUTH_DOMAIN \
    REACT_APP_FIREBASE_PROJECT_ID=$REACT_APP_FIREBASE_PROJECT_ID \
    REACT_APP_FIREBASE_STORAGE_BUCKET=$REACT_APP_FIREBASE_STORAGE_BUCKET \
    REACT_APP_FIREBASE_MESSAGING_SENDER_ID=$REACT_APP_FIREBASE_MESSAGING_SENDER_ID \
    REACT_APP_FIREBASE_APP_ID=$REACT_APP_FIREBASE_APP_ID

WORKDIR /app

# Create scripts directory that won't be affected by volume mounts
RUN mkdir -p /usr/src/app-scripts

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Create start script
COPY <<'EOF' /usr/src/app-scripts/start-dev.sh
#!/bin/sh
mkdir -p /app/public
cat > /app/public/firebase-config.js << 'EOFJS'
window.firebaseConfig = {
  apiKey: "${REACT_APP_FIREBASE_API_KEY}",
  authDomain: "${REACT_APP_FIREBASE_AUTH_DOMAIN}",
  projectId: "${REACT_APP_FIREBASE_PROJECT_ID}",
  storageBucket: "${REACT_APP_FIREBASE_STORAGE_BUCKET}",
  messagingSenderId: "${REACT_APP_FIREBASE_MESSAGING_SENDER_ID}",
  appId: "${REACT_APP_FIREBASE_APP_ID}"
};
EOFJS

cd /app && exec npm start
EOF

# Make script executable
RUN chmod +x /usr/src/app-scripts/start-dev.sh

# Expose port
EXPOSE 3000

# Start the development server
CMD ["/usr/src/app-scripts/start-dev.sh"]

# Production stage
FROM nginx:alpine as production

# Define build arguments for production
ARG REACT_APP_FIREBASE_API_KEY
ARG REACT_APP_FIREBASE_AUTH_DOMAIN
ARG REACT_APP_FIREBASE_PROJECT_ID
ARG REACT_APP_FIREBASE_STORAGE_BUCKET
ARG REACT_APP_FIREBASE_MESSAGING_SENDER_ID
ARG REACT_APP_FIREBASE_APP_ID

# Set environment variables for production
ENV REACT_APP_FIREBASE_API_KEY=$REACT_APP_FIREBASE_API_KEY \
    REACT_APP_FIREBASE_AUTH_DOMAIN=$REACT_APP_FIREBASE_AUTH_DOMAIN \
    REACT_APP_FIREBASE_PROJECT_ID=$REACT_APP_FIREBASE_PROJECT_ID \
    REACT_APP_FIREBASE_STORAGE_BUCKET=$REACT_APP_FIREBASE_STORAGE_BUCKET \
    REACT_APP_FIREBASE_MESSAGING_SENDER_ID=$REACT_APP_FIREBASE_MESSAGING_SENDER_ID \
    REACT_APP_FIREBASE_APP_ID=$REACT_APP_FIREBASE_APP_ID

# Copy built files from build stage
COPY --from=build /app/build /usr/share/nginx/html

# Create default nginx configuration
RUN echo 'server {\n\
    listen 8080;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
    location / {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
}' > /etc/nginx/conf.d/default.conf

# Create script to generate Firebase config
RUN echo '#!/bin/sh\n\
cat > /usr/share/nginx/html/firebase-config.js << EOF\n\
window.firebaseConfig = {\n\
  apiKey: "$REACT_APP_FIREBASE_API_KEY",\n\
  authDomain: "$REACT_APP_FIREBASE_AUTH_DOMAIN",\n\
  projectId: "$REACT_APP_FIREBASE_PROJECT_ID",\n\
  storageBucket: "$REACT_APP_FIREBASE_STORAGE_BUCKET",\n\
  messagingSenderId: "$REACT_APP_FIREBASE_MESSAGING_SENDER_ID",\n\
  appId: "$REACT_APP_FIREBASE_APP_ID"\n\
};\n\
EOF\n\
exec nginx -g "daemon off;"' > /docker-entrypoint.sh \
&& chmod +x /docker-entrypoint.sh

# Expose port
EXPOSE 8080

# Start nginx with Firebase config
CMD ["/docker-entrypoint.sh"] 