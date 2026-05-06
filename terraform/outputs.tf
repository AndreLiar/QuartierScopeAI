output "droplet_ip" {
  value       = digitalocean_droplet.app.ipv4_address
  description = "Public IPv4 of the QuartierScope droplet."
}

output "droplet_ipv6" {
  value       = digitalocean_droplet.app.ipv6_address
  description = "Public IPv6 of the QuartierScope droplet."
}

output "ssh_command" {
  value       = "ssh -i ~/.ssh/do_ed25519 root@${digitalocean_droplet.app.ipv4_address}"
  description = "Run this to connect."
}

output "monthly_cost_usd" {
  value = "~$24/mo (Basic 4GB, ${var.region})"
}

output "region" {
  value = var.region
}
