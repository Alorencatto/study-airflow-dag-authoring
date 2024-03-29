# Estudo Astro Certification DAG Authoriting

## Parâmetros básicos de agendameto  
- start_date : datetime -> Data na qual a tarefa começa a ser schedulada. Em suma, quando a DAG começará a ser agendadada.  
- schedule_interval : datetime -> Intervalo entre o valor mínimo do start_date + o valor do intervalo, no qual a dag será acionada.  
- catchup : bool -> Parâmetro que define se as dags serão acionadas de forma retroativa com base no `start_date`.
  Se `false`, será desabilitado o acionamento das dags retroativas.
- end_date : datetime -> Data em que a DAG não será mais AGENDADA.

*Portanto* : A DAG X começará a ser schedulada a partir do `start_date` e será acionada **depois** de todo `schedule_interval`  

  - Porquê ao pausar e retornar o processo a DAG não executa sozinha? 
    R: Porquê depende do parâmetro `start_date`

**Exemplo**: Para `start_date = 2019-01-01` e `schedule_interval = @daily`, que é todos os dias a meia-noite, temos :

![img.png](../media/schedule_interval_example.png)

Pois a primeira execução (`first_execution`) é sempre o `start_date` + `schedule_interval`. Portanto a primeira execução
será em 2019-01-02.

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
  ti.xcom_pull(key="partner_name", task_ids=["extract"])
  ```
  
  * Através de return_values
  ```commandline

  def ingest() -> dict:
    # TODO : Buisiness logic...
  
    return {'value1' : "teste", 'value2' : 'teste2'}
  
  
  def consume(ti) -> None:
  
    return_value = ti.xcom_pull("return_value",task_ids="ingest") # Se passar em [], o Airflow retornará em lista.
  
    ...
  
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

  **Limitações**

  - Tamanho : As XCOMs são recomendadas para transferir dados com volumetria baixa, sendo seu limite :
    `sqlLite 2GB, Postgres 1GB, MySQL 64kB`
  
  - Podem ser observadas na interface, em Admin -> XCOMs

  - Em termos de _performance_, é melhor passar apenas um objeto do que vários, visto que para cada XCOM é realizada
    uma conexão no banco de dados.

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
      **referencia : https://docs.astronomer.io/learn/task-groups
      
      Melhor forma de organizar as tarefas em grupos na UI do Airflow

      Exemplo :
      ```
      t0 = EmptyOperator(task_id='start')

      # Start task group definition
      with TaskGroup(group_id='group1') as tg1:
          t1 = EmptyOperator(task_id='task1')
          t2 = EmptyOperator(task_id='task2')

          t1 >> t2
      # End task group definition
          
      t3 = EmptyOperator(task_id='end')

      # Set task group's (tg1) dependencies
      t0 >> tg1 >> t3
      ```

      Pode ser utilizada com decorators também, da seguinte forma:
      ```
      1. De forma independente
      @task_group(group_id="tasks")
      def my_independent_tasks():
          task_a()
          task_b()
          task_c()

      2. De forma dependente
      @task_group(group_id="tasks")
      def my_dependent_tasks():
          return task_a(task_b(task_c()))
      ```

- Dynamic tasks
  
  1. Apenas são possíveis se o Airflow entender os parâmetros antecipadamente, ou seja, antes do parsing.
  2. Não é possível criar tarefas dinâmicas a partir do resultado de outras tarefas.
  3. Pode-se criar tarefas dinâmicas a partir de um dicionário, variável ou alguma conexão com o banco de dados.


- Trigger Rules  
  - all_success - triggered if all parents succeded  
  - all_failed - triggered if all parents failed (eg. email notification)  
  - all_done - all of the parents is done, no matter if they failed or succeded  
  - one_failed - as soon as one parent failed  
  - one_success - as soon as one parent success  
  - none_failed - run if no parent task failed or has the status upstream_failed (one of its parents failed)  
  - none_skiped - run if none of the parents were skipped  
  - none_failed_or_skipped - trigger if at lease one one of the parents succeded and all of the parents is done  
  - dummy - your task gets trigger imediatly  

- Branching

  Com base em alguma condição, define qual será as tasks posteriores que o pipeline irá seguir.

  1. Operadores : BranchPythonOperator, BranchSqlOperator, BranchDateTimeOperator, BranchDayOfWeekOperator;
  2. Nesse tipo de operador, sempre deverá ser retornando uma task_id;
  3. Para previnir o status skipped, pode-se utilizar o parâmetro trigger_rule='none_failed_or_skipped';
  4. O operador de Branching **SEMPRE** deverá retornar uma `task_id`, que é onde Workflow irá seguir.


