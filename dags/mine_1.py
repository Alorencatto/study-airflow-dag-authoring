
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.decorators import task, dag

from datetime import datetime, timedelta

@dag(description="Scheduling",
        start_date=datetime(2023, 1, 31),
        schedule_interval='*/10 * * * *',
        dagrun_timeout=timedelta(minutes=10),
        tags=['mine', 'scheduling'],
        catchup=False    )
def dag_mine_1():
    
    t1 = BashOperator(
        task_id="display",
        # bash_command="echo 'execution date : {{ ds }} modified by macros.ds_add to add 5 days : {{ macros.ds_add(ds, 5) }}'"
        bash_command="echo 'execution date : {{ ds }} | Next execution date {{ next_execution_date }}| Execution start {{ data_interval_start }}, Execution end {{ data_interval_end }} | Previous date interval success start {{ prev_data_interval_start_success }}, Previous date interval success end {{ prev_data_interval_end_success }}'"
    )

    @task.python
    def extract(): # ti = task instance object
        partner_name = "netflix"
        return partner_name

    @task.python
    def process(partner_name):
        print(partner_name)
        
        # Printando as variáveis template de agendamento
        print("Execution date : ",'{{ execution_date }} {{ ds }}')
        print("Next execution date : ","{{ next_execution_date }}")
        print("Previous date interval success start {{ prev_data_interval_start_success }}, Previous date interval success end {{ prev_data_interval_end_success }}")
        print("Execution start {{ data_interval_start }}, Execution end {{ data_interval_end }}")
        
        

    process(extract()) >> t1

dag = dag_mine_1()
