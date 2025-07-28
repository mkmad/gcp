from googleapiclient.discovery import build
from google.oauth2 import service_account

# Replace with your service account JSON file path
SERVICE_ACCOUNT_FILE = 'service-account.json'
SCOPES = ['https://www.googleapis.com/auth/cloud-billing']

def get_billing_service():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('cloudbilling', 'v1', credentials=credentials)

def list_billing_admins():
    service = get_billing_service()
    billing_accounts = []
    
    # List all billing accounts in the organization
    request = service.billingAccounts().list()
    while request is not None:
        response = request.execute()
        billing_accounts.extend(response.get('billingAccounts', []))
        request = service.billingAccounts().list_next(previous_request=request, previous_response=response)
    
    admins = {}
    for account in billing_accounts:
        account_id = account['name']
        request = service.billingAccounts().getIamPolicy(resource=account_id)
        policy = request.execute()
        
        for binding in policy.get('bindings', []):
            role = binding['role']
            if 'billing.admin' in role:  # Check for admin roles
                for member in binding.get('members', []):
                    if member.startswith('user:'):
                        email = member.replace('user:', '')
                        if account_id not in admins:
                            admins[account_id] = []
                        admins[account_id].append(email)
    
    return admins

if __name__ == '__main__':
    admins_by_account = list_billing_admins()
    for account, emails in admins_by_account.items():
        print(f"Account: {account}")
        for email in emails:
            print(f"  Admin: {email}")