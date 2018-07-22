#!/bin/bash

set -e
set +x

for FILE in img/bench/webp-src/*.jpg; do
	OUT="${FILE%.*}.webp"
	OUT2X="${FILE%.*}@2x.webp"
	cwebp -mt -resize 160 0 -q 40 $FILE -o $OUT
	cwebp -mt -q 40 $FILE -o $OUT2X
done

mv img/bench/webp-src/*.webp img/bench/
