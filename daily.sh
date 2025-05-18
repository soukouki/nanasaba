
cd $(dirname $0)

SAVEFILE="daily-$(date +%Y-%m-%d).sve"
echo "\$SAVEFILE=$SAVEFILE"

cp nanasaba1st-body/server13353-network.sve $SAVEFILE

# 注意: nanasaba1st-body.zipはsaveを含まないようにする

cp $SAVEFILE nanasaba1st-body/save
zip nanasaba1st-body-with-saves nanasaba1st-body/save/$SAVEFILE

cp $SAVEFILE nanasaba1st-saves
zip nanasaba1st-saves nanasaba1st-saves/$SAVEFILE

rm $SAVEFILE

sftp proxy <<EOF
  cd nginx-file-server/public
  put nanasaba1st-body-with-saves.zip
  put nanasaba1st-saves.zip
  bye
EOF
