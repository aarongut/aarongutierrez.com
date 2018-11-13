#!/bin/bash

set -e
set +x

for FILE in img/bench/webp-src/*.jpg; do
	FULLNAME=$(basename -- ${FILE})
	NAME=${FULLNAME%.*}
	OUT="img/bench/${NAME}.webp"
	OUT2X="img/bench/${NAME}@2x.webp"
	echo "Checking for \"${OUT}\"..."
	if [ ! -f "${OUT}" ]; then
		echo "Would thumbnail ${OUT}"
		cwebp -mt -resize 160 0 -q 40 ${FILE} -o ${OUT}
	fi
	if [ ! -f "${OUT2X}" ]; then
		echo "Would thumbnail@2x ${OUT2X}"
		cwebp -mt -q 40 ${FILE} -o ${OUT2X}
	fi
done
