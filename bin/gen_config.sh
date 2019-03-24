#!/bin/sh


connection_file=connection.txt
default_tau=1
default_const=1

if [ -f "$1" ]; then
	connection_file=$1
elif [ ! -f "$connection_file" ]; then
	echo "usage: $0 file"
	exit
fi

awk -v default_tau="$default_tau" -v default_const="$default_const" '
BEGIN{
	m = n = 0;
	exception = 0;
}
{
	sub(/#.*/,"");
	if ($0 ~ "=") {
		str = $0;
		sub(/\(.*/, "", str);
		split(str, a, "=");
		name[m] = a[1];
		#gsub(/^[[:space:]]+|[[:space:]]+$/,"",name[m]);
		gsub(/^ +| +$/,"",name[m]);
    size[m] = a[2];
		if (name[m] ~ /^[[:digit:]]/) {
		#if (name[m] ~ /^[0-9]/) {
			printf("Error! name is invalid\n");
			exception = 1;
			exit;
		}
		if (size[m] <= 0) {
			printf("Error! size <= 0\n");
			exception = 1;
			exit;
		}

		tau[m] = default_tau;
		const[m] = default_const;
		if ($0 ~ /\(.*\)/) {
			str = $0;
			sub(/\).*/, "", str);
			sub(/.*\(/, "", str);
			split(str, a, ",");
			for (i in a) {
				split(a[i], b, "=");
				if (b[1] ~ "tau") {
					tau[m] = b[2];
				}
				if (b[1] ~ "is_init_const") {
					const[m] = b[2];
				}
			}
		}
		m++;
	} else if ($0 ~ "->") {
		split($0, a, "->");
		split(a[1], x, ",");
		split(a[2], y, ",");
		for (i in x) {
			#gsub(/^[[:space:]]+|[[:space:]]+$/,"",x[i]);
			gsub(/^ +| +$/,"",x[i]);
			for (j in y) {
				#gsub(/^[[:space:]]+|[[:space:]]+$/,"",y[j]);
				gsub(/^ +| +$/,"",y[j]);
				from[n] = x[i];
				to[n] = y[j];
				n++
			}
		}
	}
}
END {
	if (exception) {
		exit;
	}
	c_state_size=0;
	for (i=0; i < m; i++) {
		printf("# name:%s, size:%d, tau:%f, is_init_const:%d\n", name[i], size[i], tau[i], const[i]);
		name2index[i] = (c_state_size+1) "-" (c_state_size+size[i]);
		c_state_size += size[i];
	}
	for (i=0; i < n; i++) {
		printf("# %s to %s\n", from[i], to[i]);
		for (j=0; j < m; j++) {
			if (from[i] == name[j]) {
				from_index[i] = name2index[j];
			}
			if (to[i] == name[j]) {
				to_index[i] = name2index[j];
			}
		}
	}

	printf("c_state_size=%d\n", c_state_size);

	str = "init_tau=";
	sum = 1;
	for (i=0; i < m; i++) {
		str = sprintf("%s%f:%d-%d,", str, tau[i], sum, sum + size[i] - 1);
		sum += size[i];
	}
	sub(/,$/, "", str);
	printf("%s\n", str);

	str = "const_init_c=";
	sum = 1;
	for (i=0; i < m; i++) {
		if (const[i] != 0) {
			str = sprintf("%s%d-%d,", str, sum, sum + size[i] - 1);
		}
		sum += size[i];
	}
	sub(/,$/, "", str);
	printf("%s\n", str);

	str = "connection_i2c=";
	for (i=0; i < n; i++) {
		#if (from[i] ~ /^[[:digit:]]/ && !(to[i] ~ /^[[:digit:]]/)) {
		if (from[i] ~ /^[0-9]/ && !(to[i] ~ /^[0-9]/)) {
			str = sprintf("%s%st%s,", str, from[i], to_index[i]);
		}
	}
	sub(/,$/, "", str);
	if (str == "connection_i2c=") {
		str = sprintf("%s-t-", str);
	}
	printf("%s\n", str);

	str = "connection_c2c=";
	for (i=0; i < n; i++) {
		#if (!(from[i] ~ /^[[:digit:]]/) && !(to[i] ~ /^[[:digit:]]/)) {
		if (!(from[i] ~ /^[0-9]/) && !(to[i] ~ /^[0-9]/)) {
			str = sprintf("%s%st%s,", str, from_index[i], to_index[i]);
		}
	}
	sub(/,$/, "", str);
	if (str == "connection_c2c=") {
		str = sprintf("%s-t-", str);
	}
	printf("%s\n", str);

	str = "connection_c2o=";
	for (i=0; i < n; i++) {
		#if (!(from[i] ~ /^[[:digit:]]/) && to[i] ~ /^[[:digit:]]/) {
		if (!(from[i] ~ /^[0-9]/) && to[i] ~ /^[0-9]/) {
			str = sprintf("%s%st%s,", str, from_index[i], to[i]);
		}
	}
	sub(/,$/, "", str);
	if (str == "connection_c2o=") {
		str = sprintf("%s-t-", str);
	}
	printf("%s\n", str);

	str = "connection_c2v=";
	for (i=0; i < n; i++) {
		#if (!(from[i] ~ /^[[:digit:]]/) && to[i] ~ /^[[:digit:]]/) {
		if (!(from[i] ~ /^[0-9]/) && to[i] ~ /^[0-9]/) {
			str = sprintf("%s%st%s,", str, from_index[i], to[i]);
		}
	}
	sub(/,$/, "", str);
	if (str == "connection_c2v=") {
		str = sprintf("%s-t-", str);
	}
	printf("%s\n", str);
}
' $connection_file

