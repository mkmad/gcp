# Overview

A Virtual Private Cloud (VPC) network is a global resource which consists of a list of regional virtual subnetworks 
(subnets) in data centers, all connected by a global wide area network (WAN). VPC networks are logically isolated from 
each other in Google Cloud.

VPC provides networking functionality to Compute Engine virtual machine (VM) instances, Kubernetes Engine containers, 
and App Engine Flex. Each Google Cloud project by default has a default network configuration which provides each region 
with an auto subnet network.

In this lab you use gcloud to create two custom VPC networks with subnets, firewall rules, and VM instances, then test 
the networks' ability to allow traffic from the public internet.

# Create a VPC Network

```
(qwiklabs-gcp-00-32a20e7f9a7a)$ gcloud compute networks create labnet --subnet-mode=custom

Created [https://www.googleapis.com/compute/v1/projects/qwiklabs-gcp-00-32a20e7f9a7a/global/networks/labnet].
NAME: labnet
SUBNET_MODE: CUSTOM
BGP_ROUTING_MODE: REGIONAL
IPV4_RANGE: 
GATEWAY_IPV4: 

Instances on this network will not be reachable until firewall rules
are created. As an example, you can allow all internal traffic between
instances as well as SSH, RDP, and ICMP by running:

$ gcloud compute firewall-rules create <FIREWALL_NAME> --network labnet --allow tcp,udp,icmp --source-ranges <IP_RANGE>
$ gcloud compute firewall-rules create <FIREWALL_NAME> --network labnet --allow tcp:22,tcp:3389,icmp
```

With this command you're doing the following:

gcloud invokes the Cloud SDK gcloud command line tool
compute is a one of the groups available in gcloud, part of a nested hierarchy of command groups
networks is a subgroup of compute with it's own specialized commands
create is the action to be executed on this group
labnet is the name of the network you're creating
--subnet-mode=custom you're passing the subnet mode flag and the type of subnet you're creating, "custom".


# Create a Subnetwork

When you create a subnetwork, its name must be unique in that project for that region, even across networks. 
The same name can appear twice in a project as long as each one is in a different region.

Each subnet must have a primary range, which must be unique within the same region in a project.

Now create sub-network labnet-sub:

```
(qwiklabs-gcp-00-32a20e7f9a7a)$ gcloud compute networks subnets create labnet-sub \
   --network labnet \
   --region "us-east4" \
   --range 10.0.0.0/28
Created [https://www.googleapis.com/compute/v1/projects/qwiklabs-gcp-00-32a20e7f9a7a/regions/us-east4/subnetworks/labnet-sub].
NAME: labnet-sub
REGION: us-east4
NETWORK: labnet
RANGE: 10.0.0.0/28
STACK_TYPE: IPV4_ONLY
IPV6_ACCESS_TYPE: 
INTERNAL_IPV6_PREFIX: 
EXTERNAL_IPV6_PREFIX:
```

# Viewing networks

```
(qwiklabs-gcp-00-32a20e7f9a7a)$ gcloud compute networks list
NAME: default
SUBNET_MODE: AUTO
BGP_ROUTING_MODE: REGIONAL
IPV4_RANGE: 
GATEWAY_IPV4: 

NAME: labnet
SUBNET_MODE: CUSTOM
BGP_ROUTING_MODE: REGIONAL
IPV4_RANGE: 
GATEWAY_IPV4: 
```

# Describing a network

Use describe to view network details, such as its peering connections and subnets.

```
(qwiklabs-gcp-00-32a20e7f9a7a)$ gcloud compute networks describe labnet
autoCreateSubnetworks: false
creationTimestamp: '2024-03-17T20:26:10.677-07:00'
id: '2911377609467759293'
kind: compute#network
name: labnet
networkFirewallPolicyEnforcementOrder: AFTER_CLASSIC_FIREWALL
routingConfig:
  routingMode: REGIONAL
selfLink: https://www.googleapis.com/compute/v1/projects/qwiklabs-gcp-00-32a20e7f9a7a/global/networks/labnet
selfLinkWithId: https://www.googleapis.com/compute/v1/projects/qwiklabs-gcp-00-32a20e7f9a7a/global/networks/2911377609467759293
subnetworks:
- https://www.googleapis.com/compute/v1/projects/qwiklabs-gcp-00-32a20e7f9a7a/regions/us-east4/subnetworks/labnet-sub
x_gcloud_bgp_routing_mode: REGIONAL
x_gcloud_subnet_mode: CUSTOM
```

# List subnets

You can list all subnets in all networks in your project, or you can show only the subnets for a particular 
network or region