- Dependencies (TODO)
  - [t1, t2, t3] >> t5 - As tarefas t1,t2 e t3 seguirião em paralelo e depois irá acionar a t5.  
  - [t1, t2, t3] >> [t4, t5, t6] - Será lançado um erro. Não se pode tratar dependências entre 2 listas.
    - Cross Dependencies
      - Maneiras de escrever relações de dependência:
      ```commandline
          t1 >> t4
          t2 >> t4
          t3 >> t4
    
          --------
          [t1, t2, t3] >> t4
    
          --------
          from airflow.models.baseoperator import cross_downstream
          cross_downstream([t1, t2, t3], [t4, t5, t6])
            
          --------
          from airflow.models.baseoperator import chain
          chain(x1, [x2,x3], [x4,x5], x6) # Listas devem ter o mesmo tamanho!
          
      ```
      Utilizando a função `cross_downstream`, temos que :
      - t4 depende de t1,t2,t3;
      - t5 depende de t1,t2,t3;
      - t6 depende de t1,t2,t3;  
      
      Vale ressaltar que a função `cross_downstream` não retornada nada, portanto não se deve seguir com
      mais dependências depois dela.

      Utilizando a função `chain`, podemos criar relações um pouco mais complexas, sendo:
      ![img.png](../media/chain-example.png)
      - t2 depende de t1;
      - t3 depende de t1;
      - t4 depende de t2;
      - t5 depende de t3;
      - t6 depende de t4;
      - t6 depende de t5;
      
      Com isso, pode-se juntar diversos padrões de relações para n casos de uso.

  - **Depends on past** 
    ```commandline
        @task.python(depends_on_past=True)    
    ```
    Verifica se a tarefa agendada depende do sucesso da execução de sua última Dag run. Exemplo
    - (1 dag run)  [A fail] -> [B] -> [C]
    - (2 dag run )  [A] -> [B] -> [C]
    - case1: Se A depends_on_past em A => (2)[A] Não será agendada. Ficará sem status

    - A tarefa vai ser excutada se a última tiver com status de `success` ou `skipped`;
    - Sempre interessante definir timeouts nas DAGs;
    - Para a primeira `dag run` e em backfills, esse parâmetro é ignorado;
      Funciona tanto para tarefas agendadadas como acionadas manulamente.
    

  - **Wait for downstream** 
  ```commandline
    @task.python(wait_for_downstream=True) 
  ```
  Basicamente define o seguinte : Execute essa tarefa somente se a mesma tarefa da `dag run` anterior
  tiver tido status de `success` ou `skipped`, **assim como sua tarefa posterior** (apenas a próxima task).
  ![img.png](../media/example-wait-for-downstream.png)
  - (1)  [A] -> [B] -> [C]
  - (2)  [A] -> [B] -> [C ]
  - Se `wait_for_downstream = True`
    - (2)[A] não será acionado se (1)[A] e (1)[B] estiver com status de `succeded` 
  - Sempre que esse parâmetro for atribuído, o depends_on_past será True;


- Pools
  - Define os slots de workers;
  - default_pool tem 128 slots
    - running slots - Ativos
    - queued slots - Aguardando
  - Podem ser criado através da interface do Airflow ;
  - pool_slots - Número de slots que uma tarefa pode ter;
  - Para subdags, apenas um pool_slot será considerado para a subDag inteira

- Configuração 

  Global

    - PARALLELISM = 32 - tarefas sendo executadas em paralelo, a nível global da aplicação;
    - DAG_CONCURRENCY = 16 - Número de tasks que poderão rodar simultâneamente para 1 DAG;
    - MAX_ACTIVE_RUNS_PER_DAG = 16 - Número de dags_runs ativos paralelos para uma mesma DAG.

  Nível DAG

    - concurrency = 2 - Número de tasks rodando simultâneamente para todas as dag_runs
    - max_active_runs = 2 - Número de dags_runs ativos paralelos para uma mesma DAG.

  Nível Task
    
    - task_concurrency = 1 - Apenas 1 tarefas simultânea para todas as dag_runs
    - pool = 'default_pool' - Pool de slots de workers, para se executar as tarefas
      Exemplo: Se existe um pool com dois slots, apenas 2 tasks simultâneas podem acontecer que utilizam esse pool.

