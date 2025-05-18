
PASSWORD="apple"

cd $(dirname $0)

./nettool -p $PASSWORD say "60秒後に定期セーブを行います。"

sleep 50

./nettool -p $PASSWORD say "まもなくセーブを開始します。"

sleep 10

./nettool -p $PASSWORD force-sync

sleep 120

SAVEFILE="$(date +hourly-%H).sve"
cp nanasaba1st-body/server13353-network.sve nanasaba1st-body/save/$SAVEFILE
