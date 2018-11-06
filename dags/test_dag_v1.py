import airflow
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from airflow.models import DAG
from airflow.operators import MyFirstOperator, MyFirstSensor

args = {'owner': 'airflow', 'start_date': airflow.utils.dates.days_ago(2)}

dag = DAG(dag_id='test_dag_v1', default_args=args, schedule_interval=None)


def printWorld(two, three, ds, **kwargs):
    print(" World")


hello = BashOperator(task_id='hello', bash_command='echo "hello"', dag=dag)
world = PythonOperator(
    task_id='world', op_args=['222', '333'], provide_context=True, python_callable=printWorld, dag=dag)
operator_task = MyFirstOperator(my_operator_param='This is a test.', task_id='my_first_operator_task', dag=dag)
sensor_task = MyFirstSensor(task_id='my_sensor_task', poke_interval=30, dag=dag)

hello >> world >> sensor_task >> operator_task


if __name__ == "__main__":
    dag.cli()
