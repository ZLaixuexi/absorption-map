#!/usr/bin/env python3
"""
plot_absorption.py — 从 FITS 数据立方体中提取指定 (l, b, d) 的吸收谱
                     画 e^{-tau} vs E 并输出 PDF + TXT

用法:
  python3 plot_absorption.py 98 -9.0 6.0
  python3 plot_absorption.py 0 0 0
  python3 plot_absorption.py 266 11.5 0.5

参考: plot_abs.C
"""
import sys
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
from pathlib import Path

# ---------- 参数 ----------
FITSFILE = "/share02/users/z/zhanglei/work/absorbed/absorb_github/absorption_map.fits"
OUTDIR   = "/share02/users/z/zhanglei/work/absorbed/absorb_github"

# 轴定义（与 merge_to_fits.py 一致）
L_START, L_STEP, L_N = 0.0, 2.0, 181    # 0, 2, 4, ..., 360
B_START, B_STEP, B_N = -15.0, 0.5, 61    # -15, -14.5, ..., +15
D_START, D_STEP, D_N = 0.0, 0.5, 51     # 0, 0.5, ..., 25


def find_index(val, start, step, n, name):
    """根据坐标值计算 FITS 数组中的索引"""
    idx = int(round((val - start) / step))
    if idx < 0 or idx >= n:
        raise ValueError(f"{name}={val} 超出范围 [{start}, {start + (n-1)*step}]")
    # 检查是否精确落在格点上
    exact = start + idx * step
    if abs(val - exact) > step * 0.01:
        print(f"警告: {name}={val} 不在格点上，近似为 {exact}")
    return idx


def main():
    if len(sys.argv) != 4:
        print("用法: python3 plot_absorption.py <l> <b> <d>")
        print("示例: python3 plot_absorption.py 98 -9.0 6.0")
        sys.exit(1)

    l_in = float(sys.argv[1])
    b_in = float(sys.argv[2])
    d_in = float(sys.argv[3])

    # 计算索引
    il = find_index(l_in, L_START, L_STEP, L_N, "l")
    ib = find_index(b_in, B_START, B_STEP, B_N, "b")
    id_ = find_index(d_in, D_START, D_STEP, D_N, "d")

    # 读取数据
    hdul = fits.open(FITSFILE)
    data = hdul[0].data        # (l=181, b=61, d=51, E=81)
    energy = hdul[1].data['E_TeV']  # 81 个能量点 (TeV)

    # FITS 维度: NAXIS4=l, NAXIS3=b, NAXIS2=d, NAXIS1=E
    y = data[il, ib, id_, :]   # 81 个吸收因子 e^{-tau}

    hdul.close()

    # 构建标签
    l_exact = L_START + il * L_STEP
    b_exact = B_START + ib * B_STEP
    d_exact = D_START + id_ * D_STEP
    label = f"l={l_exact:.1f}°  b={b_exact:.1f}°  d={d_exact:.1f} kpc"

    # ---------- 输出 TXT ----------
    basename = f"l{l_exact}_b{b_exact}_d{d_exact}"
    txt_path = Path(OUTDIR) / f"{basename}_plot.txt"
    with open(txt_path, 'w') as f:
        f.write(f"# {label}\n")
        f.write(f"# E (TeV)    e^(-tau)\n")
        for e, val in zip(energy, y):
            f.write(f"  {e:.6e}  {val:.6f}\n")
    print(f"TXT 已保存: {txt_path}")

    # ---------- 画图 ----------
    fig, ax = plt.subplots(figsize=(12, 9))
    ax.set_xscale('log')
    ax.set_xlabel('E (TeV)', fontsize=18)
    ax.set_ylabel(r'$e^{-\tau}$', fontsize=18)
    ax.tick_params(labelsize=14)

    # y 轴范围
    ymin = np.nanmin(y) - 0.02
    ymax = np.nanmax(y) + 0.015
    ax.set_ylim(ymin, ymax)
    ax.set_xlim(0.05, 1e7)

    # 吸收曲线
    ax.plot(energy, y, color='#1f77b4', linewidth=2)

    # 无吸收参考线
    ax.axhline(y=1.0, color='gray', linestyle='--', linewidth=1)

    # 标注
    ax.text(3e5, ymax - 0.025, label, fontsize=14, color='#1f77b4',
            verticalalignment='top')

    # 保存 PDF
    pdf_path = Path(OUTDIR) / f"{basename}_plot.pdf"
    fig.savefig(pdf_path, bbox_inches='tight')
    plt.close(fig)
    print(f"PDF 已保存: {pdf_path}")


if __name__ == '__main__':
    main()
