#!/bin/sh

for file in $@
do
	awk -v cfile="$file" '
	BEGIN{
		keyword[1] = "void";
		keyword[2] = "char";
		keyword[3] = "int";
		keyword[4] = "long";
		keyword[5] = "float";
		keyword[6] = "double";
		keyword[7] = "signed";
		keyword[8] = "unsigned";
		keyword[9] = "const";
		keyword[10] = "extern";
		keyword[11] = "static";
		keyword[12] = "struct";
		keyword[13] = "enum";
		keyword[14] = "union";
		keyword[15] = "inline";
		keyword[16] = "restrict";
		keyword[17] = "_Bool";
		keyword[18] = "_Complex";
		keyword[19] = "_Imaginary";
		func_block = 0;
	}
	{
		gsub(/\t/,"    ")
		if (length($0) > 80) {
			printf("length of line is over 80 columns: %s : %d\n", cfile, NR);
		}
		if ($0 ~ " $") {
			printf("end of line is space: %s : %d\n", cfile, NR);
		}
		#if ($0 ~ "if[[:space:]]*\(.*\).*alloc") {
		#	printf("use alloc in if: %s : %d\n", cfile, NR);
		#}
		#if ($0 ~ "if[[:space:]]*\(.*\).*fopen") {
		#	printf("use fopen in if: %s : %d\n", cfile, NR);
		#}
		str = $0;
		num = NR;
	}
	(func_block == 0) {
		for (i = 1; i <= 19; i++) {
			if ($0 ~ "^" keyword[i]) {
				if (sub(/\(.*/, "", $0) != 0) {
					func_block = 1;
					k_and_r_style = 0;
					break;
				}
			}
		}
	}
	(func_block == 1) {
		if ($0 ~ "^{") {
			k_and_r_style = 1;
		}
		if ($0 ~ "^}$") {
			if (!k_and_r_style) {
				printf("Not K&R style: %s : %d\n", cfile, NR);
			}
			func_block = 0;
		}
	}
	END {
		if (!(str ~ /^$/)) {
			printf("end of file is not line feed code: %s : %d\n", cfile, num);
		}
	}
	' $file
done

