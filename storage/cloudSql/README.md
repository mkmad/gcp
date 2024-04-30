# Overview

In this lab, you will configure an application running in Compute Engine to use a database managed by Cloud SQL. For this lab, you configure a web server with PHP, a web development environment that is the basis for popular blogging software. Outside this lab, you will use analogous techniques to configure these packages.

# Objectives

In this lab, you learn how to perform the following tasks:

- Create a Cloud SQL instance and configure it.
- Connect to the Cloud SQL instance from a web server.

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

# Create the Cloud SQL instance

- Follow basic setup in the Google Cloud console, on the Navigation menu (Navigation menu icon), click SQL.
- For Instance ID, type blog-db, and for Root password type a password of your choice.
- For Choose a Cloud SQL edition, click Enterprise and then select Sandbox from the dropdown.
- From the SQL instances details page, copy the Public IP address for your SQL instance to a text editor for use later in this lab.
- Click Users menu on the left-hand side, and then click Add User Account. 
- Click Connections menu on the left-hand side, and then click Networking tab >> ADD Network.
- For Network, type the external IP address of your bloghost VM instance, followed by /32

# Configure an application in a Compute Engine instance to use Cloud SQL

- SSH into the VM instance from above
- Edit /var/www/html/index.php and paste the following code:

```
<html>
<head><title>Welcome to my excellent blog</title></head>
<body>
<h1>Welcome to my excellent blog</h1>
<?php
 $dbserver = "CLOUDSQLIP";
$dbuser = "blogdbuser";
$dbpassword = "DBPASSWORD";
// In a production blog, we would not store the MySQL
// password in the document root. Instead, we would store
//  it in a Secret Manger. For more information see 
// https://cloud.google.com/sql/docs/postgres/use-secret-manager

$conn = new mysqli($dbserver, $dbuser, $dbpassword);

if (mysqli_connect_error()) {
        echo ("Database connection failed: " . mysqli_connect_error());
} else {
        echo ("Database connection succeeded.");
}
?>
</body></html>
```

- restart the web server

```
sudo service apache2 restart
```