Use this command to list all subnets in all VPC networks, in all regions:

```
(qwiklabs-gcp-00-32a20e7f9a7a)$ gcloud compute networks subnets list
```

Use this command to list subnets by name

```
(qwiklabs-gcp-00-32a20e7f9a7a)$ gcloud compute networks subnets list --filter="name=( 'labnet-sub' )"
NAME: labnet-sub
REGION: us-east4
NETWORK: labnet
RANGE: 10.0.0.0/28
STACK_TYPE: IPV4_ONLY
IPV6_ACCESS_TYPE: 
INTERNAL_IPV6_PREFIX: 
EXTERNAL_IPV6_PREFIX: 
```

# Creating firewall rules

Auto networks include default rules, custom networks do not include any firewall rules. Firewall rules are 
defined at the network level, and only apply to the network where they are created.

The name you choose for each firewall rule must be unique to the project. To allow access to VM instances, 
you must apply firewall rules.

With this command you are doing the following:

firewall-rules is a subcategory of compute
create is the action you are taking
labnet-allow-internal is the name of the firewall rule
--network=labnet puts the rule in the labnet network
--action=ALLOW must be used with the --rules flag, and is either "ALLOW" or "DENY"
--rules=icmp,tcp:22 specifies the icmp and tcp protocols and the ports that the rule applies to
--source-ranges=0.0.0.0/0 specifies the ranges of source IP addresses in CIDR format.

```
(qwiklabs-gcp-00-32a20e7f9a7a)$ gcloud compute firewall-rules create labnet-allow-internal \
        --network=labnet \
        --action=ALLOW \
        --rules=icmp,tcp:22 \
        --source-ranges=0.0.0.0/0
Creating firewall...working..Created [https://www.googleapis.com/compute/v1/projects/qwiklabs-gcp-00-32a20e7f9a7a/global/firewalls/labnet-allow-internal].
Creating firewall...done.                                                                                                                      
NAME: labnet-allow-internal
NETWORK: labnet
DIRECTION: INGRESS
PRIORITY: 1000
ALLOW: icmp,tcp:22
DENY: 
DISABLED: False
```

# Viewing firewall rules details

Inspect the firewall rules to see its name, applicable network, and components, including whether the rule is enabled or disabled:

```
(qwiklabs-gcp-00-32a20e7f9a7a)$ gcloud compute firewall-rules describe labnet-allow-internal
allowed:
- IPProtocol: icmp
- IPProtocol: tcp
  ports:
  - '22'
creationTimestamp: '2024-03-17T20:41:10.417-07:00'
description: ''
direction: INGRESS
disabled: false
id: '5443165825783171385'
kind: compute#firewall
logConfig:
  enable: false
name: labnet-allow-internal
network: https://www.googleapis.com/compute/v1/projects/qwiklabs-gcp-00-32a20e7f9a7a/global/networks/labnet
priority: 1000
selfLink: https://www.googleapis.com/compute/v1/projects/qwiklabs-gcp-00-32a20e7f9a7a/global/firewalls/labnet-allow-internal
sourceRanges:
- 0.0.0.0/0
```

# Create another network

Now you'll create a another network, add firewall rules to it, then add VMs to both networks to test the ability 
to communicate with the networks.

create the privatenet network

```
(qwiklabs-gcp-00-32a20e7f9a7a)$ gcloud compute networks create privatenet --subnet-mode=custom
Created [https://www.googleapis.com/compute/v1/projects/qwiklabs-gcp-00-32a20e7f9a7a/global/networks/privatenet].
NAME: privatenet
SUBNET_MODE: CUSTOM
BGP_ROUTING_MODE: REGIONAL
IPV4_RANGE: 
GATEWAY_IPV4: 

Instances on this network will not be reachable until firewall rules
are created. As an example, you can allow all internal traffic between
instances as well as SSH, RDP, and ICMP by running:

$ gcloud compute firewall-rules create <FIREWALL_NAME> --network privatenet --allow tcp,udp,icmp --source-ranges <IP_RANGE>
$ gcloud compute firewall-rules create <FIREWALL_NAME> --network privatenet --allow tcp:22,tcp:3389,icmp
```

Create the private-sub subnet

```
(qwiklabs-gcp-00-32a20e7f9a7a)$ gcloud compute networks subnets create private-sub \
    --network=privatenet \
    --region="us-east4" \
    --range 10.1.0.0/28
Created [https://www.googleapis.com/compute/v1/projects/qwiklabs-gcp-00-32a20e7f9a7a/regions/us-east4/subnetworks/private-sub].
NAME: private-sub
REGION: us-east4
NETWORK: privatenet
RANGE: 10.1.0.0/28
STACK_TYPE: IPV4_ONLY
IPV6_ACCESS_TYPE: 
INTERNAL_IPV6_PREFIX: 
EXTERNAL_IPV6_PREFIX: 
```

