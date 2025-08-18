#!/usr/bin/env python3
"""
GCP Organization Access Report Generator

This script generates a CSV report showing:
1. Organization name
2. Billing console access (view access)
3. GCP console access (view access)

For the currently authenticated user account.
"""

import csv
import json
import sys
from typing import Dict, List, Tuple
from googleapiclient.discovery import build
from google.auth import default
from google.auth.exceptions import DefaultCredentialsError
from googleapiclient.errors import HttpError


def get_user_email_from_gcloud() -> str:
    """Get user email from gcloud config as fallback."""
    try:
        import subprocess
        result = subprocess.run(['gcloud', 'config', 'get-value', 'account'], 
                              capture_output=True, text=True, check=True)
        email = result.stdout.strip()
        if email:
            print(f"Using email from gcloud config: {email}")
            return email
        else:
            print("Could not get email from gcloud config. Using default.")
            return 'user@example.com'
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Could not get email from gcloud config. Using default.")
        return 'user@example.com'


def get_credentials():
    """Get default credentials for the current user."""
    try:
        credentials, project = default()
        if project:
            print(f"Using project: {project}")
        else:
            print("Warning: No project set. Using default credentials.")
            # Try to get project from gcloud config
            import subprocess
            try:
                result = subprocess.run(['gcloud', 'config', 'get-value', 'project'], 
                                      capture_output=True, text=True, check=True)
                project = result.stdout.strip()
                if project:
                    print(f"Found project from gcloud config: {project}")
                else:
                    print("No project found in gcloud config either.")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("Could not determine project from gcloud config.")
        
        return credentials
    except DefaultCredentialsError:
        print("Error: No default credentials found.")
        print("Please run: gcloud auth application-default login")
        sys.exit(1)


def get_organizations(credentials) -> List[Dict]:
    """Get all organizations the user has access to."""
    try:
        service = build('cloudresourcemanager', 'v1', credentials=credentials)
        organizations = []
        
        # Use search method instead of list for organizations
        request = service.organizations().search()
        while request is not None:
            response = request.execute()
            organizations.extend(response.get('organizations', []))
            request = service.organizations().search_next(previous_request=request, previous_response=response)
        
        return organizations
    except HttpError as e:
        if e.resp.status == 403:
            print("Error: Permission denied. You may not have access to list organizations.")
            print("Required role: roles/resourcemanager.organizationViewer")
        else:
            print(f"Error getting organizations: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error getting organizations: {e}")
        return []


def discover_organizations_from_billing(credentials, billing_accounts: List[Dict]) -> List[Dict]:
    """Discover organizations through billing account relationships."""
    discovered_orgs = []
    
    for billing_account in billing_accounts:
        org_id = None
        
        # Check if billing account has a parent organization
        if billing_account.get('parent'):
            org_id = billing_account['parent']
        # Check if billing account has a master billing account (which might be an org)
        elif billing_account.get('masterBillingAccount'):
            org_id = billing_account['masterBillingAccount']
        
        if org_id and org_id.startswith('organizations/'):
            # Try to get organization details
            try:
                service = build('cloudresourcemanager', 'v1', credentials=credentials)
                org_details = service.organizations().get(name=org_id).execute()
                
                # Check if this org is already in our list
                if not any(org['name'] == org_id for org in discovered_orgs):
                    discovered_orgs.append(org_details)
                    print(f"  Discovered organization via billing: {org_details.get('displayName', 'Unknown')} ({org_id})")
            except HttpError as e:
                if e.resp.status == 403:
                    print(f"  Cannot access organization details for {org_id} (permission denied)")
                else:
                    print(f"  Error getting organization details for {org_id}: {e}")
            except Exception as e:
                print(f"  Unexpected error getting organization details for {org_id}: {e}")
    
    return discovered_orgs


