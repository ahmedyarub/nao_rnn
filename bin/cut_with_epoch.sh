#!/bin/sh

if [ -f "$1" ]; then
	file=$1
else
	file=state000000.log
fi

if [ "$2" ]; then
	epoch=$2
	awk -v epoch="$epoch" 'BEGIN{flag=0}{if($0 ~ "^# epoch ="){split($0,a,"=");if(a[2] == epoch){flag=1}else{flag=0}} if(flag==1){print $0}}' $file
else
	t_len=`awk '($0 ~ "^#"){if($0 ~ /^# target [0-9]+\tlength =/){split($0, a, "\t"); sub(/# target/, "", a[1]); target=int(a[1]); split(a[2], b, "="); t_len[target] = int(b[2]);} else if($0 ~ "^# target:"){str=$0; gsub(/^# target:|\(.+\)| +/,"",str);target=int(str); printf("%d\n", t_len[target]+3); exit;}}' $file`
	tail -n $t_len $file | awk 'BEGIN{flg=0}{if(flg==0){if($0 ~ "^# epoch ="){flg=1}}if(flg==1){print $0}}'
fi


