resource "google_container_cluster" "this" {
  name               = var.cluster_name
  location           = var.location
  remove_default_node_pool = true
  initial_node_count = 1
  network            = var.network
  subnetwork         = var.subnetwork

  release_channel {
    channel = var.release_channel
  }

  ip_allocation_policy {
    cluster_ipv4_cidr_block  = var.cluster_ipv4_cidr_block
    services_ipv4_cidr_block = var.services_ipv4_cidr_block
  }

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = var.master_ipv4_cidr_block
  }

  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = "0.0.0.0/0"
      display_name = "Allow All"
    }
  }

  vertical_pod_autoscaling {
    enabled = true
  }

  dns_config {
    cluster_dns = "PLATFORM_DEFAULT"
  }

  addons_config {
    http_load_balancing {
      disabled = false
    }

    horizontal_pod_autoscaling {
      disabled = false
    }

    network_policy_config {
      disabled = false
    }

    dns_cache_config {
      enabled = true
    }
  }

  workload_identity_config {
    workload_pool = var.workload_pool
  }

  monitoring_config {
    managed_prometheus {
      enabled = var.prometheus_enabled
    }
  }

  logging_config {
    enable_components = ["SYSTEM_COMPONENTS", "WORKLOADS"]
  }

  default_snat_status {
    disabled = !var.default_snat_enabled
  }

  gateway_api_config {
    channel = var.gateway_api_channel
  }
}
