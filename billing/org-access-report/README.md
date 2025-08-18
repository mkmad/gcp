# GCP Organization Access Report Generator

This tool generates comprehensive CSV reports showing your access across all GCP organizations, billing accounts, and subaccounts. It includes:
1. Organization name and access details
2. Billing console access (view access)
3. GCP console access (view access)
4. Billing subaccounts and their relationships
5. Standalone billing accounts

## Overview

This tool provides two different approaches:

### 1. API-Based Script (Original)
- Uses Google Cloud APIs directly
- May have permission limitations
- Generates basic organization access report

### 2. gcloud-Based Script (Recommended)
- Uses gcloud CLI commands
- Bypasses API permission issues
- Discovers all billing subaccounts and relationships
- Generates comprehensive reports

## Prerequisites

1. **Python 3.7+** installed on your system
2. **Google Cloud SDK** installed and configured
3. **Active GCP session** with appropriate permissions
4. **gcloud CLI** authenticated and configured

## Installation

1. **Navigate to the org-access-report directory:**
   ```bash
   cd gcp/billing/org-access-report
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Authenticate with Google Cloud:**
   ```bash
   gcloud auth application-default login
   ```

4. **Set the correct project (if needed):**
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

## Usage

### Recommended: gcloud-Based Script

**Run the comprehensive report:**
```bash
python gcloud_billing_report.py
```

This script will:
- Discover all organizations you have access to
- Find all billing subaccounts and their master accounts
- Identify standalone billing accounts
- Generate a comprehensive CSV: `gcp_gcloud_comprehensive_report.csv`
- Display detailed results including billing subaccounts

### Alternative: API-Based Script

**Run the basic report:**
```bash
python org_access_report.py
```

**Or use the launcher script:**
```bash
./run_report.sh
```

## Output Files

### Comprehensive Report (`gcp_gcloud_comprehensive_report.csv`)
Contains detailed information about:
- **Organizations**: All GCP organizations with access details
- **Billing Subaccounts**: All subaccounts linked to master billing accounts
- **Standalone Billing Accounts**: Billing accounts not linked to organizations

Columns:
- **Type**: Organization, Billing Subaccount, or Standalone Billing Account
- **Name**: Display name of the resource
- **ID**: Resource identifier
- **Parent/Master**: Parent organization or master billing account
- **Status**: Active/Inactive status
- **Billing Console Access**: Yes/No
- **GCP Console Access**: Yes/No
- **Notes**: Additional context and relationships

### Basic Report (`gcp_org_access_report.csv`)
Contains organization-level access information:
- **Organization Name**: Display name of the GCP organization
- **Billing Console Access**: "Yes" if you have view access to billing, "No" otherwise
- **GCP Console Access**: "Yes" if you have view access to the GCP console, "No" otherwise

## Sample Output

### Comprehensive Report Summary
```
GCP Comprehensive Access Report Generator (gcloud version)
============================================================
Getting billing accounts via gcloud...
Found 1159 billing accounts
Getting organizations via gcloud...
Found 289 organizations
Analyzing billing account relationships...
Found 1159 billing subaccounts

Summary:
Total resources: 1448
  - Organizations: 289
  - Billing Subaccounts: 1159
  - Standalone Billing Accounts: 0
Resources with billing access: 1448
Resources with GCP console access: 289

Comprehensive report saved to: gcp_gcloud_comprehensive_report.csv
```

### Billing Subaccounts Found
```
BILLING SUBACCOUNTS FOUND
============================================================
  - onXmaps, Inc. - Cloudbakers (Master: billingAccounts/0078AA-34EC5B-80DDA4)
  - Vacasa - Cloudbakers (Master: billingAccounts/0078AA-34EC5B-80DDA4)
  - Forte.io - Cloudbakers (Master: billingAccounts/0078AA-34EC5B-80DDA4)
  ...
```

## Key Features

### Comprehensive Discovery
- **Organizations**: All GCP organizations you can access
- **Billing Subaccounts**: All subaccounts under master billing accounts
- **Master Account Relationships**: Clear mapping of subaccounts to their master accounts
- **Access Verification**: Detailed billing and console access status

### Robust Data Collection
- **gcloud CLI Integration**: Uses your existing gcloud authentication
- **Permission Bypass**: Avoids API permission issues
- **Complete Coverage**: Discovers resources that API-based scripts might miss
- **Relationship Mapping**: Shows hierarchical billing account structures

### Detailed Reporting
- **Multiple Resource Types**: Organizations, subaccounts, and standalone accounts
- **Access Status**: Clear indication of billing and console access
- **Relationship Context**: Parent/master account information
- **Status Information**: Active/inactive status for all resources

## Troubleshooting

### Common Issues

1. **"No default credentials found"**
   - Run: `gcloud auth application-default login`
   - Make sure you're logged into the correct Google account

2. **Permission denied errors (API script)**
   - Use the gcloud-based script instead: `python gcloud_billing_report.py`
   - The gcloud script bypasses API permission issues

3. **Missing billing subaccounts**
   - The API-based script may miss subaccounts due to permission limitations
   - Use the gcloud-based script for complete discovery

4. **Wrong project context**
   - Set the correct project: `gcloud config set project YOUR_PROJECT_ID`
   - Verify with: `gcloud config get-value project`

### Required IAM Roles

To run this script, you need at least one of these roles:
- **Organization level:**
  - `roles/resourcemanager.organizationViewer`
  - `roles/resourcemanager.organizationMember`
  - `roles/resourcemanager.organizationAdmin`

- **Billing level:**
  - `roles/billing.viewer`
  - `roles/billing.user`
  - `roles/billing.admin`

## Security Notes

- The script only reads access information, it doesn't modify any permissions
- Credentials are stored locally and not shared
- The CSV output contains only organization names, billing account names, and access status
- No sensitive billing or resource information is included in the report
- gcloud commands use your existing authenticated session

## Use Cases

### For GCP Administrators
- Audit user access across all organizations
- Identify billing account relationships
- Track subaccount structures
- Verify access permissions

### For Billing Management
- Discover all billing subaccounts
- Map subaccounts to master accounts
- Verify billing console access
- Identify standalone billing accounts

### For Access Auditing
- Comprehensive access inventory
- Relationship mapping
- Permission verification
- Compliance reporting

## Customization

You can modify the scripts to:
- Add more detailed permission checks
- Include additional organization metadata
- Filter organizations by specific criteria
- Change the output format (JSON, Excel, etc.)
- Add custom access validation logic

## File Structure

```
org-access-report/
├── org_access_report.py          # API-based script (original)
├── gcloud_billing_report.py      # gcloud-based script (recommended)
├── run_report.sh                 # Launcher script
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── gcp_org_access_report.csv     # Basic API report output
└── gcp_gcloud_comprehensive_report.csv  # Comprehensive gcloud report output
```

## Support

If you encounter issues:
1. **For API permission issues**: Use the gcloud-based script
2. **For authentication issues**: Run `gcloud auth application-default login`
3. **For project context issues**: Set the correct project with `gcloud config set project`
4. **For missing data**: The gcloud script provides the most comprehensive discovery

## Recent Updates

- **Added gcloud-based script**: Bypasses API permission issues
- **Enhanced discovery**: Finds all billing subaccounts and relationships
- **Comprehensive reporting**: Includes organizations, subaccounts, and standalone accounts
- **Improved troubleshooting**: Better error handling and guidance
- **Relationship mapping**: Shows master account to subaccount relationships 