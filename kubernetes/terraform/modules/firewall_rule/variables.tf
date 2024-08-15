variable "firewall_rule_name" {
  description = "The name of the firewall rule"
  type        = string
}

variable "network" {
  description = "The VPC network name"
  type        = string
  default     = "default"
}

variable "ports" {
  description = "List of TCP ports to allow"
  type        = list(string)
}

variable "source_ranges" {
  description = "Source IP ranges to allow traffic from"
  type        = list(string)
}

variable "priority" {
  description = "Priority of the firewall rule"
  type        = number
  default     = 1000
}
