#!/usr/bin/env bash
# Pagouro BE round 2 — desk side. Same shape as round 1 plus the round-1 single file as the start point.
#   bash scripts/runpod/be_round2_local.sh up   <ip> <port>
#   bash scripts/runpod/be_round2_local.sh log  <ip> <port>
#   bash scripts/runpod/be_round2_local.sh home <ip> <port>
set -euo pipefail
cmd=${1:?up|log|home}; ip=${2:?ip}; port=${3:?port}
R=${ROUND:-2}; PREV=$((R-1))
KEY="$HOME/.ssh/pagouro_rpkey"
BE="$(cd "$(dirname "$0")/../.." && pwd)"
DATA="${PAGOURO_DATA:-$BE/../PAGOURO_BUILD/data/images}"
sshp() { ssh -i "$KEY" -p "$port" -o StrictHostKeyChecking=no -o ServerAliveInterval=30 "root@$ip" "$@"; }
scpp() { scp -i "$KEY" -P "$port" -o StrictHostKeyChecking=no "$@"; }
case "$cmd" in
  up)
    tar_path="$BE/runs/be_train${R}_512.tar"
    [ -f "$tar_path" ] || { echo "no $tar_path"; exit 1; }
    echo "tar $(stat -c %s "$tar_path") B"
    sshp "mkdir -p /workspace/be/train /workspace/be/out /workspace/be/r1"
    scpp "$tar_path" "root@$ip:/workspace/be/train.tar"
    scpp "$BE/runs/round${PREV}/ft_single/pagouro-be-r${PREV}-fp16.safetensors" "root@$ip:/workspace/be/r1/"
    scpp "$BE/evals/gate40.jsonl" "$BE/scripts/runpod/be_train2.sh" "root@$ip:/workspace/be/"
    sshp "cd /workspace/be && sha256sum r1/pagouro-be-r${PREV}-fp16.safetensors | cut -c1-16 && tar --no-same-owner -xf train.tar -C train && rm train.tar && ls train/512 | wc -l && sed -i 's/\r$//' be_train2.sh && ( START=/workspace/be/r1/pagouro-be-r${PREV}-fp16.safetensors OUTNAME=pagouro-be-r${R}-fp16 DONE=BE_ROUND${R}_DONE STEPS_FT=${STEPS_FT:-8000} LR=${LR:-8e-6} nohup bash be_train2.sh > be.log 2>&1 & ) && sleep 2 && echo launched"
    ;;
  log)
    sshp "tail -n 25 /workspace/be/be.log; nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader"
    ;;
  home)
    dest="$BE/runs/round${R}"; mkdir -p "$dest"
    sshp "grep -c BE_ROUND${R}_DONE /workspace/be/be.log" || { echo "not done"; exit 1; }
    sshp "cd /workspace/be/out && tar -cf - --exclude=./ft SHA256SUMS gate ft_single train_ft.log" | tar -xf - -C "$dest"
    scpp "root@$ip:/workspace/be/be.log" "$dest/"
    (cd "$dest" && grep -v " ./ft/" SHA256SUMS | sha256sum -c --quiet && echo "hashes OK: $(grep -vc ' ./ft/' SHA256SUMS) files")
    du -sh "$dest"
    ;;
esac
