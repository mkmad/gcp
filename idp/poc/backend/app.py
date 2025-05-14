import os
from flask import Flask, request, jsonify
from firebase_admin import auth, initialize_app
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import google.auth
from google.cloud import secretmanager
from functools import wraps

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize Firebase Admin SDK
initialize_app()

# Get environment
ENVIRONMENT = os.getenv('ENVIRONMENT', 'dev')

def get_db_connection():
    """Get database connection based on environment"""
    # In production, you would use Secret Manager to get these credentials
    db_user = os.getenv('DB_USER')
    db_pass = os.getenv('DB_PASS')
    db_name = os.getenv('DB_NAME')
    db_host = os.getenv('DB_HOST')
    
    connection_string = f"postgresql://{db_user}:{db_pass}@{db_host}/{db_name}"
    engine = create_engine(connection_string)
    return engine

def verify_token(id_token):
    """Verify Firebase ID token"""
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        return None

def get_user_roles(email, environment):
    """Get user roles for specific environment"""
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
    return [row[0] for row in result]

def require_auth(required_roles=None):
    """Decorator to require authentication and optional role check"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({"error": "No token provided"}), 401

            token = auth_header.split('Bearer ')[1]
            decoded_token = verify_token(token)
            
            if not decoded_token:
                return jsonify({"error": "Invalid token"}), 401

            # Get user roles for current environment
            user_roles = get_user_roles(decoded_token['email'], ENVIRONMENT)
            
            # Check if user has required roles
            if required_roles and not any(role in required_roles for role in user_roles):
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
    """Get resources based on user role"""
    engine = get_db_connection()
    with engine.connect() as connection:
        # Admin can see all resources
        if 'admin' in request.user['roles']:
            query = text("""
                SELECT * FROM resources 
                WHERE environment = :environment
            """)
        # Editor can see all non-sensitive resources and some sensitive ones
        elif 'editor' in request.user['roles']:
            query = text("""
                SELECT * FROM resources 
                WHERE environment = :environment 
                AND (NOT sensitive_data OR name = 'Analytics')
            """)
        # Viewer can only see non-sensitive resources
        else:
            query = text("""
                SELECT * FROM resources 
                WHERE environment = :environment 
                AND NOT sensitive_data
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
            "sensitive_data": row[4]
        } for row in result]

        return jsonify({
            "resources": resources,
            "user_roles": request.user['roles'],
            "environment": ENVIRONMENT
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

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port) 