def discover_all_billing_subaccounts(credentials, billing_accounts: List[Dict]) -> List[Dict]:
    """Discover ALL billing subaccounts regardless of organization access."""
    subaccounts = []
    master_accounts = {}
    
    print("Discovering all billing subaccounts...")
    
    for billing_account in billing_accounts:
        # Check if this is a subaccount (has a master billing account)
        if billing_account.get('masterBillingAccount'):
            subaccount_info = {
                'name': billing_account.get('displayName', 'Unknown'),
                'id': billing_account['name'],
                'master_account': billing_account['masterBillingAccount'],
                'type': 'subaccount',
                'status': billing_account.get('open', 'Unknown'),
                'parent_org': billing_account.get('parent', 'Unknown'),
                'access_level': 'direct'  # We can see it directly
            }
            subaccounts.append(subaccount_info)
            print(f"  Found billing subaccount: {subaccount_info['name']} (master: {subaccount_info['master_account']})")
            
            # Track master accounts
            master_id = billing_account['masterBillingAccount']
            if master_id not in master_accounts:
                master_accounts[master_id] = []
            master_accounts[master_id].append(subaccount_info['name'])
    
    # Now try to discover master accounts and their organizations
    print("Investigating master billing accounts...")
    for master_id, subaccount_names in master_accounts.items():
        print(f"  Master account {master_id} has subaccounts: {', '.join(subaccount_names)}")
        
        # Try to get details about the master account
        try:
            service = build('cloudbilling', 'v1', credentials=credentials)
            master_details = service.billingAccounts().get(name=master_id).execute()
            print(f"    Master account name: {master_details.get('displayName', 'Unknown')}")
            print(f"    Master account parent: {master_details.get('parent', 'None')}")
            
            # If master account has a parent organization, try to get org details
            if master_details.get('parent', '').startswith('organizations/'):
                org_id = master_details['parent']
                try:
                    org_service = build('cloudresourcemanager', 'v1', credentials=credentials)
                    org_details = org_service.organizations().get(name=org_id).execute()
                    print(f"    Parent organization: {org_details.get('displayName', 'Unknown')} ({org_id})")
                    
                    # Check if we can access this organization
                    has_org_access = check_org_access(credentials, org_id)
                    has_billing_access = check_billing_access(credentials, master_id)
                    print(f"    Organization access: {has_org_access}, Billing access: {has_billing_access}")
                    
                except HttpError as e:
                    if e.resp.status == 403:
                        print(f"    Cannot access organization {org_id} (permission denied)")
                    else:
                        print(f"    Error accessing organization {org_id}: {e}")
                except Exception as e:
                    print(f"    Unexpected error accessing organization {org_id}: {e}")
            
        except HttpError as e:
            if e.resp.status == 403:
                print(f"    Cannot access master account {master_id} (permission denied)")
            else:
                print(f"    Error accessing master account {master_id}: {e}")
        except Exception as e:
            print(f"    Unexpected error accessing master account {master_id}: {e}")
    
    return subaccounts


def investigate_organization_access(credentials, org_name: str, org_id: str):
    """Investigate why an organization shows no access despite having visible subaccounts."""
    print(f"\nInvestigating access to {org_name} ({org_id})...")
    
    try:
        # Method 1: Try direct organization access
        service = build('cloudresourcemanager', 'v1', credentials=credentials)
        org_details = service.organizations().get(name=org_id).execute()
        print(f"  ✓ Can access organization details directly")
        print(f"  Organization display name: {org_details.get('displayName', 'Unknown')}")
        
        # Method 2: Check IAM policy
        try:
            policy = service.organizations().getIamPolicy(resource=org_id).execute()
            user_email = get_user_email_from_gcloud()
            print(f"  Checking IAM policy for user: {user_email}")
            
            found_roles = []
            for binding in policy.get('bindings', []):
                role = binding['role']
                for member in binding.get('members', []):
                    if member == f'user:{user_email}' or member == 'allUsers' or member.startswith('group:'):
                        found_roles.append(role)
                        print(f"    Found role: {role}")
            
            if not found_roles:
                print(f"  ✗ No direct IAM roles found for user")
            else:
                print(f"  ✓ Found {len(found_roles)} IAM roles")
                
        except HttpError as e:
            if e.resp.status == 403:
                print(f"  ✗ Cannot access IAM policy (permission denied)")
            else:
                print(f"  Error accessing IAM policy: {e}")
        
        # Method 3: Check billing accounts linked to this org
        billing_accounts = get_billing_accounts(credentials)
        linked_billing_accounts = []
        
        for billing_account in billing_accounts:
            if (billing_account.get('parent') == org_id or 
                billing_account.get('masterBillingAccount') == org_id):
                linked_billing_accounts.append(billing_account)
                print(f"  Found linked billing account: {billing_account.get('displayName', 'Unknown')} ({billing_account['name']})")
        
        if linked_billing_accounts:
            print(f"  ✓ Found {len(linked_billing_accounts)} linked billing accounts")
        else:
            print(f"  ✗ No linked billing accounts found")
            
    except HttpError as e:
        if e.resp.status == 403:
            print(f"  ✗ Cannot access organization directly (permission denied)")
        else:
            print(f"  Error accessing organization: {e}")
    except Exception as e:
        print(f"  Unexpected error: {e}")


