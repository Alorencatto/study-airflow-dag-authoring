# Estudo Astro Certification DAG Authoriting

## Parâmetros básicos de agendameto  
- start_date : datetime -> Data na qual a tarefa começa a ser schedulada  
- schedule_interval : datetime -> Intervalo entre o valor mínimo do start_date + o valor do intervalo, no qual a dag será acionada.  
- catchup : bool -> Parâmetro que define se as dags serão acionadas de forma retroativa com base no `start_date`.
  Se `false`, será desabilitado o acionamento das dags retroativas.

*Portanto* : A DAG X começará a ser schedulada a partir do `start_date` e será acionada **depois** de todo `schedule_interval`  

  - Porquê ao pausar e retornar o processo a DAG não executa sozinha? (TODO)

## Crontab X Timedelta

  - **Crontab** -> Definição de agendamento absoluta, que não possuí estado  
    ```
    */10 * * * * -> A cada 10 minutos
    10 * * * * -> No minuto 10 de cada hora
    10 5-8 * * * -> No minuto 10 de cada hora entre 5 e 8 horas
    ```

  - **Cron "preset"** -> Padrões de cron abstraídos na aplicação do airflow.  
    Exemplo : 
      - @hourly -> 0 * * * * -> Sempre no começo de uma hora  
      - @daily -> 0 0 * * * -> Sempre as 00:00  

  
  - **Timedelta** -> possuí estado, sendo dinâmico. Quando se usa o timedelta, o agendamento está sempre relacionado com a última executação (`start_date`). É útil para pipelines em que é necessário um período de tempo entre as suas execuções.

  **Obs: Se não for necessário o agendamento do pipeline, sendo seu funcionamento acionado manulamente na interface ou via API, pode ser usar o valor `None` no parâmetro `schedule_interval`.


## Características das tasks 

- Determinism -> Para a mesma entrada, deve-se obter a mesma saída em uma task  
- Indempotent -> Se a DAG for executada múltiplas vezes, deve-se obter o mesmo resultado.

**obs: Lembrar que as tarefas podem ser executadas múltiplas vezes
    
## Backfilling (preenchimento)

- Catchup = True -> implica no acionamento de todas as dagruns (agendamento das DAGs) desde a data do parâmetro `start_date` até a data atual (current_date). Para isso, quando não queremos esse tipo de comportamento, basta manter o parâmetro catchup = False.  

- Para forçar o backfilling, podemos através da CLI utilizar o comando como mostra no exemplo a seguir : 
  `airflow dags backfill -s 2020-01-01 -e 2021-01-01 <nome da dag>` 

- O Parâmetro `max_active_runs`, controla quantos processos a mesma DAG pode estar ativa no mesmo tempo. Por exemplo, se `max_active_runs`=1, evitamos que o mesmo processo esteja rodando no mesmo tempo mais de uma vez.

---

## Variáveis  

As variáveis no Airflow, são definidas em um modelo chave -> valor, possuindo também uma descrição. Estas são armazendas no banco de metadados da aplicação, podendo ser usadas globalmente, através do package `airflow.models`, com a classe `Variable`.

- Criando variáveis
  - UI  
    Airflow UI -> Admin -> Variables -> add new record
  
  - Através de variáveis de ambiente no Dockerfile
    ```
    ENV AIRFLOW_VAR_VARIABLE_NAME_1='{"key1":"value1", "key2":"value2"}'
    ```
    **obs: Essas variáveis não vão estar disponíveis na UI e não vão estar armazenadas no banco de dados da aplicação. Ideal para evitar conexões com o banco de dados, e dados sensíveis.

  - Via CLI
  - Via REST API

## Taskflow API

- Templating  
  Os templates permitem passar as informações para as DAGs de forma dinâmica, e em tempo de execução.

  **Exemplos:
  ```
  {{ ds }}

  {{ data_interval_start }}

  {{ starting_date }} is {{ starting_date | days_to_now }}

  {{ macros.datetime.now() }}

  {{ execution_date.format('dddd') }}

  {{ dag_run.conf['numbers'] }}

  ```

- XCOMs

  Forma no Airflow de compartilhar dados (um dicionário, json , por exemplo) entre as tasks. Quando se realiza a operação de `push XCOM`, os dados são armazenados no banco de metadados da aplicação. Para recuperar esses dados, basta realizar o `pull XCOM`. Segue exemplo.

  * Através da task instance
  ```
  ti.xcom_push(key="partner_name", value=partner_name)
  ti.xcom_pull(key="partner_name", task_ids="extract")
  ```

  * Através da taskflow api, com funções
  ```
  @task.python
  def extract(): # ti = task instance object
      partner_name = "netflix"
      return partner_name

  @task.python
  def process(partner_name):
      print(partner_name)
  ```

  ** Limitações

  - Tamanho : As XCOMs são recomendadas para transferir dados com volumetria baixa, sendo seu limite :
    `sqlLite 2GB, Postgres 1GB, MySQL 64kB`
  
  - Podem ser observadas na interface, em Admin -> XCOMs

- TaskFlow API

  - Introduzida no Airflow 2.0
  - É caracterizada pela utilização de decorators  
    - @task.python on top of your python function  
    - @task.virtualenv  
    - @task_group  
    - @dag  
  - XCOM Args
    - Automaticamente cria dependências explicitas, como demonstrada no exemplo das XCOms
  
  - A DAG terá o nome da função decorada por `@dag`  
  
  - A tarefa terá o nome da função python
    Exemplo : A task terá o nome de `extract`
    ```
    @task.python
    def extract(): # ti = task instance object
        partner_name = "netflix"
        return partner_name
    ```
  
  - Para múltiplos XCOMs entre as tasks, utiliza-se o parâmetro `multiple_outputs` na task em que irá realizar o push.
    Exemplo : 
    ```
    @task.python(task_id="extract_partners", do_xcom_push=False, multiple_outputs=True)
    def extract():
        return {"partner_name":"neftlix", "partner_path":"/path/netflix"}

    @task.python
    def process(partner_name, partner_path):
        print(partner_name)
        print(partner_path)
    ```

  - No final do arquivo de definição da DAG, é necessário rodar essa função decorada por `@dag`, da seguinte forma : `dag = dag_303_taskflow()`, sendo a função decorada = `dag_303_taskflow`

  - Agrupamento de tarefas  

    - Subdags
      Trazem uma abordagem complicada, e necessita de associações específicas.Por trás dos panos, utilza um sensor que espera a tarefa completar, podendo ser customizado com os parâmetros `poke_interval` e `mode`. Além disso, é necessário especificar a `task_concurrency`. Dessa forma, não é recomendado sua utilização.
    - Task Groups