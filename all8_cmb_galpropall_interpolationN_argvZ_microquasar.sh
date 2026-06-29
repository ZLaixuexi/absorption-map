#!/bin/bash
IFS="
"
for LINE in `cat /afs/ihep.ac.cn/users/j/jlzhang/lhaasofs/absorb/data/XBCat/microquasar.txt |sort -t , -k 6n`
do
    #echo $LINE
    name=`echo $LINE |gawk -F, '{print $1}' `
    dist=`echo $LINE |gawk -F, '{print $6}' `
    dist=`echo "scale=5; ${dist}/1000."|bc`
    l=`echo $LINE |gawk -F, '{print $4}' `
    b=`echo $LINE |gawk -F, '{print $5}' `
    echo $name $dist $l $b
    echo ./all8_cmb_galpropall_interpolationN_argvZ $dist  $l $b \> data/microquasar/all8_cmb_galpropall_interpolationN_argvZ_$name.txt 
    ./all8_cmb_galpropall_interpolationN_argvZ $dist  $l $b > data/microquasar/all8_cmb_galpropall_interpolationN_argvZ_$name.txt 
done