def get_all_organizations(credentials) -> List[Dict]:
    """Get all organizations through multiple discovery methods."""
    print("Discovering organizations...")
    
    # Method 1: Direct organization access
    direct_orgs = get_organizations(credentials)
    print(f"Found {len(direct_orgs)} organizations through direct access")
    
    # Method 2: Discover organizations through billing accounts
    billing_accounts = get_billing_accounts(credentials)
    billing_orgs = discover_organizations_from_billing(credentials, billing_accounts)
    print(f"Found {len(billing_orgs)} additional organizations through billing accounts")
    
    # Method 3: Discover ALL billing subaccounts (enhanced)
    subaccounts = discover_all_billing_subaccounts(credentials, billing_accounts)
    print(f"Found {len(subaccounts)} billing subaccounts")
    
    # Combine and deduplicate
    all_orgs = direct_orgs.copy()
    for org in billing_orgs:
        if not any(existing_org['name'] == org['name'] for existing_org in all_orgs):
            all_orgs.append(org)
    
    print(f"Total unique organizations found: {len(all_orgs)}")
    return all_orgs, subaccounts


def get_billing_accounts(credentials) -> List[Dict]:
    """Get all billing accounts the user has access to."""
    try:
        service = build('cloudbilling', 'v1', credentials=credentials)
        billing_accounts = []
        
        request = service.billingAccounts().list()
        while request is not None:
            response = request.execute()
            billing_accounts.extend(response.get('billingAccounts', []))
            request = service.billingAccounts().list_next(previous_request=request, previous_response=response)
        
        return billing_accounts
    except HttpError as e:
        if e.resp.status == 403:
            print("Error: Permission denied or Cloud Billing API not enabled.")
            print("Please ensure you have billing.viewer role and Cloud Billing API is enabled.")
        else:
            print(f"Error getting billing accounts: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error getting billing accounts: {e}")
        return []


def check_billing_access(credentials, billing_account_name: str) -> bool:
    """Check if user has view access to billing console for a specific billing account."""
    try:
        service = build('cloudbilling', 'v1', credentials=credentials)
        request = service.billingAccounts().getIamPolicy(resource=billing_account_name)
        policy = request.execute()
        
        # Get current user email safely
        user_email = get_user_email_from_gcloud()
        
        for binding in policy.get('bindings', []):
            role = binding['role']
            # Check for billing viewer or admin roles
            if any(billing_role in role for billing_role in ['billing.viewer', 'billing.admin', 'billing.user']):
                for member in binding.get('members', []):
                    if member == f'user:{user_email}' or member == 'allUsers' or member.startswith('group:'):
                        return True
        
        return False
    except HttpError as e:
        if e.resp.status == 403:
            print(f"Permission denied checking billing access for {billing_account_name}")
        else:
            print(f"Error checking billing access for {billing_account_name}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error checking billing access for {billing_account_name}: {e}")
        return False


