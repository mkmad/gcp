# This code is compatible with Terraform 4.25.0 and versions that are backwards compatible to 4.25.0.
# For information about validating this Terraform code, see https://developer.hashicorp.com/terraform/tutorials/gcp-get-started/google-cloud-platform-build#format-and-validate-the-configuration

resource "google_compute_instance" "sts-machine-2" {
  boot_disk {
    auto_delete = true
    device_name = "instance-20240818-164147"

    initialize_params {
      image = "projects/ubuntu-os-cloud/global/images/ubuntu-2004-focal-v20240808"
      size  = 490
      type  = "pd-balanced"
    }

    mode = "READ_WRITE"
  }

  can_ip_forward      = false
  deletion_protection = false
  enable_display      = false

  labels = {
    goog-ec-src           = "vm_add-tf"
    goog-ops-agent-policy = "v2-x86-template-1-3-0"
  }

  machine_type = "e2-highcpu-8"

  metadata = {
    enable-osconfig = "TRUE"
    ssh-keys        = "mohan_madhavan:ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBLOJo2YJue9vdwLS/PwUy0s0pqlTGoRQShTw4XctRmoZ8SDpwURG2joWchHI+UH35eZSBzATP3LzHC2DB1blSAo= google-ssh {\"userName\":\"mohan.madhavan@66degrees.com\",\"expireOn\":\"2024-08-21T11:11:44+0000\"}\nmohan_madhavan:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCgh9iJmlzlvcsLM6QLKJ+4MHn/aQxrIUZzHBnnVgmoj5ddWCb1L9oEY3sF2SDPuZlu1N9P7SPJPVOeoPZeFBSO0V8xq0TMyVMf4Uf4GWnKYjVmynbWakHSDBvfNFk1cfnNTtNDHwp6HSc1blquFAvdnYs84SasBxdCZJJevbg3E9zf6bZj3DSy7tSWMJRR8poxXAbMm5QytPnOykSBaeEn+nuCZZ1pqVD18fxL5qCBjxyCQCg8ErISvGCL0xCUn09GjLcKJKW0aHY4e01fJsEzBWfouV3yGrllUu1xKCD3+BrNT2SzCbwMmTTSHjkQ5Bfxdc007nXpEaO5YCyxZhet google-ssh {\"userName\":\"mohan.madhavan@66degrees.com\",\"expireOn\":\"2024-08-21T11:11:48+0000\"}"
  }

  name = "sts-machine-2"

  network_interface {
    access_config {
      network_tier = "PREMIUM"
    }

    queue_count = 0
    stack_type  = "IPV4_ONLY"
    subnetwork  = "projects/backup-428118/regions/us-east1/subnetworks/default"
  }

  scheduling {
    automatic_restart   = true
    on_host_maintenance = "MIGRATE"
    preemptible         = false
    provisioning_model  = "STANDARD"
  }

  service_account {
    email  = "backuptransfer@backup-428118.iam.gserviceaccount.com"
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }

  shielded_instance_config {
    enable_integrity_monitoring = true
    enable_secure_boot          = false
    enable_vtpm                 = true
  }

  tags = ["http-server", "https-server"]
  zone = "us-east1-c"
}
