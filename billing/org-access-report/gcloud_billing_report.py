#!/usr/bin/env python3
"""
GCP Organization Access Report Generator using gcloud commands

This script uses gcloud CLI commands to get billing and organization data
since the API approach has permission issues.
"""

import csv
import json
import subprocess
import sys
from typing import Dict, List, Tuple


def run_gcloud_command(command: List[str]) -> str:
    """Run a gcloud command and return the output."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(command)}: {e}")
        return ""


def get_billing_accounts() -> List[Dict]:
    """Get billing accounts using gcloud command."""
    print("Getting billing accounts via gcloud...")
    
    # Get billing accounts in JSON format
    output = run_gcloud_command([
        'gcloud', 'billing', 'accounts', 'list', '--format=json'
    ])
    
    if not output:
        return []
    
    try:
        accounts = json.loads(output)
        print(f"Found {len(accounts)} billing accounts")
        return accounts
    except json.JSONDecodeError as e:
        print(f"Error parsing billing accounts JSON: {e}")
        return []


def get_organizations() -> List[Dict]:
    """Get organizations using gcloud command."""
    print("Getting organizations via gcloud...")
    
    # Get organizations in JSON format
    output = run_gcloud_command([
        'gcloud', 'organizations', 'list', '--format=json'
    ])
    
    if not output:
        return []
    
    try:
        orgs = json.loads(output)
        print(f"Found {len(orgs)} organizations")
        return orgs
    except json.JSONDecodeError as e:
        print(f"Error parsing organizations JSON: {e}")
        return []


def get_user_email() -> str:
    """Get current user email."""
    output = run_gcloud_command(['gcloud', 'config', 'get-value', 'account'])
    return output if output else 'unknown@example.com'


def analyze_billing_accounts(billing_accounts: List[Dict]) -> List[Dict]:
    """Analyze billing accounts to find subaccounts and relationships."""
    print("Analyzing billing account relationships...")
    
    # Group by master billing account
    master_accounts = {}
    subaccounts = []
    
    for account in billing_accounts:
        account_name = account.get('displayName', 'Unknown')
        account_id = account.get('name', '')
        
        # Check if this is a subaccount
        if account.get('masterBillingAccount'):
            master_id = account['masterBillingAccount']
            subaccounts.append({
                'name': account_name,
                'id': account_id,
                'master_account': master_id,
                'type': 'subaccount',
                'status': 'Active' if account.get('open', False) else 'Inactive'
            })
            
            if master_id not in master_accounts:
                master_accounts[master_id] = []
            master_accounts[master_id].append(account_name)
    
    print(f"Found {len(subaccounts)} billing subaccounts")
    
    # Show master account relationships
    for master_id, subaccount_names in master_accounts.items():
        print(f"  Master account {master_id} has subaccounts: {', '.join(subaccount_names)}")
    
    return subaccounts


def generate_comprehensive_report():
    """Generate comprehensive report using gcloud data."""
    print("GCP Comprehensive Access Report Generator (gcloud version)")
    print("=" * 60)
    
    # Get current user
    user_email = get_user_email()
    print(f"Generating report for user: {user_email}")
    
    # Get data via gcloud
    billing_accounts = get_billing_accounts()
    organizations = get_organizations()
    subaccounts = analyze_billing_accounts(billing_accounts)
    
    # Prepare comprehensive data
    comprehensive_data = []
    
    # Add organizations
    for org in organizations:
        org_name = org.get('displayName', 'Unknown')
        org_id = org.get('name', '')
        
        # For now, assume billing access if we can see the org
        # and GCP console access if we can list it
        comprehensive_data.append((
            'Organization',
            org_name,
            org_id,
            'N/A',
            'Active',
            True,  # We can see it, so likely have billing access
            True,  # We can see it, so likely have console access
            'Discovered via gcloud organizations list'
        ))
    
    # Add billing subaccounts
    for subaccount in subaccounts:
        comprehensive_data.append((
            'Billing Subaccount',
            subaccount['name'],
            subaccount['id'],
            subaccount['master_account'],
            subaccount['status'],
            True,  # If we can see it, we have billing access
            False,  # Subaccounts don't have direct GCP console access
            f"Subaccount of {subaccount['master_account']}"
        ))
    
    # Add standalone billing accounts (not subaccounts)
    for account in billing_accounts:
        # Check if this is not a subaccount
        if not account.get('masterBillingAccount'):
            account_name = account.get('displayName', 'Unknown')
            account_id = account.get('name', '')
            
            # Check if this account is not already covered as an organization
            is_org = any(org.get('name') == account_id for org in organizations)
            
            if not is_org:
                comprehensive_data.append((
                    'Standalone Billing Account',
                    account_name,
                    account_id,
                    'N/A',
                    'Active' if account.get('open', False) else 'Inactive',
                    True,  # If we can see it, we have billing access
                    False,  # Standalone billing accounts don't have direct GCP console access
                    'Standalone billing account not linked to any organization'
                ))
    
    return comprehensive_data


def save_comprehensive_csv(report_data: List[Tuple], filename: str = 'gcp_gcloud_comprehensive_report.csv'):
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
    """Main function."""
    # Generate comprehensive report
    comprehensive_data = generate_comprehensive_report()
    
    if not comprehensive_data:
        print("No resources found.")
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
    
    # Show specific subaccounts
    print(f"\n" + "="*60)
    print("BILLING SUBACCOUNTS FOUND")
    print("="*60)
    subaccounts = [row for row in comprehensive_data if row[0] == 'Billing Subaccount']
    for subaccount in subaccounts:
        print(f"  - {subaccount[1]} (Master: {subaccount[3]})")


if __name__ == '__main__':
    main() 