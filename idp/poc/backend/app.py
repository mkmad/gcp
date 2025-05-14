import os
from flask import Flask, request, jsonify
from firebase_admin import auth, initialize_app
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import google.auth
from google.cloud import secretmanager, resourcemanager_v3
from functools import wraps
from flask_cors import CORS
import sys

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize Firebase Admin SDK
try:
    initialize_app()
    print("[INFO] Firebase Admin SDK initialized.", file=sys.stderr)
except Exception as e:
    print(f"[ERROR] Failed to initialize Firebase Admin SDK: {e}", file=sys.stderr)

# Get environment
ENVIRONMENT = os.getenv('ENVIRONMENT', 'dev')
print(f"[INFO] Backend running in environment: {ENVIRONMENT}", file=sys.stderr)

def get_db_connection():
    """Get database connection based on environment"""
    db_user = os.getenv('DB_USER')
    db_pass = os.getenv('DB_PASS')
    db_name = os.getenv('DB_NAME')
    db_host = os.getenv('DB_HOST')
    print(f"[INFO] Connecting to DB: user={db_user}, db={db_name}, host={db_host}", file=sys.stderr)
    connection_string = f"postgresql://{db_user}:{db_pass}@{db_host}/{db_name}"
    engine = create_engine(connection_string)
    return engine

def verify_token(id_token):
    """Verify Firebase ID token"""
    try:
        decoded_token = auth.verify_id_token(id_token)
        print(f"[INFO] Token verified for user: {decoded_token.get('email', 'unknown')}", file=sys.stderr)
        return decoded_token
    except Exception as e:
        print(f"[ERROR] Token verification failed: {e}", file=sys.stderr)
        return None

def get_user_roles(email, environment):
    print(f"[INFO] Fetching roles for user: {email} in env: {environment}", file=sys.stderr)
    engine = get_db_connection()
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT r.name as role_name
                FROM user_roles ur
                JOIN roles r ON ur.role_id = r.id
                WHERE ur.user_email = :email
                AND ur.environment = :environment
            """),
            {"email": email, "environment": environment}
        ).fetchall()
    roles = [row[0] for row in result]
    print(f"[INFO] Roles found: {roles}", file=sys.stderr)
    return roles

def require_auth(required_roles=None):
    """Decorator to require authentication and optional role check"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                print("[WARN] No token provided in Authorization header", file=sys.stderr)
                return jsonify({"error": "No token provided"}), 401

            token = auth_header.split('Bearer ')[1]
            decoded_token = verify_token(token)
            
            if not decoded_token:
                print("[WARN] Invalid token received", file=sys.stderr)
                return jsonify({"error": "Invalid token"}), 401

            # Get user roles for current environment
            user_roles = get_user_roles(decoded_token['email'], ENVIRONMENT)
            
            # Check if user has required roles
            if required_roles and not any(role in required_roles for role in user_roles):
                print(f"[WARN] User {decoded_token['email']} lacks required roles: {required_roles}. User roles: {user_roles}", file=sys.stderr)
                return jsonify({
                    "error": "Insufficient permissions",
                    "required_roles": required_roles,
                    "user_roles": user_roles,
                    "environment": ENVIRONMENT
                }), 403

            # Add user info to request context
            request.user = {
                'uid': decoded_token['uid'],
                'email': decoded_token['email'],
                'roles': user_roles
            }
            print(f"[INFO] Authenticated user: {decoded_token['email']} with roles: {user_roles}", file=sys.stderr)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "environment": ENVIRONMENT})

@app.route('/api/user')
@require_auth()
def get_user():
    """Get user information including roles"""
    return jsonify({
        "user_id": request.user['uid'],
        "email": request.user['email'],
        "roles": request.user['roles'],
        "environment": ENVIRONMENT
    })

@app.route('/api/resources')
@require_auth(['viewer', 'editor', 'admin'])
def get_resources():
    """Get resources based on user role with categorization"""
    print(f"[INFO] Fetching resources for user with roles: {request.user['roles']}", file=sys.stderr)
    
    engine = get_db_connection()
    with engine.connect() as connection:
        # Base query with role-specific conditions
        if 'admin' in request.user['roles']:
            # Admin can see everything
            query = text("""
                SELECT 
                    r.*,
                    CASE 
                        WHEN sensitive_data = true THEN 'Highly Sensitive'
                        ELSE 'General Access'
                    END as access_level
                FROM resources r
                WHERE environment = :environment
                ORDER BY sensitive_data DESC, name ASC
            """)
        elif 'editor' in request.user['roles']:
            # Editor can see non-sensitive data and specific sensitive resources
            query = text("""
                SELECT 
                    r.*,
                    CASE 
                        WHEN name IN ('Analytics Dashboard', 'Sales Pipeline') THEN 'Editor Access'
                        ELSE 'General Access'
                    END as access_level
                FROM resources r
                WHERE environment = :environment 
                AND (
                    NOT sensitive_data 
                    OR name IN ('Analytics Dashboard', 'Sales Pipeline')
                )
                ORDER BY sensitive_data DESC, name ASC
            """)
        else:
            # Viewer can only see non-sensitive resources
            query = text("""
                SELECT 
                    r.*,
                    'General Access' as access_level
                FROM resources r
                WHERE environment = :environment 
                AND NOT sensitive_data
                ORDER BY name ASC
            """)
        
        result = connection.execute(
            query,
            {"environment": ENVIRONMENT}
        ).fetchall()

        resources = [{
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "environment": row[3],
            "sensitive_data": row[4],
            "access_level": row[6]  # New field from our CASE statement
        } for row in result]

        print(f"[INFO] Returning {len(resources)} resources for user", file=sys.stderr)
        
        return jsonify({
            "resources": resources,
            "user_roles": request.user['roles'],
            "environment": ENVIRONMENT,
            "access_summary": {
                "total_resources": len(resources),
                "has_sensitive_access": any(r["sensitive_data"] for r in resources),
                "access_level": "Full Access" if 'admin' in request.user['roles'] else 
                              "Extended Access" if 'editor' in request.user['roles'] else 
                              "Basic Access"
            }
        })

@app.route('/api/admin/users', methods=['POST'])
@require_auth(['admin'])
def manage_user_roles():
    """Manage user roles (admin only)"""
    data = request.json
    if not data or 'email' not in data or 'role' not in data:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        engine = get_db_connection()
        with engine.connect() as connection:
            connection.execute(
                text("SELECT add_user_role(:email, :role, :environment)"),
                {
                    "email": data['email'],
                    "role": data['role'],
                    "environment": ENVIRONMENT
                }
            )
        return jsonify({
            "message": f"Role {data['role']} assigned to {data['email']} in {ENVIRONMENT} environment"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/iam-roles')
@require_auth()
def get_iam_roles():
    user_email = request.user['email']
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('PROJECT_ID') or 'your-project-id'
    client = resourcemanager_v3.ProjectsClient()
    resource = f"projects/{project_id}"
    policy = client.get_iam_policy(request={"resource": resource})
    user_roles = []
    for binding in policy.bindings:
        if f"user:{user_email}" in binding.members:
            user_roles.append(binding.role)
    return jsonify({"gcp_iam_roles": user_roles})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port) 