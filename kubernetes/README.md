# Private GKE cluster with the following config will be created via Terraform

```
Name	                            : tele-webhook-gke	
Location type	                    : Regional	
Region	                            : us-central1	
Release channel	                    : Regular channel	
Version	                            : 1.29.6-gke.1326000	
External endpoint                   : <Auto assign>
Internal endpoint                   : 10.0.0.2
Private cluster	                    : Enabled		
Default SNAT	                    : Enabled		
Control plane address range	        : 10.0.0.0/28		
Control plane global access	        : Disabled		
Network	                            : default		
Subnet	                            : default 		
Stack type	                        : IPv4		
VPC-native traffic routing	        : Enabled		
cluster_ipv4_cidr_block             : "172.16.0.0/12"
services_ipv4_cidr_block            : "172.32.0.0/16"		
HTTP Load Balancing	                : Enabled		
Subsetting for L4 Internal LB       : Enabled				
Gateway API	                        : Enabled		
Shielded GKE nodes	                : Enabled		
Workload Identity	                : Enabled	
Workload identity namespace	        : mohan-sandbox.svc.id.goog	
Google Groups for RBAC	            : Enabled	
Managed Service for Prometheus	    : Enabled	
Compute Engine persistent disk CSI  : Enabled
```