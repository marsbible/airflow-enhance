export PYTHONPATH='./config:./plugins'
export AIRFLOW_HOME=`pwd`

airflow worker --stdout ~/airflow/airflow-worker.out --stderr ~/airflow/airflow-worker.err -l ~/airflow/airflow-worker.log -D
airflow webserver --stdout ~/airflow/airflow-webserver.out --stderr ~/airflow/airflow-webserver.err -l ~/airflow/airflow-webserver.log -D
airflow scheduler --stdout ~/airflow/airflow-scheduler.out --stderr ~/airflow/airflow-scheduler.err -l ~/airflow/airflow-scheduler.log -D
