# Overview

Google Cloud’s Network Address Translation (NAT) service enables you to provision your application instances without public IP addresses while also allowing them to access the internet for updates, patching, config management, and more in a controlled and efficient manner.

In this lab, you will configure Private Google Access and Cloud NAT for a VM instance that doesn't have an external IP address. Then, you will verify access to public IP addresses of Google APIs and services and other connections to the internet. Finally, you will use Cloud NAT logging to record connections made in your gateway.

# Objectives

In this lab, you will learn how to perform the following tasks:

- Configure a VM instance that doesn't have an external IP address.
- Create a bastion host to connect to the VM that doesn't have an external IP address.
- Enable Private Google Access on a subnet.
- Verify access to public IP addresses of Google APIs and services
- Configure a Cloud NAT gateway. 
- Verify connections to the internet.
- Log NAT connections with Cloud NAT logging.

# Create a VPC network and firewall rules

- In the Cloud Console, on the Navigation menu (Navigation menu icon), click VPC network > VPC networks.
- Click Create VPC Network.
- For Name, type privatenet.
- For Subnet creation mode, click Custom.
- Specify the following, and leave the remaining settings as their defaults, don't enable Private Google access yet!
```
Name	            privatenet-us
Region	            Region
IP address range	10.130.0.0/20
```
- Click Done.
- Click Create and wait for the network to be created.
- In the left pane, click Firewall.
- Click Create Firewall Rule.
- Specify the following, and leave the remaining settings as their defaults:
```
Name	                    privatenet-allow-ssh
Network	                    privatenet
Targets	                    All instances in the network
Source filter	            IPv4 ranges
Source IPv4 ranges	        0.0.0.0/0
Protocols and ports	        Specified protocols and ports
```
- For tcp, specify port 22.
- Click Create.

# Create the VM instance with no public IP address

- In the Cloud Console, on the Navigation menu (Navigation menu icon), click Compute Engine > VM instances.
- Click Create Instance.
- Specify the following, and leave the remaining settings as their defaults:
```
Name	        vm-internal
Region	        Region
Zone	        Zone
Machine type	e2-medium(2 vCPU, 1 core, 4 GB memory)
```
- Click Advanced Options.
- Click Networking.
- For Network interfaces.
- Specify the following, and leave the remaining settings as their defaults:
```
Network	                      privatenet
Subnetwork	                  privatenet-us
External IPv4 address	      None
```
- Click Done.
- Click Create, and wait for the VM instance to be created.
- On the VM instances page, verify that the External IP of vm-internal is None.

# Create the bastion host

Because vm-internal has no external IP address, it can only be reached by other instances on the network or via a managed VPN gateway. This includes SSH access to vm-internal, which is grayed out (unavailable) in the Cloud Console.

In order to connect via SSH to vm-internal, create a bastion host vm-bastion on the same VPC network as vm-internal.

- In the Cloud Console, on the VM instances page, click Create Instance.
- Specify the following, and leave the remaining settings as their defaults:
```
Name	                                         vm-bastion
Region	                                         Region
Zone	                                         Zone
Machine type	                                 e2-micro (2vCPU)
Identity and API access > Access scopes	         Set access for each API
Compute Engine	                                 Read Write
```
- Click Advanced Options..
- Click Networking.
- For Network interfaces.
- Specify the following, and leave the remaining settings as their defaults:
```
Network	                privatenet
Subnetwork	            privatenet-us
External IPv4 address	Ephemeral
```
- Click Done.
- Click Create, and wait for the VM instance to be created.

From the vm-bastion SSH terminal, verify external connectivity by running the following command:

```
ping -c 2 www.google.com
```

# SSH to vm-bastion and verify access to vm-internal

Verify that you can access vm-internal through vm-bastion.

Connect to vm-internal by running the following command in the bastion host shell:
```
gcloud compute ssh vm-internal --zone=Zone --internal-ip
```

# Enable private Google access

VM instances that have no external IP addresses can use Private Google Access to reach external IP addresses of Google APIs and services. By default, Private Google Access is disabled on a VPC network.

Private Google access is enabled at the subnet level. When it is enabled, instances in the subnet that only have private IP addresses can send traffic to Google APIs and services through the default route (0.0.0.0/0) with a next hop to the default internet gateway.

- In the Cloud Console, on the Navigation menu (Navigation menu), click VPC network > VPC networks.
- Click privatenet > privatenet-us to open the subnet.
- Click Edit.
- For Private Google access, select On.
- Click Save.

Now you can access Google APIs and services through vm-internal. For example this should work

```
gsutil cp gs://[my_bucket]/*.png .
```

# Configure a Cloud NAT gateway

Although vm-internal can now access certain Google APIs and services without an external IP address, the instance cannot access the internet for updates and patches. You will now configure a Cloud NAT gateway, which allows vm-internal to reach the internet.

Cloud NAT is a regional resource. You can configure it to allow traffic from all ranges of all subnets in a region, from specific subnets in the region only, or from specific primary and secondary CIDR ranges only.


- In the Cloud Console, on the Navigation menu (Navigation menu icon), click Network services > Cloud NAT.
- Click Get started to configure a NAT gateway.
- Specify the following:
```
Gateway name	nat-config
Network	        privatenet
Region	        Region
```
- For Cloud Router, select Create new router.
- For Name, type nat-router.
- Click Create.

```
Note: The NAT mapping section allows you to choose the subnets to map to the NAT gateway. You can also manually assign static IP addresses that should be used when performing NAT. 
```

# Verify the Cloud NAT gateway

For vm-bastion, click SSH to launch a terminal and connect.
Connect to vm-internal by running the following command:
```
gcloud compute ssh vm-internal --zone=Zone --internal-ip
```
Try to re-synchronize the package index of vm-internal by running the following:
```
sudo apt-get update
```

This should now work!

Note: Connecting to `vm-internal` is via `baston` host, but `vm-internal` has access to internet via `nat-router` + `nat-gateway`.

# Configure and view logs with Cloud NAT Logging

Cloud NAT logging allows you to log NAT connections and errors. When Cloud NAT logging is enabled, one log entry can be generated for each of the following scenarios:

- When a network connection using NAT is created.
- When a packet is dropped because no port was available for NAT.

You can opt to log both kinds of events, or just one or the other. Created logs are sent to Cloud Logging.

- In the Cloud Console, on the Navigation menu (Navigation menu icon), click Network services > Cloud NAT.
- Click on the nat-config gateway and then click Edit.
- Click Advanced configurations.
- Under cloud logging (Stackdriver), select Translation and errors and then click Save.






