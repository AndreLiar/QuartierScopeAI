variable "do_token" {
  type        = string
  sensitive   = true
  description = "DigitalOcean Personal Access Token. Provide via TF_VAR_do_token env var."
}

variable "ssh_key_name" {
  type        = string
  default     = "Andre-MBA-ed25519"
  description = "Name of an existing SSH key already uploaded to your DigitalOcean account."
}

variable "region" {
  type        = string
  default     = "ams3"
  description = "DigitalOcean region. ams3 = Amsterdam (lowest latency from France)."
}

variable "droplet_size" {
  type        = string
  default     = "s-2vcpu-4gb"
  description = "Basic 4GB / 2 vCPU / 80GB SSD = $24/mo."
}

variable "project_name" {
  type    = string
  default = "quartierscope"
}
