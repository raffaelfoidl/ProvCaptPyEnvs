#!/bin/bash
CHECKER="./prov-check-master/provcheck/provconstraints.py"

# download prov-check if not found locally
if [ ! -f "$CHECKER" ]; then
  URL="https://github.com/pgroth/prov-check/archive/master.zip"
  echo "Downloading and extracting prov-check..."
  echo "  URL: $URL"
  echo ""
  rm -rf prov-check-master
  wget $URL
  unzip master.zip
  rm master.zip
  echo "Done."
  echo ""
else
  echo "Found prov-check at $CHECKER"
  echo "  No download necessary"
  echo ""
fi

# specify maximum size of files to be validated
# in order to reduce validation runtime (here: 2048 Kilobytes)
DIR="../sample_data"
FILES=$(find $DIR -type f -size -2048k)
TOTAL=$(ls $FILES | wc -l)

echo "Start validation process..."
echo "  checking files from $DIR"
# iterate over files to be validated and print status information
COUNT=1 ; SIZE=0
for file in $FILES
do
  ((SIZE=$(wc -c < "$file") / 1000))
  echo -n "$COUNT/$TOTAL ($SIZE kB): "
  python $CHECKER $file
  ((COUNT+=1))
done
echo "Done."