Create the firewall rules for privatenet

```
(qwiklabs-gcp-00-32a20e7f9a7a)$ gcloud compute firewall-rules create privatenet-deny \
    --network=privatenet \
    --action=DENY \
    --rules=icmp,tcp:22 \
    --source-ranges=0.0.0.0/0
Creating firewall...working..Created [https://www.googleapis.com/compute/v1/projects/qwiklabs-gcp-00-32a20e7f9a7a/global/firewalls/privatenet-deny].
Creating firewall...done.                                                                                                                      
NAME: privatenet-deny
NETWORK: privatenet
DIRECTION: INGRESS
PRIORITY: 1000
ALLOW: 
DENY: icmp,tcp:22
DISABLED: False
```

# Create VM instances

Create two VM instances in the subnets:

- `pnet-vm` in `private-sub`
- `lnet-vm` in `labnet-sub`

Create the pnet-vm instance in the `private-sub` subnet

```
(qwiklabs-gcp-00-32a20e7f9a7a)$ gcloud compute instances create pnet-vm \             
--zone="us-east4-a" \
--machine-type=n1-standard-1 \
--subnet=private-sub
Created [https://www.googleapis.com/compute/v1/projects/qwiklabs-gcp-00-32a20e7f9a7a/zones/us-east4-a/instances/pnet-vm].
NAME: pnet-vm
ZONE: us-east4-a
MACHINE_TYPE: n1-standard-1
PREEMPTIBLE: 
INTERNAL_IP: 10.1.0.2
EXTERNAL_IP: 35.236.245.109
STATUS: RUNNING
```

Create the lnet-vm instance in the `labnet-sub` subnet

```
(qwiklabs-gcp-00-32a20e7f9a7a)$ gcloud compute instances create lnet-vm --zone="us-east4-a" --machine-type=
n1-standard-1 --subnet=labnet-sub
Created [https://www.googleapis.com/compute/v1/projects/qwiklabs-gcp-00-32a20e7f9a7a/zones/us-east4-a/instances/lnet-vm].
NAME: lnet-vm
ZONE: us-east4-a
MACHINE_TYPE: n1-standard-1
PREEMPTIBLE: 
INTERNAL_IP: 10.0.0.2
EXTERNAL_IP: 34.48.58.123
STATUS: RUNNING
```

list all the VM instances (sorted by zone)

```
(qwiklabs-gcp-00-32a20e7f9a7a)$ gcloud compute instances list --sort-by=ZONE
NAME: lnet-vm
ZONE: us-east4-a
MACHINE_TYPE: n1-standard-1
PREEMPTIBLE: 
INTERNAL_IP: 10.0.0.2
EXTERNAL_IP: 34.48.58.123
STATUS: RUNNING

NAME: pnet-vm
ZONE: us-east4-a
MACHINE_TYPE: n1-standard-1
PREEMPTIBLE: 
INTERNAL_IP: 10.1.0.2
EXTERNAL_IP: 35.236.245.109
STATUS: RUNNING
```

# Explore the connectivity

When you created the networks, you applied firewall rules to each - so one network allows `INGRESS` traffic, 
and the other denies `INGRESS` traffic.

For this experiment, you should be able to communicate with the first network, but be unable to communicate 
with the second one.

Ping the external IP addresses

1. Ping lnet-vm's external IP: This should work - lnet-vm's network has a firewall rule that allows traffic.
```
(qwiklabs-gcp-00-32a20e7f9a7a)$ ping -c 3 34.48.58.123
PING 34.48.58.123 (34.48.58.123) 56(84) bytes of data.
64 bytes from 34.48.58.123: icmp_seq=1 ttl=55 time=12.9 ms
64 bytes from 34.48.58.123: icmp_seq=2 ttl=55 time=11.8 ms
64 bytes from 34.48.58.123: icmp_seq=3 ttl=55 time=11.8 ms
```

2. Ping pnet-vm's external IP address: This should not work - nothing should be happening. pnet-vm's network has a 
firewall rule that denies traffic.

```
(qwiklabs-gcp-00-32a20e7f9a7a)$ ping -c 3 35.236.245.109
PING 35.236.245.109 (35.236.245.109) 56(84) bytes of data.

--- 35.236.245.109 ping statistics ---
3 packets transmitted, 0 received, 100% packet loss, time 2047ms
```

