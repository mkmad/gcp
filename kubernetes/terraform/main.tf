provider "google" {
  project = var.project_id
  region  = var.region
}

# Create the GKE Cluster
module "gke_cluster" {
  source            = "./modules/gke_cluster"
  cluster_name      = var.cluster_name
  location          = var.location
  network           = var.network
  subnetwork        = var.subnetwork
  release_channel   = var.release_channel
  cluster_ipv4_cidr_block = var.cluster_ipv4_cidr_block
  services_ipv4_cidr_block = var.services_ipv4_cidr_block
  master_ipv4_cidr_block = var.master_ipv4_cidr_block
  workload_pool     = var.workload_pool
  prometheus_enabled = var.prometheus_enabled
  default_snat_enabled = var.default_snat_enabled
  l4_ilb_subsetting_enabled = var.l4_ilb_subsetting_enabled
  gateway_api_channel = var.gateway_api_channel
}

# Fetch the GKE Cluster's external IP only after the cluster is created
data "google_container_cluster" "gke_cluster" {
  depends_on = [module.gke_cluster]  # Ensure GKE cluster is created first
  name       = module.gke_cluster.cluster_name
  location   = var.location
}

# Create the Firewall Rule
module "firewall_rule" {
  source = "./modules/firewall_rule"

  firewall_rule_name = "allow-k8s-masters-to-pods"
  network            = var.network
  ports              = ["8443"]
  source_ranges      = [data.google_container_cluster.gke_cluster.endpoint]  # Control plane's external IP
  priority           = 1000

  depends_on = [module.gke_cluster]  # Ensure GKE cluster is created first
}

# Create the GKE Node Pool
module "gke_node_pool" {
  source            = "./modules/gke_node_pool"
  cluster_name      = module.gke_cluster.cluster_name
  node_pool_name    = var.node_pool_name
  node_count        = var.node_count
  machine_type      = var.machine_type
  min_node_count    = var.min_node_count
  max_node_count    = var.max_node_count
}
