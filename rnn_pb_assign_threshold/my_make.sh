#!/bin/sh

if test ! -f configure; then
    ./autogen.sh
fi

if test x"$1" = xtest; then
    cd src/unit-test
    ./rnn-unit-test
    srcs=`awk '($0 ~ "rnn_unit_test_SOURCES") {split($0, s, "="); print s[2];}' Makefile.am`
    for src in $srcs
    do
        gcov -n -b $src
    done
    exit
fi

./configure --prefix=$HOME CC=gcc CFLAGS="-Wall -Wextra -Wno-unused-parameter -O3"
#./configure --prefix=$HOME --disable-assert CC=gcc CFLAGS="-Wall -Wextra -Wno-unused-parameter -O3"
#./configure --prefix=$HOME --disable-assert CC=gcc CFLAGS="-Wall -Wextra -Wno-unused-parameter -O3 -pipe -fomit-frame-pointer -funroll-loops -fprefetch-loop-arrays -falign-functions=4 -fforce-addr -march=pentium3 -msse2 -mfpmath=sse"
#./configure --prefix=$HOME CC=gcc CFLAGS="-std=c99 -pedantic -Wall -Wextra -Wno-unused-parameter -g -O"
#./configure --prefix=$HOME CC=gcc CFLAGS="-Wall -Wextra -Wno-unused-parameter -O3 -fprofile-arcs -ftest-coverage -fstack-check -g"
#./configure --prefix=$HOME CC=gcc CFLAGS="-Wall -Wextra -Wno-unused-parameter -O3 -g -pg"
#./configure --prefix=$HOME --disable-assert CC=icc CFLAGS="-O3"

make
#make install

