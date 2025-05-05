#! /bin/bash

.venv/bin/python bot.py  &  PID_MAIN=$!
.venv/bin/python bot_admin.py &  PID_ADMIN=$!

wait $PID_MAIN
wait $PID_ADMIN