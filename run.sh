export PYTHONPATH='./config'
./ramoi.py vision /airflow  172.16.30.19:2181 --start_service="airflow scheduler" --service_max_run=-1
