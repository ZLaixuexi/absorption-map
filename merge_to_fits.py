#!/usr/bin/env python3
# ===========================================================================
# 将 563,091 个吸收谱输出文件合并为单个 FITS 文件
#
# 输出结构：4D ImageHDU (l=181, b=61, d=51, E=81)
# 能量范围: 0.1 – 10^7 TeV, 对数等间隔, 81 个点
# ===========================================================================
import os
import gc
import numpy as np
from astropy.io import fits
from datetime import datetime

# ---------- 参数 ----------
OUTDIR  = "/share02/users/z/zhanglei/work/absorbed/absorb_github/all_output"
FITSOUT = "/share02/users/z/zhanglei/work/absorbed/absorb_github/absorption_map.fits"

l_vals = [i * 2 for i in range(0, 181)]            # 整数: 0, 2, 4, ..., 360
b_vals = [round(i * 0.5, 2) for i in range(-30, 31)]  # -15.0, -14.5, ..., 15.0
d_vals = [round(i * 0.5, 2) for i in range(0, 51)]    # 0.0, 0.5, ..., 25.0

nl, nb, nd = len(l_vals), len(b_vals), len(d_vals)
ne = 81

print(f"l: {nl} 个 ({l_vals[0]} – {l_vals[-1]}°)")
print(f"b: {nb} 个 ({b_vals[0]} – {b_vals[-1]}°)")
print(f"d: {nd} 个 ({d_vals[0]} – {d_vals[-1]} kpc)")
print(f"E: {ne} 个 (0.1 – 1e7 TeV)")
print(f"数据总量: {nl} × {nb} × {nd} × {ne} = {nl * nb * nd * ne:,} 个 float32 ≈ {nl * nb * nd * ne * 4 / 1024**3:.1f} GB")
print()

# ---------- 分配 4D 数组 ----------
data = np.full((nl, nb, nd, ne), np.nan, dtype=np.float32)
energy_grid = None

# ---------- 逐个读取文件 ----------
total   = nl * nb * nd
missing = 0
count   = 0

for il, l_val in enumerate(l_vals):
    for ib, b_val in enumerate(b_vals):
        for id_, d_val in enumerate(d_vals):
            l_str = str(l_val) if l_val >= 0 else f"{l_val}"
            b_str = str(b_val) if b_val >= 0 else f"{b_val}"
            d_str = str(d_val) if d_val >= 0 else f"{d_val}"
            fname = f"l{l_str}_b{b_str}_d{d_str}.txt"
            fpath = os.path.join(OUTDIR, fname)

            count += 1
            if not os.path.isfile(fpath):
                missing += 1
                continue

            try:
                arr = np.loadtxt(fpath, dtype=np.float32, ndmin=2)
                if arr.shape[0] != ne:
                    missing += 1
                    continue

                if energy_grid is None:
                    energy_grid = arr[:, 0].astype(np.float64).copy()

                # 第2列为吸收因子
                data[il, ib, id_, :] = arr[:, 1]
            except Exception:
                missing += 1
                continue

            if count % 50000 == 0:
                pct = count / total * 100
                print(f"\r进度: {count:,} / {total:,} ({pct:.1f}%)  — 缺 {missing} 个", end="", flush=True)

print(f"\r进度: {count:,} / {total:,} (100.0%)  — 缺 {missing} 个", flush=True)
print()

if energy_grid is None:
    print("错误：未能从任何文件中读取能量网格！")
    exit(1)

print(f"能量网格: {energy_grid[0]:.1f} – {energy_grid[-1]:.2e} TeV, 共 {len(energy_grid)} 个点")

# ---------- 统计 NaN ----------
nan_count = np.sum(np.isnan(data))
print(f"NaN 像素数: {nan_count:,} / {data.size:,} ({nan_count / data.size * 100:.2f}%)")

# ---------- 写入 FITS ----------
print(f"\n写入 FITS: {FITSOUT}")

hdu = fits.PrimaryHDU(data)
hdr = hdu.header

