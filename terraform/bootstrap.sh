#!/bin/bash
set -euo pipefail
exec > >(tee -a /var/log/quartierscope-bootstrap.log) 2>&1

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y --no-install-recommends \
  ca-certificates curl gnupg ufw fail2ban git

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

. /etc/os-release
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" \
  > /etc/apt/sources.list.d/docker.list

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

systemctl enable --now fail2ban

if ! id quartierscope >/dev/null 2>&1; then
  useradd -m -s /bin/bash -G docker quartierscope
fi

mkdir -p /home/quartierscope/.ssh
cp /root/.ssh/authorized_keys /home/quartierscope/.ssh/authorized_keys
chown -R quartierscope:quartierscope /home/quartierscope/.ssh
chmod 700 /home/quartierscope/.ssh
chmod 600 /home/quartierscope/.ssh/authorized_keys

echo "[bootstrap] complete. Connect with: ssh quartierscope@<ip>"
