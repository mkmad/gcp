# Overview
In this lab, you set up a VM server.

You use an e2-medium machine type that includes a 10-GB boot disk, 2 virtual CPU (vCPU), and 4 GB of RAM. 
This machine type runs Debian Linux by default.

To make sure there is plenty of room for the  data, you also attach a high-performance 
50-GB persistent solid-state drive (SSD) to the instance.

# Objectives
In this lab, you learn how to perform the following tasks:

- Customize an application server
- Install and configure necessary software
- Configure network access
- Schedule regular backups

# Create VM

Define a VM using advanced options
- In the Cloud Console, on the Navigation menu (Navigation menu), click Compute Engine > VM instances.
- Click Create Instance.
- Specify the following and leave the remaining settings as their defaults:
```
Name	                                    mc-server
Region	                                    REGION
Zone	                                    ZONE
Boot disk	                                Debian GNU/Linux 11 (bullseye)
Identity and API access > Access scopes	    Set access for each API
Storage	Read Write
```
- Click Advanced options.
- Click Disks. You will add a disk to be used for game storage.
- Click Add new disk.
- Specify the following and leave the remaining settings as their defaults:
```
Name	            minecraft-disk
Disk type	        SSD Persistent Disk
Disk Source type	Blank disk
Size (GB)	        50
Encryption	        Google-managed encryption key
```
- Click Save. This creates the disk and automatically attaches it to the VM when the VM is created.
- Click Networking.
- Specify the following and leave the remaining settings as their defaults:
```
Network tags	        minecraft-server
Network interfaces	    Click default to edit the interface
External IPv4 address	Reserve Static External IP Address
Name	                mc-server-ip
```
- Click Reserve.
- Click Done.
- Click Create.

# Prepare the data disk

## Create a directory and format and mount the disk

The disk is attached to the instance, but it is not yet mounted or formatted.

- For mc-server, click SSH to open a terminal and connect.
- To create a directory that serves as the mount point for the data disk, run the following command:
```
sudo mkdir -p /home/minecraft
```
- To format the disk, run the following command:
```
sudo mkfs.ext4 -F -E lazy_itable_init=0,\
lazy_journal_init=0,discard \
/dev/disk/by-id/google-minecraft-disk
```
- To mount the disk, run the following command:
```
sudo mount -o discard,defaults /dev/disk/by-id/google-minecraft-disk /home/minecraft
```

# Allow client traffic

Up to this point, the server has an external static IP address, but it cannot receive traffic because there is no firewall rule in 
place. Minecraft server uses TCP port 25565 by default. So you need to configure a firewall rule to allow these connections.

## Create a firewall rule

- In the Cloud Console, on the Navigation menu (Navigation menu), click VPC network > Firewall.
- Click Create firewall rule.
- Specify the following and leave the remaining settings as their defaults:
```
Name	                minecraft-rule
Target	                Specified target tags
Target tags	            minecraft-server
Source filter	        IPv4 ranges
Source IPv4 ranges	    0.0.0.0/0
Protocols and ports	    Specified protocols and ports
```
- For tcp, specify port 25565.
- Click Create. Users can now access your server from their Minecraft clients.

# Schedule regular backups

Backing up your application data is a common activity. In this case, you configure the system to back up Minecraft world data to Cloud Storage.

## Create a Cloud Storage bucket

- On the Navigation menu (Navigation menu), click Compute Engine > VM instances.
- For mc-server, click SSH.
- Create a globally unique bucket name, and store it in the environment variable YOUR_BUCKET_NAME. To make it unique, you can use your Project ID. Run the following command:
```
export YOUR_BUCKET_NAME=<Enter your bucket name here>
```
To create the bucket using the gcloud storage tool, part of the Cloud SDK, run the following command:
```
gcloud storage buckets create gs://$YOUR_BUCKET_NAME-minecraft-backup
```

## Create a backup script

- In the mc-server SSH terminal, navigate to your home directory:
```
cd /home/minecraft
```
- To create the script, run the following command:
```
sudo nano /home/minecraft/backup.sh
```
Copy and paste the following script into the file:
```
#!/bin/bash
screen -r mcs -X stuff '/save-all\n/save-off\n'
/usr/bin/gcloud storage cp -R ${BASH_SOURCE%/*}/world gs://${YOUR_BUCKET_NAME}-minecraft-backup/$(date "+%Y%m%d-%H%M%S")-world
screen -r mcs -X stuff '/save-on\n'
```
Note: The script saves the current state of the server's world data and pauses the server's auto-save functionality. Next, 
it backs up the server's world data directory (world) and places its contents in a timestamped directory (<timestamp>-world) 
in the Cloud Storage bucket. After the script finishes backing up the data, it resumes auto-saving on the Minecraft server.

- To make the script executable, run the following command:
```
sudo chmod 755 /home/minecraft/backup.sh
```

## Test the backup script and schedule a cron job

- In the mc-server SSH terminal, run the backup script:
```
. /home/minecraft/backup.sh
```
- After the script finishes, return to the Cloud Console.
- To verify that the backup file was written, on the Navigation menu ( Navigation menu icon), click Cloud Storage > Buckets.
- Click on the backup bucket name. You should see a folder with a date-time stamp name. Now that you've verified that the backups are working, you can schedule a cron job to automate the task.
- In the mc-server SSH terminal, open the cron table for editing:
```
sudo crontab -e
```
- When you are prompted to select an editor, type the number corresponding to nano, and press ENTER.
- At the bottom of the cron table, paste the following line:
```
0 */4 * * * /home/minecraft/backup.sh
```

# Server maintenance

## Automate server maintenance with startup and shutdown scripts
Instead of following the manual process to mount the persistent disk and launch the server application in a screen, you can use metadata scripts to create a startup script and a shutdown script to do this for you.

- Click mc-server.
- Click Edit.
- For Metadata, click + Add Item and specify the following:
```
Key	                    Value
startup-script-url	    https://storage.googleapis.com/cloud-training/archinfra/mcserver/startup.sh
shutdown-script-url	    https://storage.googleapis.com/cloud-training/archinfra/mcserver/shutdown.sh
```
- Click Save.

