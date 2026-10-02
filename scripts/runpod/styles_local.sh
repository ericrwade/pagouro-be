#!/usr/bin/env bash
# Pagouro BE Styles — desk side.
#   bash scripts/runpod/styles_local.sh up   <ip> <port> "rockart ukiyoe ..."   # upload sets + base + script, launch
#   bash scripts/runpod/styles_local.sh log  <ip> <port>
#   bash scripts/runpod/styles_local.sh home <ip> <port>                        # fetch out/, verify hashes
set -euo pipefail
cmd=${1:?up|log|home}; ip=${2:?ip}; port=${3:?port}; STYLES=${4:-}
KEY="$HOME/.ssh/pagouro_rpkey"; BE="$(cd "$(dirname "$0")/../.." && pwd)"
DATA="${PAGOURO_DATA:-$BE/../PAGOURO_BUILD/data/images}"
sshp() { ssh -i "$KEY" -p "$port" -o StrictHostKeyChecking=no -o ServerAliveInterval=30 "root@$ip" "$@"; }
scpp() { scp -i "$KEY" -P "$port" -o StrictHostKeyChecking=no "$@"; }
case "$cmd" in
  up)
    [ -n "$STYLES" ] || { echo "styles list required"; exit 1; }
    tar_path="$BE/runs/styles_train.tar"; rm -f "$tar_path"
    (cd "$DATA/styles_train" && tar -cf "$tar_path" $STYLES)
    echo "tar $(stat -c %s "$tar_path") B"
    sshp "mkdir -p /workspace/st/train /workspace/st/out /workspace/st/r1"
    scpp "$tar_path" "root@$ip:/workspace/st/train.tar"
    scpp "$BE/runs/round3/ft_single/pagouro-be-r3-fp16.safetensors" "root@$ip:/workspace/st/r1/"
    scpp "$BE/styles.json" "$BE/evals/gate40_styles.jsonl" "$BE/scripts/runpod/styles_train.sh" "root@$ip:/workspace/st/"
    sshp "cd /workspace/st && sha256sum r1/pagouro-be-r3-fp16.safetensors | cut -c1-16 && tar --no-same-owner -xf train.tar -C train && rm train.tar && ls train && sed -i 's/\r$//' styles_train.sh && ( STYLES=\"$STYLES\" STEPS=${STEPS:-2000} RANK=${RANK:-64} SEEDS=${SEEDS:-2} nohup bash styles_train.sh > st.log 2>&1 & ) && sleep 2 && echo launched"
    ;;
  log) sshp "tail -n 20 /workspace/st/st.log; nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader" ;;
  home)
    dest="$BE/runs/styles"; mkdir -p "$dest"
    sshp "grep -c STYLES_DONE /workspace/st/st.log" || { echo "not done"; exit 1; }
    sshp "cd /workspace/st/out && tar -cf - ." | tar -xf - -C "$dest"
    scpp "root@$ip:/workspace/st/st.log" "$dest/"
    (cd "$dest" && sha256sum -c --quiet SHA256SUMS && echo "hashes OK: $(wc -l < SHA256SUMS) files")
    du -sh "$dest"
    ;;
esac
