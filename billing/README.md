# GCP Organization Access Report Generator

This script generates a CSV report showing your access across all GCP organizations, including:
1. Organization name
2. Billing console access (view access)
3. GCP console access (view access)

## Prerequisites

1. **Python 3.7+** installed on your system
2. **Google Cloud SDK** installed and configured
3. **Active GCP session** with appropriate permissions

## Installation

1. **Navigate to the billing directory:**
   ```bash
   cd gcp/billing
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Authenticate with Google Cloud:**
   ```bash
   gcloud auth application-default login
   ```

## Usage

1. **Run the script:**
   ```bash
   python org_access_report.py
   ```

   **Or use the launcher script:**
   ```bash
   ./run_report.sh
   ```

2. **The script will:**
   - Fetch all organizations you have access to
   - Check your billing console access for each organization
   - Check your GCP console access for each organization
   - Generate a CSV file: `gcp_org_access_report.csv`
   - Display results in the terminal

## Output

The script generates a CSV file with the following columns:
- **Organization Name**: Display name of the GCP organization
- **Billing Console Access**: "Yes" if you have view access to billing, "No" otherwise
- **GCP Console Access**: "Yes" if you have view access to the GCP console, "No" otherwise

## Sample Output

```
GCP Organization Access Report Generator
==================================================
Fetching organizations...
Fetching billing accounts...
Checking access permissions...
Generating report for user: your.email@domain.com
  Checking access for organization: Organization A
  Checking access for organization: Organization B
  ...

Summary:
Total organizations: 15
Organizations with billing access: 8
Organizations with GCP console access: 12

Report saved to: gcp_org_access_report.csv

Detailed Results:
Organization                    Billing         GCP Console    
------------------------------------------------------------
Organization A                 Yes             Yes            
Organization B                 No              Yes            
...
```

## Troubleshooting

### Common Issues

1. **"No default credentials found"**
   - Run: `gcloud auth application-default login`
   - Make sure you're logged into the correct Google account

2. **Permission denied errors**
   - Ensure your account has the necessary IAM roles:
     - `roles/resourcemanager.organizationViewer` (minimum for org access)
     - `roles/billing.viewer` (minimum for billing access)
   - Contact your GCP admin if you need elevated permissions

3. **API not enabled errors**
   - The script automatically uses the required APIs:
     - Cloud Resource Manager API
     - Cloud Billing API
     - OAuth2 API

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
- The CSV output contains only organization names and access status
- No sensitive billing or resource information is included in the report

## Customization

You can modify the script to:
- Add more detailed permission checks
- Include additional organization metadata
- Filter organizations by specific criteria
- Change the output format (JSON, Excel, etc.)

## Support

If you encounter issues:
1. Check the error messages in the terminal output
2. Verify your GCP permissions and authentication
3. Ensure all required APIs are enabled in your projects 