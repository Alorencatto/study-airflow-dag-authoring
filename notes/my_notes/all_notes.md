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

As variáveis no Airflow, são definidas em um modelo chave -> valor, possuindo também uma descrição.Estas são armazendas no banco de metadados da aplicação, podendo ser usadas globalmente, através do package `airflow.models`, com a classe `Variable`.

- Criando variáveis
  - UI  
    Airflow UI -> Admin -> Variables -> add new record