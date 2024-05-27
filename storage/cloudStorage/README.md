# Overview

In this lab, you create a Cloud Storage bucket and place an image in it. For this lab, you configure a web server with PHP, a web development environment that is the basis for popular blogging software. Outside this lab, you will use analogous techniques to configure these packages.

You also configure the web server to reference the image in the Cloud Storage bucket.

# Objectives

In this lab, you learn how to perform the following tasks:

- Create a Cloud Storage bucket and place an image into it.
- Use the image in the Cloud Storage bucket on a web page.
- Use your own encryption keys
- Implement version controls
- Use directory synchronization
- Share a bucket across projects using IAM Service Accounts


## Deploy a web server VM instance

- In the Google Cloud console, on the Navigation menu (Navigation menu icon), click Compute Engine > VM instances.
- Click Create Instance.
- On the Create an Instance page, for Name, type bloghost
- For Region and Zone, select the region and zone assigned by Qwiklabs.
- For Machine type, accept the default.
- For Boot disk, if the Image shown is not Debian GNU/Linux 11 (bullseye), click Change and select Debian GNU/Linux 11 (bullseye).
- Leave the defaults for Identity and API access unmodified.
- For Firewall, click Allow HTTP traffic.
- Click Advanced options to open that section of the dialog.
- Click Management to open that section of the dialog.
- Scroll down to the Automation section, and enter the following script as the value for Startup script:

```
apt-get update
apt-get install apache2 php php-mysql -y
service apache2 restart
```
- Leave the remaining settings as their defaults, and click Create.
- On the VM instances page, copy the bloghost VM instance's internal and external IP addresses to a text editor for use later in this lab.

# #Create a Cloud Storage bucket using the gcloud storage command line

In Cloud Shell, the DEVSHELL_PROJECT_ID environment variable contains your project ID. Enter this command to make a bucket named after your project ID:

```
export LOCATION=US
gcloud storage buckets create -l $LOCATION gs://$DEVSHELL_PROJECT_ID

```

Retrieve a banner image from a publicly accessible Cloud Storage location:

```
gcloud storage cp gs://cloud-training/gcpfci/my-excellent-blog.png my-excellent-blog.png
```

Copy the banner image to your newly created Cloud Storage bucket:

```
gcloud storage cp my-excellent-blog.png gs://$DEVSHELL_PROJECT_ID/my-excellent-blog.png
```

Modify the Access Control List of the object you just created so that it's readable by everyone:

```
gsutil acl ch -u allUsers:R gs://$DEVSHELL_PROJECT_ID/my-excellent-blog.png
```

## Configure an application in a Compute Engine instance to use a Cloud Storage object

- SSH into the VM instance from above
- Edit /var/www/html/index.php and paste the following code:

```
<img src='https://storage.googleapis.com/qwiklabs-gcp-0005e186fa559a09/my-excellent-blog.png'>
```

- Restart the web server

```
sudo service apache2 restart
```

- Return to the web browser tab in which you opened your bloghost VM instance's external IP address. When you load the page, its content now includes a banner image.


## Customer-supplied encryption keys (CSEK)

- For the next step, you need an AES-256 base-64 key to encrypt the data in the bucket.

```
$ python3 -c 'import base64; import os; print(base64.encodebytes(os.urandom(32)))'

$ b'tmxElCaabWvJqR7uXEWQF39DhWTcDvChzuCmpHe6sb0=\n'
```

- Copy the value of the generated key excluding b' and \n' from the command output. Key should be in form of `tmxElCaabWvJqR7uXEWQF39DhWTcDvChzuCmpHe6sb0=`
- The encryption controls are contained in a gsutil configuration file named `.boto`.
```
Note: If the .boto file is empty, close the nano editor with Ctrl+X and generate a new .boto file using the gsutil config -n command. Then, try opening the file again with the above commands.
```
- Locate the line with "#encryption_key="
```
Before:
# encryption_key=

After:
encryption_key=tmxElCaabWvJqR7uXEWQF39DhWTcDvChzuCmpHe6sb0=
```

- Upload the remaining setup files (encrypted) and verify in the Cloud Console
```
gcloud storage cp my-excellent-blog-2.png gs://$DEVSHELL_PROJECT_ID/my-excellent-blog-2.png
```

- Now clicking on `gs://$DEVSHELL_PROJECT_ID/my-excellent-blog-2.png` will show that they are customer-encrypted.

## Customer-supplied decryption keys (CSEK)

- Similar to encryption key, generate a AES-256 base-64 key to decrypt the data from the bucket

```
$ python3 -c 'import base64; import os; print(base64.encodebytes(os.urandom(32)))

$ b'nW+rBmIXZQLeorU791CxE3msuNQ+FAU9R/wqckS0a2U=\n'
```

- modify the `.boto` file

```
Before:
encryption_key=2dFWQGnKhjOcz4h0CudPdVHLG2g+OoxP8FQOIKKTzsg=

# decryption_key1=

After:
encryption_key=2dFWQGnKhjOcz4h0CudPdVHLG2g+OoxP8FQOIKKTzsg=

decryption_key1=nW+rBmIXZQLeorU791CxE3msuNQ+FAU9R/wqckS0a2U=
```

## Enable versioning

To enable versioning, run the following command:

```
gsutil versioning set on gs://$BUCKET_NAME_1
```

## Synchronize a directory to a bucket

- Make a nested directory structure so that you can examine what happens when it is recursively copied to a bucket.

```
mkdir firstlevel
mkdir ./firstlevel/secondlevel
cp setup.html firstlevel
cp setup.html firstlevel/secondlevel
```

- To sync the `firstlevel` directory on the VM with your bucket, run the following command:
```
gsutil rsync -r ./firstlevel gs://$BUCKET_NAME_1/firstlevel
```
- Further changes in `secondlevel` or `firstlevel` will automatically synced to the storage bucket

## Cross-project sharing

### Create an IAM Service Account
- In the Cloud Console, on the Navigation menu (Navigation menu icon), click IAM & admin > Service accounts.
- Click Create service account.
- On Service account details page, specify the Service account name as `cross-project-storage`.
- Click Create and Continue.
- On the Service account permissions page, specify the role as Cloud Storage > Storage Object Viewer.
- Click on the Storage Object Viewer role, and then click Cloud Storage > Storage Object Admin.
- Click Continue and then Done.
- Click the `cross-project-storage` service account to add the JSON key.
- In Keys tab, click Add Key dropdown and select Create new key.
- Select JSON as the key type and click Create. A JSON key file will be downloaded. You will need to find this key file and upload it in into the VM in a later step.
- Click Close.
- On your hard drive, rename the JSON key file to `credentials.json`.

Now this service account can be use accross projects, 

- For example in another project create a VM and copy/upload the `credentials.json`
- Auth the SA using `gcloud` command
```
gcloud auth activate-service-account --key-file credentials.json
```
- `gcloud` (in turn the VM) should now have all the access the Service Account (from the other project) has to the bucket created above (in the other project).