def check_org_access(credentials, org_name: str) -> bool:
    """Check if user has view access to GCP console for a specific organization."""
    try:
        service = build('cloudresourcemanager', 'v1', credentials=credentials)
        
        # Try to get organization IAM policy
        request = service.organizations().getIamPolicy(resource=org_name)
        policy = request.execute()
        
        # Get current user email safely
        user_email = get_user_email_from_gcloud()
        
        for binding in policy.get('bindings', []):
            role = binding['role']
            # Check for organization viewer or admin roles
            if any(org_role in role for org_role in ['roles/resourcemanager.organizationViewer', 
                                                   'roles/resourcemanager.organizationAdmin',
                                                   'roles/resourcemanager.organizationMember']):
                for member in binding.get('members', []):
                    if member == f'user:{user_email}' or member == 'allUsers' or member.startswith('group:'):
                        return True
        
        return False
    except HttpError as e:
        if e.resp.status == 403:
            print(f"Permission denied checking org access for {org_name}")
        else:
            print(f"Error checking org access for {org_name}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error checking org access for {org_name}: {e}")
        return False


def generate_access_report(credentials) -> List[Tuple[str, bool, bool]]:
    """Generate the access report for all organizations."""
    print("Fetching organizations...")
    organizations, subaccounts = get_all_organizations(credentials)
    
    print("Fetching billing accounts...")
    billing_accounts = get_billing_accounts(credentials)
    
    print("Checking access permissions...")
    report_data = []
    
    # Get current user email for display
    user_email = get_user_email_from_gcloud()
    print(f"Generating report for user: {user_email}")
    
    # First, let's check which billing accounts the user actually has access to
    accessible_billing_accounts = []
    for billing_account in billing_accounts:
        if check_billing_access(credentials, billing_account['name']):
            accessible_billing_accounts.append(billing_account)
            print(f"  User has access to billing account: {billing_account.get('displayName', 'Unknown')} ({billing_account['name']})")
            # Debug: Show billing account details
            print(f"    - Parent: {billing_account.get('parent', 'None')}")
            print(f"    - Master: {billing_account.get('masterBillingAccount', 'None')}")
            print(f"    - Open: {billing_account.get('open', 'Unknown')}")
            
            # Check if this billing account is linked to an organization
            parent = billing_account.get('parent', '')
            master = billing_account.get('masterBillingAccount', '')
            if parent.startswith('organizations/') or master.startswith('organizations/'):
                org_id = parent if parent.startswith('organizations/') else master
                print(f"    - Linked to organization: {org_id}")
    
    print(f"Total accessible billing accounts: {len(accessible_billing_accounts)}")
    
    # Debug: Show all organizations
    print(f"Total organizations found: {len(organizations)}")
    for org in organizations:
        print(f"  - {org['displayName']}: {org['name']}")
        
        # Show which billing accounts are linked to this org
        linked_billing_accounts = []
        for billing_account in accessible_billing_accounts:
            if (billing_account.get('parent') == org['name'] or 
                billing_account.get('masterBillingAccount') == org['name']):
                linked_billing_accounts.append(billing_account.get('displayName', 'Unknown'))
        
        if linked_billing_accounts:
            print(f"    Linked billing accounts: {', '.join(linked_billing_accounts)}")
        else:
            print(f"    No directly linked billing accounts found")
    
    for org in organizations:
        org_name = org['displayName']
        org_id = org['name']
        
        print(f"  Checking access for organization: {org_name}")
        
        # Check GCP console access
        has_gcp_access = check_org_access(credentials, org_id)
        
        # Check billing access - improved logic
        has_billing_access = False
        
        # Method 1: Check if any accessible billing account is linked to this org
        for billing_account in accessible_billing_accounts:
            # Check direct parent relationship
            if billing_account.get('parent') == org_id:
                has_billing_access = True
                print(f"    Billing access via direct parent relationship")
                break
            
            # Check master billing account relationship
            if billing_account.get('masterBillingAccount') == org_id:
                has_billing_access = True
                print(f"    Billing access via master billing account")
                break
        
        # Method 2: If no direct link found, check if user can access billing for this org
        # by trying to list billing accounts within the org context
        if not has_billing_access:
            try:
                # Try to get billing accounts in the context of this organization
                service = build('cloudbilling', 'v1', credentials=credentials)
                # This is a bit tricky - we'll check if the user can access any billing
                # information related to this organization
                for billing_account in accessible_billing_accounts:
                    # Check if the billing account name contains the org ID or if we can
                    # access billing info for this org through the billing account
                    if org_id in billing_account.get('name', '') or org_id in billing_account.get('displayName', ''):
                        has_billing_access = True
                        print(f"    Billing access via billing account association")
                        break
            except Exception as e:
                print(f"    Error checking org-specific billing access: {e}")
        
        # Method 3: Check if user has billing viewer role at the organization level
        if not has_billing_access:
            try:
                service = build('cloudresourcemanager', 'v1', credentials=credentials)
                request = service.organizations().getIamPolicy(resource=org_id)
                policy = request.execute()
                
                for binding in policy.get('bindings', []):
                    role = binding['role']
                    # Check for billing-related roles at org level
                    if any(billing_role in role for billing_role in ['billing.admin', 'billing.user', 'billing.viewer']):
                        for member in binding.get('members', []):
                            if member == f'user:{user_email}' or member == 'allUsers' or member.startswith('group:'):
                                has_billing_access = True
                                print(f"    Billing access via organization-level IAM role: {role}")
                                break
                        if has_billing_access:
                            break
            except Exception as e:
                print(f"    Error checking org-level billing roles: {e}")
        
        report_data.append((org_name, has_billing_access, has_gcp_access))
    
    return report_data