hdr['CTYPE1']  = ('Energy',   'Energy axis (TeV)')
hdr['CTYPE2']  = ('Distance', 'Distance axis (kpc)')
hdr['CTYPE3']  = ('GLAT',     'Galactic latitude b (degree)')
hdr['CTYPE4']  = ('GLON',     'Galactic longitude l (degree)')

hdr['CRPIX1'] = (1.0, 'Reference pixel (energy)')
hdr['CRVAL1'] = (float(energy_grid[0]), 'Reference value (TeV)')
hdr['CDELT1'] = (0.0, 'Log spacing, see ENERGY_GRID extension')

hdr['CRPIX2'] = (1.0, 'Reference pixel (distance)')
hdr['CRVAL2'] = (float(d_vals[0]), 'Reference value (kpc)')
hdr['CDELT2'] = (float(d_vals[1] - d_vals[0]), 'Step (kpc)')

hdr['CRPIX3'] = (1.0, 'Reference pixel (latitude)')
hdr['CRVAL3'] = (float(b_vals[0]), 'Reference value (degree)')
hdr['CDELT3'] = (float(b_vals[1] - b_vals[0]), 'Step (degree)')

hdr['CRPIX4'] = (1.0, 'Reference pixel (longitude)')
hdr['CRVAL4'] = (float(l_vals[0]), 'Reference value (degree)')
hdr['CDELT4'] = (float(l_vals[1] - l_vals[0]), 'Step (degree)')

hdr['E_MIN']  = (float(energy_grid[0]), 'Min energy (TeV)')
hdr['E_MAX']  = (float(energy_grid[-1]), 'Max energy (TeV)')
hdr['E_NUM']  = (len(energy_grid), 'Number of energy bins')
hdr['D_MIN']  = (float(d_vals[0]), 'Min distance (kpc)')
hdr['D_MAX']  = (float(d_vals[-1]), 'Max distance (kpc)')
hdr['L_MIN']  = (float(l_vals[0]), 'Min longitude (degree)')
hdr['L_MAX']  = (float(l_vals[-1]), 'Max longitude (degree)')
hdr['B_MIN']  = (float(b_vals[0]), 'Min latitude (degree)')
hdr['B_MAX']  = (float(b_vals[-1]), 'Max latitude (degree)')
hdr['MISSING'] = (missing, 'Number of missing/corrupt files')
hdr['DATE']   = (datetime.now().strftime('%Y-%m-%dT%H:%M:%S'), 'Creation time')
hdr['CREATOR'] = ('merge_to_fits.py', 'Creator script')
hdr['COMMENT'] = 'Absorption 4D data cube (l, b, d, E)'
hdr['COMMENT'] = 'Energy: 0.1 - 1e7 TeV, log-spaced, 81 bins'
hdr['COMMENT'] = f'Longitude: {l_vals[0]} - {l_vals[-1]} deg, step {l_vals[1]-l_vals[0]} deg'
hdr['COMMENT'] = f'Latitude:  {b_vals[0]} - {b_vals[-1]} deg, step {b_vals[1]-b_vals[0]} deg'
hdr['COMMENT'] = f'Distance:  {d_vals[0]} - {d_vals[-1]} kpc, step {d_vals[1]-d_vals[0]} kpc'

# ---------- 能量网格扩展表（仅 TeV）----------
e_hdu = fits.BinTableHDU.from_columns([
    fits.Column(name='INDEX', format='I', array=np.arange(1, ne + 1, dtype=np.int32)),
    fits.Column(name='E_TeV', format='D', array=energy_grid, unit='TeV'),
])
e_hdu.header['EXTNAME'] = 'ENERGY_GRID'

# ---------- 写入 ----------
hdul = fits.HDUList([hdu, e_hdu])
hdul.writeto(FITSOUT, overwrite=True)

print(f"\n完成！")
print(f"  主图像:      {FITSOUT}  [{nl}×{nb}×{nd}×{ne}]")
print(f"  扩展表:      ENERGY_GRID [{ne} 行]")
print(f"  文件大小:    {os.path.getsize(FITSOUT) / 1024**3:.2f} GB")
print(f"  缺失文件数:  {missing}")

del data
gc.collect()
