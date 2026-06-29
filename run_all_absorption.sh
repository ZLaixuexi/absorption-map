#!/bin/bash
# ===========================================================================
# 批量计算吸收谱：遍历 (l, b, d) 参数空间
#
# 银经 l : 0° – 360°, 步长 2°    (181 个值)
# 银纬 b : -15° – +15°, 步长 0.5° (61 个值)
# 距离 d : 0 – 25 kpc, 步长 0.5 kpc (51 个值)
#
# 总计 181 × 61 × 51 = 563,091 个任务
#
# 用法:
#   ./run_all_absorption.sh -p 20         # 20进程并行
#   ./run_all_absorption.sh -p 20 -r      # 断点续传
#   kill $(cat all_output/.pid)            # 安全停止
# ===========================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN="${SCRIPT_DIR}/all8_cmb_galpropall_interpolationN_argvZ"
OUTDIR="${SCRIPT_DIR}/all_output"
JOBS=1
RESUME=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        -p) JOBS="$2"; shift 2 ;;
        -r) RESUME=true; shift ;;
        *) shift ;;
    esac
done

mkdir -p "$OUTDIR"

# 写 PID 方便 kill
echo $$ > "$OUTDIR/.pid"

# Ctrl+C 时清理
cleanup() { echo -e "\n已停止"; rm -f "$OUTDIR/.pid"; exit 0; }
trap cleanup SIGINT SIGTERM

# ---------- 生成任务列表 ----------
TASKFILE="${OUTDIR}/.task_list.txt"
echo "生成任务列表..."
python3 -c "
l_vals = [round(i,1) for i in [i*2 for i in range(0, 181)]]
b_vals = [round(i,2) for i in [i*0.5 for i in range(-30, 31)]]
d_vals = [round(i,2) for i in [i*0.5 for i in range(0, 51)]]
tasks = []
for d in d_vals:
    for l in l_vals:
        for b in b_vals:
            outfile = '${OUTDIR}/l' + str(l) + '_b' + str(b) + '_d' + str(d) + '.txt'
            tasks.append(str(d)+' '+str(l)+' '+str(b)+' '+outfile)
with open('${TASKFILE}', 'w') as f:
    f.write('\n'.join(tasks))
"
TOTAL=$(wc -l < "$TASKFILE")
echo "总任务数: $(printf "%'d" $TOTAL)"
echo "输出目录: $OUTDIR"
echo "PID: $(cat $OUTDIR/.pid)"
echo ""

# ---------- 执行 ----------
if [ "$JOBS" -gt 1 ]; then
    echo "并行模式: $JOBS 进程"
    SCRIPTPID=$(cat "$OUTDIR/.pid")
    cat "$TASKFILE" | xargs -n 4 -P "$JOBS" -I {} bash -c '
        read d l b outfile <<< "$*"
        if [ ! -f "'"$OUTDIR"'/.pid" ]; then exit 1; fi
        if [ "'"$RESUME"'" = true ] && [ -f "$outfile" ] && [ -s "$outfile" ]; then
            exit 0
        fi
        '"$BIN"' "$d" "$l" "$b" > "$outfile" 2>/dev/null
    ' _ {}
else
    echo "顺序模式"
    COUNT=0
    while read -r d l b outfile; do
        if [ "$RESUME" = true ] && [ -f "$outfile" ] && [ -s "$outfile" ]; then
            COUNT=$((COUNT + 1))
            continue
        fi
        echo -ne "\r[$COUNT/$TOTAL] d=$d l=$l b=$b   "
        "$BIN" "$d" "$l" "$b" > "$outfile" 2>/dev/null
        COUNT=$((COUNT + 1))
    done < "$TASKFILE"
    echo -e "\r[$COUNT/$TOTAL] 完成                    "
fi

rm -f "$OUTDIR/.pid"
echo "完成！"