def save_to_csv(report_data: List[Tuple[str, bool, bool]], filename: str = 'gcp_org_access_report.csv'):
    """Save the report data to a CSV file."""
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow(['Organization Name', 'Billing Console Access', 'GCP Console Access'])
        
        # Write data
        for org_name, billing_access, gcp_access in report_data:
            writer.writerow([
                org_name,
                'Yes' if billing_access else 'No',
                'Yes' if gcp_access else 'No'
            ])
    
    print(f"\nReport saved to: {filename}")


def generate_comprehensive_report(credentials) -> List[Tuple[str, str, str, str, str, bool, bool, str]]:
    """Generate a comprehensive report including organizations, billing accounts, and subaccounts."""
    print("Fetching organizations...")
    organizations, subaccounts = get_all_organizations(credentials)
    
    print("Fetching billing accounts...")
    billing_accounts = get_billing_accounts(credentials)
    
    print("Checking access permissions...")
    comprehensive_data = []
    
    # Get current user email for display
    user_email = get_user_email_from_gcloud()
    print(f"Generating report for user: {user_email}")
    
    # First, let's check which billing accounts the user actually has access to
    accessible_billing_accounts = []
    for billing_account in billing_accounts:
        if check_billing_access(credentials, billing_account['name']):
            accessible_billing_accounts.append(billing_account)
            print(f"  User has access to billing account: {billing_account.get('displayName', 'Unknown')} ({billing_account['name']})")
            # Debug: Show billing account details
            print(f"    - Parent: {billing_account.get('parent', 'None')}")
            print(f"    - Master: {billing_account.get('masterBillingAccount', 'None')}")
            print(f"    - Open: {billing_account.get('open', 'Unknown')}")
            
            # Check if this billing account is linked to an organization
            parent = billing_account.get('parent', '')
            master = billing_account.get('masterBillingAccount', '')
            if parent.startswith('organizations/') or master.startswith('organizations/'):
                org_id = parent if parent.startswith('organizations/') else master
                print(f"    - Linked to organization: {org_id}")
    
    print(f"Total accessible billing accounts: {len(accessible_billing_accounts)}")
    
    # Debug: Show all organizations
    print(f"Total organizations found: {len(organizations)}")
    for org in organizations:
        print(f"  - {org['displayName']}: {org['name']}")
        
        # Show which billing accounts are linked to this org
        linked_billing_accounts = []
        for billing_account in accessible_billing_accounts:
            if (billing_account.get('parent') == org['name'] or 
                billing_account.get('masterBillingAccount') == org['name']):
                linked_billing_accounts.append(billing_account.get('displayName', 'Unknown'))
        
        if linked_billing_accounts:
            print(f"    Linked billing accounts: {', '.join(linked_billing_accounts)}")
        else:
            print(f"    No directly linked billing accounts found")
    
    # Process Organizations
    for org in organizations:
        org_name = org['displayName']
        org_id = org['name']
        
        print(f"  Checking access for organization: {org_name}")
        
        # Check GCP console access
        has_gcp_access = check_org_access(credentials, org_id)
        
        # Check billing access - improved logic
        has_billing_access = False
        billing_notes = []
        
        # Method 1: Check if any accessible billing account is linked to this org
        for billing_account in accessible_billing_accounts:
            # Check direct parent relationship
            if billing_account.get('parent') == org_id:
                has_billing_access = True
                billing_notes.append(f"Direct parent: {billing_account.get('displayName', 'Unknown')}")
                print(f"    Billing access via direct parent relationship")
                break
            
            # Check master billing account relationship
            if billing_account.get('masterBillingAccount') == org_id:
                has_billing_access = True
                billing_notes.append(f"Master account: {billing_account.get('displayName', 'Unknown')}")
                print(f"    Billing access via master billing account")
                break
        
        # Method 2: If no direct link found, check if user can access billing for this org
        if not has_billing_access:
            try:
                # Try to get billing accounts in the context of this organization
                service = build('cloudbilling', 'v1', credentials=credentials)
                # This is a bit tricky - we'll check if the user can access any billing
                # information related to this organization
                for billing_account in accessible_billing_accounts:
                    # Check if the billing account name contains the org ID or if we can
                    # access billing info for this org through the billing account
                    if org_id in billing_account.get('name', '') or org_id in billing_account.get('displayName', ''):
                        has_billing_access = True
                        billing_notes.append(f"Associated: {billing_account.get('displayName', 'Unknown')}")
                        print(f"    Billing access via billing account association")
                        break
            except Exception as e:
                print(f"    Error checking org-specific billing access: {e}")
        
        # Method 3: Check if user has billing viewer role at the organization level
        if not has_billing_access:
            try:
                service = build('cloudresourcemanager', 'v1', credentials=credentials)
                request = service.organizations().getIamPolicy(resource=org_id)
                policy = request.execute()
                
                for binding in policy.get('bindings', []):
                    role = binding['role']
                    # Check for billing-related roles at org level
                    if any(billing_role in role for billing_role in ['billing.admin', 'billing.user', 'billing.viewer']):
                        for member in binding.get('members', []):
                            if member == f'user:{user_email}' or member == 'allUsers' or member.startswith('group:'):
                                has_billing_access = True
                                billing_notes.append(f"Org-level role: {role}")
                                print(f"    Billing access via organization-level IAM role: {role}")
                                break
                        if has_billing_access:
                            break
            except Exception as e:
                print(f"    Error checking org-level billing roles: {e}")
        
        comprehensive_data.append(('Organization', org_name, org_id, 'N/A', 'Active', has_billing_access, has_gcp_access, '; '.join(billing_notes)))
    
    # Process Billing Subaccounts
    for subaccount in subaccounts:
        comprehensive_data.append((
            'Billing Subaccount',
            subaccount['name'],
            subaccount['id'],
            subaccount['master_account'],
            'Active' if subaccount['status'] else 'Inactive',
            True,  # If we can see it, we have billing access
            False,  # Subaccounts don't have direct GCP console access
            f"Subaccount of {subaccount['master_account']}"
        ))
    
    # Process Standalone Billing Accounts (not linked to any org)
    for billing_account in accessible_billing_accounts:
        # Check if this billing account is not already covered as a subaccount
        is_subaccount = any(sub['id'] == billing_account['name'] for sub in subaccounts)
        is_linked_to_org = any(
            billing_account.get('parent') == org['name'] or 
            billing_account.get('masterBillingAccount') == org['name'] 
            for org in organizations
        )
        
        if not is_subaccount and not is_linked_to_org:
            comprehensive_data.append((
                'Standalone Billing Account',
                billing_account.get('displayName', 'Unknown'),
                billing_account['name'],
                billing_account.get('masterBillingAccount', 'N/A'),
                'Active' if billing_account.get('open', False) else 'Inactive',
                True,  # If we can see it, we have billing access
                False,  # Standalone billing accounts don't have direct GCP console access
                'Standalone billing account not linked to any organization'
            ))
    
    return comprehensive_data


