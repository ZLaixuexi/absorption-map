#!/bin/bash
IFS="
"
for LINE in `grep 'LHAASO' /afs/ihep.ac.cn/users/j/jlzhang/lhaasofs/absorb/data/1LHAASO_PeVCat_DistOrder_lb.txt`
do
    #echo $LINE
    name=`echo $LINE |gawk '{print $1}' `
    dist=`echo $LINE |gawk '{print $2}' `
    l=`echo $LINE |gawk '{print $3}' `
    b=`echo $LINE |gawk '{print $4}' `
    echo $name $dist $l $b
    echo ./all8_cmb_galpropall_interpolationN_argvZ $dist  $l $b \> data/1LHAASO/all8_cmb_galpropall_interpolationN_argvZ_$name.txt 
    if [ -f data/1LHAASO/all8_cmb_galpropall_interpolationN_argvZ_$name.txt ]; then
       echo exist!!!
       continue
    fi
    ./all8_cmb_galpropall_interpolationN_argvZ $dist  $l $b > data/1LHAASO/all8_cmb_galpropall_interpolationN_argvZ_$name.txt 
done

