variable "cluster_name" {
  description = "The name of the GKE cluster"
  type        = string
}

variable "location" {
  description = "The location for the GKE cluster"
  type        = string
}

variable "network" {
  description = "The VPC network for the cluster"
  type        = string
}

variable "subnetwork" {
  description = "The subnetwork for the cluster"
  type        = string
}

variable "release_channel" {
  description = "The release channel for the GKE cluster"
  type        = string
}

variable "cluster_ipv4_cidr_block" {
  description = "The CIDR block for the cluster's pod IPs"
  type        = string
}

variable "services_ipv4_cidr_block" {
  description = "The CIDR block for the cluster's service IPs"
  type        = string
}

variable "master_ipv4_cidr_block" {
  description = "The CIDR block for the control plane"
  type        = string
}

variable "master_authorized_networks_cidr_block" {
  description = "The CIDR block for the control plane"
  type        = string
  default     = "10.0.0.0/28"  
}

variable "workload_pool" {
  description = "The workload identity pool for the GKE cluster"
  type        = string
}

variable "prometheus_enabled" {
  description = "Enable Managed Service for Prometheus"
  type        = bool
}

variable "default_snat_enabled" {
  description = "Enable default SNAT"
  type        = bool
}

variable "l4_ilb_subsetting_enabled" {
  description = "Enable subsetting for L4 Internal Load Balancer"
  type        = bool
}

variable "gateway_api_channel" {
  description = "The channel for Gateway API"
  type        = string
}
