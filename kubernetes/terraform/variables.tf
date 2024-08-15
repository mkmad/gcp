variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
}

variable "cluster_name" {
  description = "The name of the GKE cluster"
  type        = string
}

variable "location" {
  description = "The location for the GKE cluster"
  type        = string
  default     = "us-central1"
}

variable "network" {
  description = "The VPC network for the cluster"
  type        = string
  default     = "default"
}

variable "subnetwork" {
  description = "The subnetwork for the cluster"
  type        = string
  default     = "default"
}

variable "release_channel" {
  description = "The release channel for the GKE cluster"
  type        = string
  default     = "REGULAR"
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

variable "workload_pool" {
  description = "The workload identity pool for the GKE cluster"
  type        = string
  default     = "mohan-sandbox.svc.id.goog"
}


variable "node_pool_name" {
  description = "The name of the node pool"
  type        = string
  default     = "primary-node-pool"
}

variable "node_count" {
  description = "The number of nodes in the node pool"
  type        = number
  default     = 3
}

variable "machine_type" {
  description = "The machine type for the nodes"
  type        = string
  default     = "e2-medium"
}

variable "min_node_count" {
  description = "The minimum number of nodes in the node pool"
  type        = number
  default     = 1
}

variable "max_node_count" {
  description = "The maximum number of nodes in the node pool"
  type        = number
  default     = 5
}

variable "prometheus_enabled" {
  description = "Enable Managed Service for Prometheus"
  type        = bool
  default     = true
}

variable "default_snat_enabled" {
  description = "Enable default SNAT"
  type        = bool
  default     = true
}

variable "l4_ilb_subsetting_enabled" {
  description = "Enable subsetting for L4 Internal Load Balancer"
  type        = bool
  default     = true
}

variable "gateway_api_channel" {
  description = "The channel for Gateway API"
  type        = string
  default     = "CHANNEL_STANDARD"
}
