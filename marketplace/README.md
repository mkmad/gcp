# Overview

In this lab, you use Google Cloud Marketplace to quickly and easily deploy a LAMP stack on a Compute Engine instance. The Bitnami LAMP Stack provides a complete web development environment for Linux that can be launched in one click.

Component	                   Role
Linux	                 Operating system
Apache HTTP Server	        Web server
MySQL	                Relational database
PHP	                 Web application framework
phpMyAdmin	          PHP administration tool


# Use Cloud Marketplace to deploy a LAMP stack

- In the Google Cloud Console, on the Navigation menu (=), click Marketplace.

- In the search bar, type LAMP and then press ENTER.

- In the search results, click Bitnami package for LAMP.

- If you choose another LAMP stack, such as the Google Click to Deploy offering, the lab instructions will not work as expected.

- On the LAMP page, click GET STARTED.

- On the Agreements page, check the box for Terms and agreements, and click AGREE.

- On the Successfully agreed to terms pop up, click DEPLOY.

- If this is your first time using Compute Engine, the Compute Engine API must be initialized before you can continue.

- For Zone, select the deployment zone to us-west1-c .

- For Machine Type, select E2 as the Series and e2-medium as the Machine Type.

- Leave the remaining settings as their defaults.

- Click Deploy.

- If a Welcome to Deployment Manager message appears, click Close to dismiss it.

When the deployment is complete, click the Site address link in the right pane. (If the website is not responding, wait 30 seconds and try again.) If you see a redirection notice, click on that link to view your new site.
