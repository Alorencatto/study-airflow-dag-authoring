#

- start_date : datetime -> Data na qual a tarefa começa a ser schedulada  
- schedule_interval : datetime -> Intervalo entre o valor mínimo do start_date + o valor do intervalo, no qual a dag será acionada.  
- catchup : bool -> Parâmetro que define se as dags serão acionadas de forma retroativa com base no `start_date`.
  Se `false`, será desabilitado o acionamento das dags retroativas.

*Portanto* : A DAG X começará a ser schedulada a partir do `start_date` e será acionada **depois** de todo `schedule_interval`  

Exemplo : 

  - Porquê ao pausar e retornar o processo a DAG não executa sozinha?