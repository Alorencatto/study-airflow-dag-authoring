from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.decorators import task, dag
from airflow.utils.task_group import TaskGroup
from airflow.operators.dummy import DummyOperator

from datetime import datetime, timedelta
from typing import Dict


services: dict = {
    "service_globo": {"name": "Globo", "api": "www.google.com"},
    "service_record": {"name": "Record", "api": "www.google.com"},
    "service_redetv": {"name": "RedeTv", "api": "www.google.com"},

}

default_args = {
    "start_date": datetime(2021, 1, 1)
}


def _choosing_service_based_on_day(execution_date):
    """
    Always return task id
    """
    day = execution_date.day_of_week

    # Mocking for test
    # day: int = 5

    print(day)
    if (day == 0):
        return 'extract_service_redetv'
    if (day == 1):
        return 'extract_service_globo'

    return 'stop'


@task.python
def process_a(partner_name, partner_path):
    print(partner_name)
    print(partner_path)


@task.python
def process_b(partner_name, partner_path):
    print(partner_name)
    print(partner_path)


@task.python
def process_c(partner_name, partner_path):
    print(partner_name)
    print(partner_path) @ task.python


@task.python
def check_a():
    print("checking")


def check_b():
    print("checking")


def process_tasks(service_settings):
    with TaskGroup(group_id = "process_tasks", add_suffix_on_collision = True) as process_tasks:
        # with TaskGroup(group_id = "test_tasks") as process_tasks:
        #     check_a()
        #     check_b()

        process_a(service_settings['service_name'], service_settings['service_path'])
        process_b(service_settings['service_name'], service_settings['service_path'])

    return process_tasks


@dag(description = "DAG for praticing branching",
     default_args = default_args,
     schedule_interval = None,
     dagrun_timeout = timedelta(minutes = 10),
     tags = ['mine', 'branching'],
     catchup = False, max_active_runs = 1)
def mine_branching_1():
    start = DummyOperator(task_id = "start")
    stop = DummyOperator(task_id = "stop")

    final_task = DummyOperator(task_id = "final_task", trigger_rule = 'none_failed_or_skipped')

    choosing_service_based_on_day = BranchPythonOperator(
            task_id = "branching_based_on_service",
            python_callable = _choosing_service_based_on_day
    )

    choosing_service_based_on_day >> stop >> final_task

    for service, details in services.items():
        @task.python(task_id = f"extract_{service}", do_xcom_push = False, multiple_outputs = True)
        def extract(service_name: str, service_path: str) -> dict:
            return {"service_name": service_name, "service_path": service_path}

        extracted_values = extract(details['name'], details['api'])

        start >> choosing_service_based_on_day >> extracted_values
        process_tasks(extracted_values) >> final_task

    # storing = DummyOperator(task_id = "storing", trigger_rule = 'none_failed_or_skipped')
    #
    # choosing_pertner_based_on_day = BranchPythonOperator(
    #         task_id = 'choosing_pertner_based_on_day',
    #         python_callable = _choosing_pertner_based_on_day
    # )
    #
    # choosing_pertner_based_on_day >> stop
    #
    # for partner, details in partners.items():
    #     @task.python(task_id = f"extract_{partner}", do_xcom_push = False, multiple_outputs = True)
    #     def extract(partner_name, partner_path):
    #         return {"partner_name": partner_name, "partner_path": partner_path}
    #
    #     extracted_values = extract(details['name'], details['path'])
    #     start >> choosing_pertner_based_on_day >> extracted_values
    #     process_tasks(extracted_values) >> storing


dag = mine_branching_1()
