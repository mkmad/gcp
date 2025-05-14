#!/bin/sh

# Create env-config.js with runtime environment variables
cat <<EOF > /usr/share/nginx/html/env-config.js
window.ENV = {
  REACT_APP_API_URL: "${REACT_APP_API_URL}",
  ENVIRONMENT: "${ENVIRONMENT}"
};
EOF

# Start nginx
nginx -g "daemon off;" 