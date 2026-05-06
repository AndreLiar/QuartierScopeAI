provider "digitalocean" {
  token = var.do_token
}

data "digitalocean_ssh_key" "main" {
  name = var.ssh_key_name
}

resource "digitalocean_droplet" "app" {
  name       = "${var.project_name}-prod"
  region     = var.region
  size       = var.droplet_size
  image      = "ubuntu-24-04-x64"
  ssh_keys   = [data.digitalocean_ssh_key.main.fingerprint]
  ipv6       = true
  monitoring = true
  user_data  = file("${path.module}/bootstrap.sh")
  tags       = ["quartierscope", "prod"]
}

resource "digitalocean_firewall" "app" {
  name        = "${var.project_name}-fw"
  droplet_ids = [digitalocean_droplet.app.id]

  inbound_rule {
    protocol         = "tcp"
    port_range       = "22"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  inbound_rule {
    protocol         = "tcp"
    port_range       = "80"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  inbound_rule {
    protocol         = "tcp"
    port_range       = "443"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "tcp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "udp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "icmp"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
}

resource "digitalocean_project" "main" {
  name        = var.project_name
  description = "QuartierScope AI — multi-agent neighborhood analyst for French CGP firms"
  purpose     = "Web Application"
  environment = "Production"
  resources   = [digitalocean_droplet.app.urn]
}
