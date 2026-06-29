#!/bin/bash
# 合并拆分的 FITS 文件
cat abs_map.part_* > absorption_map.fits
echo "合并完成: absorption_map.fits"
