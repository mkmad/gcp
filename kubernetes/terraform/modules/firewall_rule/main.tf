resource "google_compute_firewall" "allow_k8s_master_to_pods" {
  name    = var.firewall_rule_name
  network = var.network

  allow {
    protocol = "tcp"
    ports    = var.ports
  }

  source_ranges = var.source_ranges

  direction = "INGRESS"
  priority  = var.priority
}
