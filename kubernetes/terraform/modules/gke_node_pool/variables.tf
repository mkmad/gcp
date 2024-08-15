variable "cluster_name" {
  description = "The name of the GKE cluster"
  type        = string
}

variable "node_pool_name" {
  description = "The name of the node pool"
  type        = string
}

variable "node_count" {
  description = "The number of nodes in the node pool"
  type        = number
}

variable "machine_type" {
  description = "The machine type for the nodes"
  type        = string
}

variable "min_node_count" {
  description = "The minimum number of nodes in the node pool"
  type        = number
}

variable "max_node_count" {
  description = "The maximum number of nodes in the node pool"
  type        = number
}
