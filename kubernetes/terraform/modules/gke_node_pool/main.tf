resource "google_container_node_pool" "this" {
  cluster    = var.cluster_name
  name       = var.node_pool_name
  node_count = var.node_count

  node_config {
    machine_type = var.machine_type

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
    ]

    labels = {
      "env" = "prod"
    }

    tags = ["gke-node", "tele-webhook"]

    metadata = {
      disable-legacy-endpoints = "true"
    }

    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  autoscaling {
    min_node_count = var.min_node_count
    max_node_count = var.max_node_count
  }

  upgrade_settings {
    max_surge       = 1
    max_unavailable = 0
  }
}
