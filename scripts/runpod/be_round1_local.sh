#!/usr/bin/env bash
# Pagouro BE round 1 — desk side (Git Bash). Uploads the training set, the gate and the pod script to a
# RunPod pod over its DIRECT ssh port (the proxy has no scp), launches be_train.sh detached, and
# later brings the outputs home with hashes checked. Never prints anything secret.
#
#   bash scripts/runpod/be_round1_local.sh up   <ip> <port>      # upload + launch
#   bash scripts/runpod/be_round1_local.sh log  <ip> <port>      # tail the pod log
#   bash scripts/runpod/be_round1_local.sh home <ip> <port>      # fetch out/ (minus the fp32 unet), verify SHA256SUMS
set -euo pipefail
cmd=${1:?up|log|home}; ip=${2:?ip}; port=${3:?port}
KEY="$HOME/.ssh/pagouro_rpkey"
BE="$(cd "$(dirname "$0")/../.." && pwd)"
DATA="${PAGOURO_DATA:-$BE/../PAGOURO_BUILD/data/images}"
sshp() { ssh -i "$KEY" -p "$port" -o StrictHostKeyChecking=no -o ServerAliveInterval=30 "root@$ip" "$@"; }
scpp() { scp -i "$KEY" -P "$port" -o StrictHostKeyChecking=no "$@"; }
case "$cmd" in
  up)
    tar_path="$BE/runs/be_train_512.tar"
    [ -f "$tar_path" ] || (cd "$DATA/be_train" && tar -cf "$tar_path" 512)
    echo "tar $(stat -c %s "$tar_path") B"
    sshp "mkdir -p /workspace/be/train /workspace/be/out"
    scpp "$tar_path" "root@$ip:/workspace/be/train.tar"
    scpp "$BE/evals/gate40.jsonl" "$BE/scripts/runpod/be_train.sh" "root@$ip:/workspace/be/"
    sshp "cd /workspace/be && tar --no-same-owner -xf train.tar -C train && rm train.tar && ls train/512 | wc -l && sed -i 's/\r$//' be_train.sh && ( nohup bash be_train.sh > be.log 2>&1 & ) && sleep 2 && echo launched"
    ;;
  log)
    sshp "tail -n 25 /workspace/be/be.log; nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader"
    ;;
  home)
    dest="$BE/runs/round1"; mkdir -p "$dest"
    sshp "grep -c BE_ROUND1_DONE /workspace/be/be.log" || { echo "not done"; exit 1; }
    sshp "cd /workspace/be/out && tar -cf - --exclude=./ft --exclude='lora/checkpoint-*' SHA256SUMS gate lora ft_single train_ft.log train_lora.log" | tar -xf - -C "$dest"
    scpp "root@$ip:/workspace/be/be.log" "$dest/"
    (cd "$dest" && grep -v " ./ft/" SHA256SUMS | sha256sum -c --quiet && echo "hashes OK: $(grep -vc ' ./ft/' SHA256SUMS) files")
    du -sh "$dest"
    ;;
esac