def save_comprehensive_csv(report_data: List[Tuple[str, str, str, str, str, bool, bool, str]], filename: str = 'gcp_comprehensive_access_report.csv'):
    """Save the comprehensive report data to a CSV file."""
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow(['Type', 'Name', 'ID', 'Parent/Master', 'Status', 'Billing Console Access', 'GCP Console Access', 'Notes'])
        
        # Write data
        for row in report_data:
            writer.writerow([
                row[0],  # Type
                row[1],  # Name
                row[2],  # ID
                row[3],  # Parent/Master
                row[4],  # Status
                'Yes' if row[5] else 'No',  # Billing Console Access
                'Yes' if row[6] else 'No',  # GCP Console Access
                row[7]   # Notes
            ])
    
    print(f"\nComprehensive report saved to: {filename}")


def main():
    """Main function to generate the access report."""
    print("GCP Comprehensive Access Report Generator")
    print("=" * 50)
    
    # Get credentials
    credentials = get_credentials()
    
    # Generate comprehensive report
    comprehensive_data = generate_comprehensive_report(credentials)
    
    if not comprehensive_data:
        print("No resources found or no access to retrieve information.")
        return
    
    # Count by type
    org_count = sum(1 for row in comprehensive_data if row[0] == 'Organization')
    subaccount_count = sum(1 for row in comprehensive_data if row[0] == 'Billing Subaccount')
    standalone_count = sum(1 for row in comprehensive_data if row[0] == 'Standalone Billing Account')
    
    # Display summary
    print(f"\nSummary:")
    print(f"Total resources: {len(comprehensive_data)}")
    print(f"  - Organizations: {org_count}")
    print(f"  - Billing Subaccounts: {subaccount_count}")
    print(f"  - Standalone Billing Accounts: {standalone_count}")
    
    billing_access_count = sum(1 for row in comprehensive_data if row[5])
    gcp_access_count = sum(1 for row in comprehensive_data if row[6])
    print(f"Resources with billing access: {billing_access_count}")
    print(f"Resources with GCP console access: {gcp_access_count}")
    
    # Save comprehensive CSV
    save_comprehensive_csv(comprehensive_data)
    
    # Display detailed results
    print(f"\nDetailed Results:")
    print(f"{'Type':<20} {'Name':<30} {'Billing':<15} {'GCP Console':<15}")
    print("-" * 80)
    for row in comprehensive_data:
        print(f"{row[0]:<20} {row[1]:<30} {'Yes' if row[5] else 'No':<15} {'Yes' if row[6] else 'No':<15}")
    
    # Special investigation for premier.cloudbakers.com
    print(f"\n" + "="*60)
    print("SPECIAL INVESTIGATION: premier.cloudbakers.com")
    print("="*60)
    investigate_organization_access(credentials, "premier.cloudbakers.com", "organizations/387978708188")
    
    # Show all discovered subaccounts
    print(f"\n" + "="*60)
    print("ALL DISCOVERED BILLING SUBACCOUNTS")
    print("="*60)
    organizations, subaccounts = get_all_organizations(credentials)
    
    if subaccounts:
        print(f"Found {len(subaccounts)} billing subaccounts:")
        for subaccount in subaccounts:
            print(f"  - {subaccount['name']}")
            print(f"    ID: {subaccount['id']}")
            print(f"    Master: {subaccount['master_account']}")
            print(f"    Status: {subaccount['status']}")
            print()
    else:
        print("No billing subaccounts found.")


if __name__ == '__main__':
    main() 