- Prioridade de task

  - Nome do parâmetro que define prioridade da task : priority_weight, e é utilizado a nível de task;
  - Quando maior o priority_weight, antes a tarefa será executada;
  - Fazem sentido quando as tarefas estão dentro de um pool, que será definido qual task irá ser executada primeiro;
  - DAGs que são acionadas manualmente não respeitaram o priority_weight
  - O priority_weight padrão é 1;
  - weight_rule (referência : https://towardsdatascience.com/3-steps-to-build-airflow-pipelines-with-efficient-resource-utilisation-b9f399d29fb3)
        - downstream - add up downstream
        - upstream - add up on the upstream
        - absolute - Baseado em cada nível de prioridade informado pelo owner
  - Para priorizar uma DAG sob as outras, pode-se colocar o priority_weight = 99 para todas suas tasks.


- Sensores
  referência : https://docs.astronomer.io/learn/what-is-a-sensor

  Define-se como um operador que espera uma condição ser verdadeira para depois mover para a próxima tarefa

  - Exemplos : FileSensor, DateTimeSensor, SqlSensor

  - Para o DateTimeSensor (espera uma data específica):
    - target_dime - Timedelta, e por ser templated

  - poke_interval - O intervalo que o Airflow irá realizar a verificação se a condição é verdadeira.
  - mode 
    - poke every poke_interval - Irá bloquear um worker slot
    - reschedule - Não irá bloquear um worker slot. Será reagendado. Melhor prática para otimizar recursos.
    - timeout = 7days
      - soft_fail = True - Para quando não atender a condição, a task irá realizar o skipp
      - exponential_backoff=True - Irá aumentar de forma exponencial o período de espera na condição
      - Como boa prática, deve-se sempre definir um timeout.

- Timeouts

  - Podem ser definidos no nível DAG, através do parâmetro dagrun_timeout;
  - Funcionam apenas para DAGs scheduladas, ou seja, que não foram acionadas manualmente;
  - Como boa prática, sempre devem ser definidos

- Controle de falha

  - Nível de DAG
    - on_success_callback(context) - Acionada a função quando DAG retorna status de sucesso;
    - on_failure_callback(context) - Acionada a função quando DAG retorna status de falha. Aqui pode-se enviar notificações, interagir com o board do Jira na parte de incidentes, etc.
    - on_retry_callback(context) - Acionada a funação quando DAG entra em período de retentativa
    - on_sla_miss_callback - Quando a DAG ultrapassa o SLA definido

  - Nível de Task
    Pode-se usar os mesmos parâmetros do nível DAG

  - Funções úteis no controle de falhas:
    ```
    context['exception'] irá retornar a instância da exception (AirflowTaskTimeout,AirflowSensorTimeout,etc..)

    context['ti'].try_number() irá retornar o número da retentativa
    ```

  - retry_delay : timedelta(minutes=5) - Espera 5 minutos para realizar a próxima retentativa;
  - retry_exponential_backoff - Irá esperar mais tempo a cada retentativa. Pode ser útil no consumo de uma API ou Banco de dados, devido a uma carga execessiva.
  - max_retry_delay - Máximo de tempo que o retray_delay pode chegar.
  - `default_task_retries` : configuração global - O parâmtro `retries`   no nível dag e task da override.

  
- SLA
  - É utilizado para verificar se as task foram finalizadas em um certo período de tempo;  
  - Deve ser sempre menor que o timeout, podendo servir como parâmetro a nível de DAG e task no callback : `on_sla_miss_callback`;  
  - Está relacionado com a `execution_date` da DAG;
  - Se não possuir um SLA para DAG, pode-se definir um SLA para última tarefa.


- Versionamento de DAG
  - Novas tarefas irão começar com `no_status`, das tarefas anteriores
  - Para tarefas removidas, todas as anteriores não aparecerão mais
  - Na versão 2.5.0 não há nenhuma mecanismo para realziar o versionamento, porém como boa prática pode-se adotar a anotação : `<dag_name>_0_0_1`
  - 
- DAGs dinâmicas
  - Método de único arquivo:
    - Utilizar um for loop com `globals()<dag_id>`;
    - As Dags serão geradas sem que o Scheduler realizar o parse;
    - Pode resultar em problemas de performance;
    - Não será possível visualizar o código atual da DAG na UI, apenas o código gerador das DAGs dinâmicas
  - Método de vários arquivos (TODO : Ver exemplo)
    - Utiliza arquivos templates
    - É mais produtivo e escalável
    - Uma DAG por arquivo
    - Mais performático
    - Mais trabalhoso na implementação

- Dependência entre DAGs
  - ExternalTaskSensor
    - Como premissa, a DAG deveŕa ter o mesmo `execution_date`
    - Argumentos
        - external_dag_id
        - external_task_id
        - execution_delta - use if the execution_times are different
        - execution_delta_fn - for more compelx cases
        - failed_states - a list of statuses eg. ['failed', 'skipped']
        - alowd_states - eg. ['success']
    - Falhará depois de 7 dias como padrão;
    
  - TriggerDagRunOperator
    - Pode ser uma forma melhor de implementar dependência entre as DAGs
    - arguments
      - trigger_dag_id
      - execution_date (string|timedelta) - eg. "{{ ds }}"
      - wait_for_completion - wait for the triggered dag to finish
          - poke_interval
          - mode is not available!
      - reset_dag_run
          - if you clear the parent without this set to True, the triggered dag will raise an exception
          - you can't trigger a dag with the same execution_date twice without this
          - also can't backfill without this
      - failed_states - use if you wait
      
**observações** XCOM não são removidas automaticamente