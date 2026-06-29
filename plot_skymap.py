#!/usr/bin/env python3
"""
plot_skymap.py — 从 FITS 数据立方体画银道坐标下的 survival probability (e^{-tau})

默认：对某距离 d 画所有能量点的多面板图，也可指定单个能量 E。

用法:
  python3 plot_skymap.py                           # 默认 d=0.5, 全部 81 个能量 (9×9 面板)
  python3 plot_skymap.py -d 5.0                     # d=5.0 kpc
  python3 plot_skymap.py -d 10.0 -e 100.0           # d=10 kpc, E=100 TeV 单张图
  python3 plot_skymap.py -d 0.5 -e 1,10,100,1e3,1e4 # 指定5个能量，多面板
"""
import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from astropy.io import fits
from pathlib import Path

# ---------- 参数 ----------
FITSFILE = "/share02/users/z/zhanglei/work/absorbed/absorb_github/absorption_map.fits"
OUTDIR   = "/share02/users/z/zhanglei/work/absorbed/absorb_github"

L_START, L_STEP, L_N = 0.0, 2.0, 181    # 0, 2, 4, ..., 360
B_START, B_STEP, B_N = -15.0, 0.5, 61   # -15, -14.5, ..., +15
D_START, D_STEP, D_N = 0.0, 0.5, 51     # 0, 0.5, ..., 25


def find_index(val, start, step, n, name):
    """值 → 数组索引"""
    idx = int(round((val - start) / step))
    if idx < 0 or idx >= n:
        raise ValueError(f"{name}={val} 超出范围 [{start}, {start + (n-1)*step}]")
    exact = start + idx * step
    if abs(val - exact) > step * 0.01:
        print(f"警告: {name}={val} 不在格点上，近似为 {exact}")
    return idx


def find_energy_index(e_val, energy):
    """找最接近的能量索引 (81 个对数等间隔点中)"""
    idx = np.argmin(np.abs(energy - e_val))
    return idx


def plot_single(ax, data_2d, title, l_vals, b_vals, vmin=None, vmax=None):
    """画单张 l-b 天图，银心 l=0 居中，l=-180° 至 +180°"""
    surv = data_2d  # survival probability e^{-tau}, shape (l=181, b=61)

    # 自动缩放：用 P1–P99 避免离群点挤压
    if vmin is None:
        vmin = np.nanpercentile(surv, 1)
    if vmax is None:
        vmax = np.nanpercentile(surv, 99)

    # 把 l=180° 滚到最左侧，银心 l=0 居中
    mid = 90
    surv_rolled = np.roll(surv, -mid, axis=0)

    img = ax.imshow(surv_rolled.T, origin='lower',
                    extent=[-180, 180, b_vals[0], b_vals[-1]],
                    aspect='auto', cmap='viridis', vmin=vmin, vmax=vmax,
                    interpolation='bilinear')
    ax.set_xticks([-180, -150, -120, -90, -60, -30, 0, 30, 60, 90, 120, 150, 180])
    ax.set_xlabel('l (deg)', fontsize=10)
    ax.set_ylabel('b (deg)', fontsize=10)
    ax.set_title(title, fontsize=10)
    ax.tick_params(labelsize=8)
    return img, vmin, vmax


def main():
    # 解析命令行
    d_val = 0.5
    e_list = None   # None = 全部 81 个能量点

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '-d' and i + 1 < len(args):
            d_val = float(args[i+1]); i += 2
        elif args[i] == '-e' and i + 1 < len(args):
            e_list = [float(x) for x in args[i+1].split(',')]; i += 2
        else:
            i += 1

    # 读取 FITS
    hdul = fits.open(FITSFILE)
    data = hdul[0].data       # (l=181, b=61, d=51, E=81)
    energy = hdul[1].data['E_TeV']
    hdul.close()

    id_ = find_index(d_val, D_START, D_STEP, D_N, "d")
    d_exact = D_START + id_ * D_STEP

    l_vals = np.array([L_START + i * L_STEP for i in range(L_N)])
    b_vals = np.array([B_START + i * B_STEP for i in range(B_N)])

    # 选能量点
    if e_list is None:
        e_idx = list(range(81))
        e_selected = energy
    else:
        e_idx = [find_energy_index(e, energy) for e in e_list]
        e_selected = energy[e_idx]

    n_e = len(e_idx)

    print(f"距离: d = {d_exact:.1f} kpc")
    print(f"能量: {n_e} 个点")

    # ---------- 画图 ----------
    if n_e == 1:
        fig, ax = plt.subplots(figsize=(14, 6))
        data_slice = data[:, :, id_, e_idx[0]]
        title = f"d = {d_exact:.1f} kpc,  E = {e_selected[0]:.2e} TeV"
        _, vmin, vmax = plot_single(ax, data_slice, title, l_vals, b_vals)
        cbar = plt.colorbar(ax.images[0], ax=ax,
                            label=f'$e^{{-\\tau}}$  [{vmin:.3f} – {vmax:.3f}]')
        cbar.ax.tick_params(labelsize=10)
    elif n_e <= 12:
        # 1-12 个能量：排成一行多列或多行
        ncols = min(n_e, 4)
        nrows = int(np.ceil(n_e / ncols))
        fig, axes = plt.subplots(nrows, ncols, figsize=(4.5*ncols, 3*nrows))
        axes = np.atleast_1d(axes).flatten()
        for k, (ei, ev) in enumerate(zip(e_idx, e_selected)):
            data_slice = data[:, :, id_, ei]
            plot_single(axes[k], data_slice,
                        f"E = {ev:.2e} TeV", l_vals, b_vals)
        # 隐藏多余子图
        for k in range(n_e, len(axes)):
            axes[k].set_visible(False)
        plt.tight_layout()
    else:
        # 81 个能量点：9×9 面板
        ncols, nrows = 9, 9
        fig = plt.figure(figsize=(24, 20))
        fig.suptitle(f"Survival Probability  $e^{{-\\tau}}$   (d = {d_exact:.1f} kpc)",
                     fontsize=16, y=0.98)
        gs = GridSpec(nrows, ncols, figure=fig,
                      left=0.04, right=0.96, top=0.94, bottom=0.04,
                      hspace=0.35, wspace=0.20)

        for k, (ei, ev) in enumerate(zip(e_idx, e_selected)):
            row, col = divmod(k, ncols)
            ax = fig.add_subplot(gs[row, col])
            data_slice = data[:, :, id_, ei]
            plot_single(ax, data_slice,
                        f"E = {ev:.2e} TeV", l_vals, b_vals)

    # 保存
    if e_list is None:
        outname = f"skymap_d{d_exact:.1f}_allE.pdf"
    elif len(e_list) == 1:
        outname = f"skymap_d{d_exact:.1f}_E{e_list[0]:.2e}.pdf"
    else:
        outname = f"skymap_d{d_exact:.1f}_multiE.pdf"

    outpath = Path(OUTDIR) / outname
    fig.savefig(outpath, bbox_inches='tight')
    plt.close(fig)
    print(f"PDF 已保存: {outpath}")


if __name__ == '__main__':
    main()
