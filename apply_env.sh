#!/bin/bash
set -e

cd ~/AnonXMusic

echo "Stopping old bot..."
screen -S anonxmusic -X quit || echo "No screen session to quit"

echo "Writing new .env..."
cat > .env << 'EOF'
# from my.telegram.org/apps
API_ID=35660683
API_HASH=7afb42cd73fb5f3501062ffa6a1f87f7

# from @BotFather on telegram
BOT_TOKEN=8551975632:AAHPhKGajn1NwBoP4XuIzEkxkRPBXqaC6yI
LOGGER_ID=-1003150808065

# mongo url from cloud.mongodb.com
MONGO_URL=mongodb+srv://teamdaxx123:teamdaxx123@cluster0.ysbpgcp.mongodb.net/?retryWrites=true&w=majority

OWNER_ID=5147822244

# pyrogram session from @StringFatherBot on telegram
SESSION=BQFLMyQAnZIcgriaz5jwQOjJeMu_CFGEjo3LJfN2uv9YkxS1YSuedyhK0N9ZuV_WQ7g_WkinAMiH2KNI5XtfnZnbum5l2NLlZuLROPrLZ8yf3aw5mmkGcavzKS-Ni77XMqO4bEsDUMbc-lhMgTofnlGz3q_wojApm28E6C3zQ-43Cmb9XTgb-lbRtSsUxMm2pXmY8qxFOOtFJc2NNu3GN1emr-YLcQ4E7LHa5O5Xgl7CDiGkVQFvT3eE8JpbLqw0dAvEFJsNhUZqo4p57PhHpYQd7Gr7Nnby3vTB4HpW1mRDAaA_HQxCJsnxth-wVdQECOanIonTUoTrludm0cXWw6b6e-SU-wAAAAH32icvAA

# NEW — Hybrid Router
COBALT_URL=http://127.0.0.1:9000
JIOSAAVN_API_URL=https://saavn.dev
EOF

echo "Starting bot again..."
screen -dmS anonxmusic bash start

echo "Waiting for bot to start..."
sleep 12
tail -n 25 log.txt
