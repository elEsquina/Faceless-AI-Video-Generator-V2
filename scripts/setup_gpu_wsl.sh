#!/usr/bin/env bash
# Ubuntu-only NVIDIA Container Toolkit repair. No Windows or display-driver changes.
# Source: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html
set -euo pipefail
if [[ ${EUID} -ne 0 ]]; then
  echo 'Run this script with sudo in your Ubuntu terminal.' >&2
  exit 1
fi
if [[ ! -e /dev/dxg ]]; then
  echo 'WSL GPU device /dev/dxg is absent; no configuration was changed.' >&2
  exit 1
fi
if [[ -n $(docker ps -q) ]]; then
  echo 'Containers are running. Finish/stop them before this Docker runtime restart.' >&2
  exit 1
fi
/usr/lib/wsl/lib/nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
faceless_gpu_tmp=$(mktemp -d)
trap 'rm -rf "$faceless_gpu_tmp"' EXIT
faceless_gpu_backup="/var/backups/faceless-nvidia-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$faceless_gpu_backup"
for faceless_gpu_file in /etc/docker/daemon.json /etc/apt/sources.list.d/nvidia-container-toolkit.list /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg; do
  if [[ -f "$faceless_gpu_file" ]]; then cp --parents "$faceless_gpu_file" "$faceless_gpu_backup/"; fi
done
if ! command -v curl >/dev/null || ! command -v gpg >/dev/null; then
  apt-get update
  apt-get install -y --no-install-recommends ca-certificates curl gnupg
fi
curl --proto '=https' --tlsv1.2 -fsSL https://nvidia.github.io/libnvidia-container/gpgkey -o "$faceless_gpu_tmp/key.asc"
gpg --batch --yes --dearmor --output "$faceless_gpu_tmp/key.gpg" "$faceless_gpu_tmp/key.asc"
install -D -m 0644 "$faceless_gpu_tmp/key.gpg" /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl --proto '=https' --tlsv1.2 -fsSL https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list -o "$faceless_gpu_tmp/repository.list"
sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' "$faceless_gpu_tmp/repository.list" > "$faceless_gpu_tmp/signed.list"
install -D -m 0644 "$faceless_gpu_tmp/signed.list" /etc/apt/sources.list.d/nvidia-container-toolkit.list
apt-get update
apt-get install -y nvidia-container-toolkit
nvidia-ctk runtime configure --runtime=docker
systemctl restart docker
docker run --rm --gpus all --network none nvidia/cuda:12.8.1-base-ubuntu24.04 nvidia-smi
printf '\nDocker GPU runtime configured. Backup: %s\n' "$faceless_gpu_backup"
