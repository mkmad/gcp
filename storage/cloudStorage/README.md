# Overview

In this lab, you create a Cloud Storage bucket and place an image in it. For this lab, you configure a web server with PHP, a web development environment that is the basis for popular blogging software. Outside this lab, you will use analogous techniques to configure these packages.

You also configure the web server to reference the image in the Cloud Storage bucket.

# Objectives

In this lab, you learn how to perform the following tasks:

- Create a Cloud Storage bucket and place an image into it.
- Use the image in the Cloud Storage bucket on a web page.

# Deploy a web server VM instance

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

# Create a Cloud Storage bucket using the gcloud storage command line

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

# Configure an application in a Compute Engine instance to use a Cloud Storage object

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

