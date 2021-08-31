# Simple shell script to clean up all the log files created by the CRON jobs


tar -zcvf "$(date '+%Y-%m-%d')trade_logs.tar.gz" trade*.log

rm trade*.log
