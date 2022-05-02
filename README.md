# Airflow Tutorials


## STEP 0. PREREQUISITE 
### Ubuntu OS (20.04.1 LTS)

### Install the airflow
#### Set up python virtual environment 
```
> cd ~
> sudo apt-get update
> sudo apt-get install python3-virtualenv
> sudo apt install python3-venv
> python3 -m venv sandbox
> source sandbox/bin/activate
(sandbox) freepsw.12@airflow:~$
(sandbox) > python -V
Python 3.8.10
(sandbox) > pip install wheel
Collecting wheel
```
- 이후 모든 작업은 python virtual env 환경에서 실행


#### Install a airflow 2.1.1
- Airflow를 pip로 설치할 때, 의존하는 라이브러리의 버전에 따라서 가끔 오류가 발생 가능
- 이를 방지하기 위하여 constraint option을 사용하여 해당 버전에서 사용하는 라이브러리 버전을 지정
    - url로 constraint 파일을 제공
    - https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt
    - (예시) https://raw.githubusercontent.com/apache/airflow/constraints-2.1.1/constraints-3.8.txt
```
(sandbox) > pip install apache-airflow==2.1.0 --constraint constraint.txt
```

### Create the airflow project
- Initialize the metadata database
```
(sandbox) > airflow db init
(sandbox) > ls airflow
airflow.cfg  airflow.db  logs  webserver_config.py
```

### Start Web server
```
## User 생성 
(sandbox) > airflow users create -u admin -p admin -f Park -l SW  -r Admin -e admin@airflow.com

## 
(sandbox) > airflow webserver
  ____________       _____________
 ____    |__( )_________  __/__  /________      __
____  /| |_  /__  ___/_  /_ __  /_  __ \_ | /| / /
___  ___ |  / _  /   _  __/ _  / / /_/ /_ |/ |/ /
 _/_/  |_/_/  /_/    /_/    /_/  \____/____/|__/
[2022-04-28 12:31:59,917] {dagbag.py:487} INFO - Filling up the DagBag from /dev/null
```
- 아래 포트로 브라우저를 통해서 접속한다. 
    - http://34.64.xx.xxx:8080/
    - admin/admin 으로 접속



### 주요 명령어
```
## airflow 버전 업그레이드를 하는 경우 실행
> airflow db upgrade

## 모든 데이터를 초기화 (데이터가 삭제됨. 매우 주의)
> airflow db reset

## 스케줄러를 실행
> airflow scheduler

## 실행중인 dag 목록을 확인
> airflow dags list
airflow dags list
dag_id                                  | filepath                                                 | owner   | paused
========================================+==========================================================+=========+=======
example_bash_operator                   | /home/freepsw.12/sandbox/lib/python3.8/site-packages/air | airflow | True
                                        | flow/example_dags/example_bash_operator.py               |         |
example_branch_datetime_operator_2      | /home/freepsw.12/sandbox/lib/python3.8/site-packages/air | airflow | True
                                        | flow/example_dags/example_branch_datetime_operator.py    |         |
example_xcom_args                       | /home/freepsw.12/sandbox/lib/python3.8/site-packages/air | airflow | True
                                        | flow/example_dags/example_xcomargs.py                    |         |


## 상세 Task 확인 
> airflow tasks list example_xcom_args
generate_value
print_value

```


## STEP 2. Create a data pipeline with airflow
### Create a dag 1 (create_table)
```
> cd ~/airflow
> mkdir dags
> cd dags
> vi user_processing.py

# 1) 모든 입력 변수를 함수에 정의하는 방법
# catchup = :"start_date" 이후 interval 시점마다 실행되지 못한 task를 순서대로 실행한다.
#   이 때, 처음 실행되는 경우라면 start_data 부터 시간 순으로 실행되고,
#   실행 중에 장애가 발생한 상황이었다면, 가장 최근의 interval 시간 부터 실행한다. 
#   이 2가지 차이를 사전에 확인하는 것이 중요!!! 
  with DAG('user_processing', schedule_interval='@daily', 
                              start_date=datetime(2020,1,1), 
                              catchcup=False) as dag:
    creating_table = SqliteOperator(
        task_id='creating_table',
        sqlite_conn_id='db_sqlite',
        sql='''
            CREATE TABLE users (
                firstname TEXT NOT NULL,
                lastname TEXT NOT NULL,
                country TEXT NOT NULL,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                email TEXT NOT NULL PRIMARY KEY
            );
            '''
    )

> cd ~
> airflow webserver
```

#### Run airflow scheduler to apply pipeline in dag
```
> cd ~
> airflow scheduler
```

#### Install provider package (sqlite)
```
> pip install apache-airflow-providers-sqlite

# 현재 설치된 provider 목록 확인 
> airflow providers list
package_name                    | description                                                     | version
================================+=================================================================+========
apache-airflow-providers-ftp    | File Transfer Protocol (FTP) https://tools.ietf.org/html/rfc114 | 1.1.0
apache-airflow-providers-imap   | Internet Message Access Protocol (IMAP)                         | 1.0.1
                                | https://tools.ietf.org/html/rfc3501                             |
apache-airflow-providers-sqlite | SQLite https://www.sqlite.org/                                  | 1.0.2
```

#### Test airflow dags 
- dags 디렉토리에 생성한 pipeline을 실행하기 전에 테스트한다. 
- dag(user_processing) > task(creating_table) 테스트 
```
> airflow tasks test user_processing creating_table 2020-01-01

[2022-04-29 01:56:07,494] {base.py:69} INFO - Using connection to: id: db_sqlite. Host: /home/freepsw.12/airflow/airflow.db, Port: None, Schema: , Login: , Password: None, extra: {}
[2022-04-29 01:56:07,494] {dbapi.py:204} INFO - Running statement:
            CREATE TABLE users (
                firstname TEXT NOT NULL,
                lastname TEXT NOT NULL,
                country TEXT NOT NULL,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                email TEXT NOT NULL PRIMARY KEY
            );
            , parameters: []
[2022-04-29 01:56:07,502] {taskinstance.py:1184} INFO - Marking task as SUCCESS


# sqlite로 실제 생성된 테이블 확인 
> sudo apt install sqlite3
> cd airflow 
> sqlite3 airflow.db

# table 조회
sqlite> .tables

........
dag                            task_reschedule
dag_code                       users  <== 생성된 테이블 확인

sqlite> select * from users;
sqlite>
```

### Create a dag 2 (is_api_available)

```
> cd ~/airflow/dags
> vi user_processing.py

    # Operator 2. Wait until api is available
    is_api_available = HttpSensor(
        task_id='is_api_available',
        http_conn_id='user_api',
        endpoint='api/'
    )
```

#### Install http provider 
- provider 설치 후에 airflow webserver를 재 시작해야 Connection type이 화면에 표시된다. 
```
> pip install apache-airflow-providers-http
```


#### Test Task
```
> cd ~
> airflow tasks test user_processing is_api_available 2020-01-01

[2022-04-29 02:46:06,191] {base.py:69} INFO - Using connection to: id: user_api. Host: https://randomuser.me, Port: None, Schema: , Login: , Password: None, extra: {}
[2022-04-29 02:46:06,192] {http.py:129} INFO - Sending 'GET' to url: https://randomuser.me/api/
[2022-04-29 02:46:06,445] {base.py:243} INFO - Success criteria met. Exiting.
[2022-04-29 02:46:06,449] {taskinstance.py:1184} INFO - Marking task as SUCCESS. dag_id=user_processing, task_id=is_api_available, execution_date=20200101T000000, start_date=20220429T024358, end_date=20220429T024606
```


### Create a Opeartor 3 (extract user info)
```
> cd ~/airflow/dags
> vi user_processing.py

    # Operator 3. Extracting user info
    extracting_user = SimpleHttpOperator(
        task_id='extracting_user',
        http_conn_id='user_api',
        endpoint='api/',
        method='GET',
        response_filter=lambda response: json.loads(response.text),
        log_response=True
    )

> airflow tasks test user_processing extracting_user  2020-01-01

# 아래 결과에 "result" 로 사용자에 대한 상세정보를 확인할 수 있다. 

[2022-04-29 02:53:16,947] {http.py:102} INFO - Calling HTTP method
[2022-04-29 02:53:16,950] {base.py:69} INFO - Using connection to: id: user_api. Host: https://randomuser.me, Port: None, Schema: , Login: , Password: None, extra: {}
[2022-04-29 02:53:16,951] {http.py:129} INFO - Sending 'GET' to url: https://randomuser.me/api/
[2022-04-29 02:53:17,240] {http.py:106} INFO - {"results":[{"gender":"female","name":{"title":"Ms","first":"Afet","last":"Topçuoğlu"},"location":{"street":{"number":7092,"name":"Filistin Cd"},"city":"Çanakkale","state":"Kırklareli","country":"Turkey","postcode":35349,"coordinates":{"latitude":"70.2797","longitude":"174.9225"},"timezone":{"offset":"+5:30","description":"Bombay, Calcutta, Madras, New Delhi"}},"email":"afet.topcuoglu@example.com","login":{"uuid":"0cfbb937-440e-49a5-9be1-a357b67ffbe8","username":"beautifulostrich278","password":"tang","salt":"sb5LOuhT","md5":"3067d7223aae480c07dc27f3aa744ea4","sha1":"2df20fcccfeb571781c4b27669c538c28dc4e22a","sha256":"130da433c87a2e7e948f17386da6daa218879f970bc7e9c7804e3121dc5b6c26"},"dob":{"date":"1964-01-27T07:30:21.109Z","age":58},"registered":{"date":"2010-12-02T08:18:12.655Z","age":12},"phone":"(449)-978-5240","cell":"(260)-901-5402","id":{"name":"","value":null},"picture":{"large":"https://randomuser.me/api/portraits/women/69.jpg","medium":"https://randomuser.me/api/portraits/med/women/69.jpg","thumbnail":"https://randomuser.me/api/portraits/thumb/women/69.jpg"},"nat":"TR"}],"info":{"seed":"f12b92752e709c9b","results":1,"page":1,"version":"1.3"}}
[2022-04-29 02:53:17,253] {taskinstance.py:1184} INFO - Marking task as SUCCESS. dag_id=user_processing, task_id=extracting_user, execution_date=20200101T000000, start_date=20220429T025316, end_date=20220429T025317
```

#### 그럼 "https://randomuser.me/api"는 실제 존재하는 서비스 인가?
- 아마도 강사가 실습용으로 간단한 http server를 구성하여 제공하는 것 같음. 
```
> curl https://randomuser.me/api
{"results":[{"gender":"female","name":{"title":"Miss","first":"Maia","last":"Nordrum"},"location":{"street":{"number":2050,"name":"Verkstedveien"},"city":"Isebakke","state":"Vest-Agder","country":"Norway","postcode":"8026","coordinates":{"latitude":"50.7504","longitude":"17.2224"},"timezone":{"offset":"+9:00","description":"Tokyo, Seoul, Osaka, Sapporo, Yakutsk"}},"email":"maia.nordrum@example.com","login":{"uuid":"995e3e5e-2b4b-4808-9b06-43a2e1883a0a","username":"happyelephant281","password":"55bgates","salt":"TsQGbFZR","md5":"2100c77440ed73bdc9b1fef112bf4a5f","sha1":"78f50d5a38e7f3afa1ef99bd38bdbb64c11a5938","sha256":"a17855bd48abe197e80a87afb0c9d7244aed9ce69ab842586837a0ba182af408"},"dob":{"date":"1978-07-22T00:12:44.347Z","age":44},"registered":{"date":"2004-11-06T10:31:15.642Z","age":18},"phone":"25516067","cell":"49541933","id":{"name":"FN","value":"22077844663"},"picture":{"large":"https://randomuser.me/api/portraits/women/85.jpg","medium":"https://randomuser.me/api/portraits/med/women/85.jpg","thumbnail":"https://randomuser.me/api/portraits/thumb/
```

### Create a Opeartor 4 (extract user info)
```
> cd ~/airflow/dags
> vi user_processing.py

# 'ti'는 task_id의 약자로 airflow에서 task 정보를 추출하기 위해 사용
def _processing_user(ti):
    # 특정 task id의 작업 결과를 조회하는 명령어
    users = ti.xcom_pull(task_ids=['extracting_user'])
    if not len(users) or 'results' not in users[0]:
        raise ValueError("User is empty")
    user = users[0]['results'][0]

    # json_normalize로 json 데이터를 pandas df로 변환
    processed_user = json_normalize({
        'firstname': user['name']['first'],
        'lasttname': user['name']['last'],
        'country': user['location']['country'],
        'username': user['login']['username'],
        'password': user['login']['password'],
        'email': user['email']
    })

    # 위 pandas dataframe 데이터를 csv 파일로 저장한 후, 다음 operator에서 활용
    processed_user.to_csv('/tmp/processed_user.csv', index=None, header=False)


    # Operator 4. Processing user info
    # 위 extracting_user Task의 결과로 저장된 json 파일을 처리해야 한다. 
    processing_user = PythonOperator(
        task_id='processing_user',
        python_callable=_processing_user
    )

    # {"results":[{"gender":"female","name":{"title":"Ms","first":"Afet","last":"Topçuoğlu"},"location":{"street":{"number":7092,"name":"Filistin Cd"},"city":"Çanakkale","state":"Kırklareli","country":"Turkey","postcode":35349,"coordinates":{"latitude":"70.2797","longitude":"174.9225"},"timezone":{"offset":"+5:30","description":"Bombay, Calcutta, Madras, New Delhi"}},"email":"afet.topcuoglu@example.com","login":{"uuid":"0cfbb937-440e-49a5-9be1-a357b67ffbe8","username":"beautifulostrich278","password":"tang","salt":"sb5LOuhT","md5":"3067d7223aae480c07dc27f3aa744ea4","sha1":"2df20fcccfeb571781c4b27669c538c28dc4e22a","sha256":"130da433c87a2e7e948f17386da6daa218879f970bc7e9c7804e3121dc5b6c26"},"dob":{"date":"1964-01-27T07:30:21.109Z","age":58},"registered":{"date":"2010-12-02T08:18:12.655Z","age":12},"phone":"(449)-978-5240","cell":"(260)-901-5402","id":{"name":"","value":null},"picture":{"large":"https://randomuser.me/api/portraits/women/69.jpg","medium":"https://randomuser.me/api/portraits/med/women/69.jpg","thumbnail":"https://randomuser.me/api/portraits/thumb/women/69.jpg"},"nat":"TR"}],"info":{"seed":"f12b92752e709c9b","results":1,"page":1,"version":"1.3"}}


## Test task
> airflow tasks test user_processing processing_user  2020-01-01

[2022-04-29 03:18:10,981] {taskinstance.py:1087} INFO - Executing <Task(PythonOperator): processing_user> on 2020-01-01T00:00:00+00:00
[2022-04-29 03:18:11,023] {taskinstance.py:1280} INFO - Exporting the following env vars:
AIRFLOW_CTX_DAG_OWNER=airflow
AIRFLOW_CTX_DAG_ID=user_processing
AIRFLOW_CTX_TASK_ID=processing_user
AIRFLOW_CTX_EXECUTION_DATE=2020-01-01T00:00:00+00:00
[2022-04-29 03:18:11,032] {python.py:151} INFO - Done. Returned value was: None
[2022-04-29 03:18:11,035] {taskinstance.py:1184} INFO - Marking task as SUCCESS. dag_id=user_processing, task_id=processing_user, execution_date=20200101T000000, start_date=20220429T031631, end_date=20220429T031811

## Check processed file (csv)
> cat /tmp/processed_user.csv
Afet,Topçuoğlu,Turkey,beautifulostrich278,tang,afet.topcuoglu@example.com
```

### Create a Opeartor 5 (Storing data)
```
> cd ~/airflow/dags
> vi user_processing.py

    # Operator 5. Store the processed use info
    # file example 
    # Afet,Topçuoğlu,Turkey,beautifulostrich278,tang,afet.topcuoglu@example.com
    storing_user = BashOperator(
        task_id='storing_user',
        bash_command='echo -e ".separator ","\n.import /tmp/processed_user.csv users" | sqlite3 /home/freepsw.12/airflow/airflow.db'
    )

# Test task
> airflow tasks test user_processing storing_user  2020-01-01

[2022-04-29 03:31:24,657] {subprocess.py:52} INFO - Tmp dir root location:
 /tmp
[2022-04-29 03:31:24,657] {subprocess.py:63} INFO - Running command: ['bash', '-c', 'echo -e ".separator ","\n.import /tmp/processed_user.csv users" | sqlite3 /home/freepsw.12/airflow.db']
[2022-04-29 03:31:24,664] {subprocess.py:75} INFO - Output:
[2022-04-29 03:31:24,667] {subprocess.py:79} INFO - /tmp/processed_user.csv:1: expected 1 columns but found 6 - extras ignored
[2022-04-29 03:31:24,671] {subprocess.py:83} INFO - Command exited with return code 0
[2022-04-29 03:31:24,687] {taskinstance.py:1184} INFO - Marking task as SUCCESS. dag_id=user_processing, task_id=storing_user, execution_date=20200101T000000, start_date=20220429T032930, end_date=20220429T033124

```


#### Create a pipeline with operator 
```
> cd ~/airflow/dags
> vi user_processing.py
    ## 위에서 정의한 operator의 실행 순서를 지정하여 하나의 pipeline으로 구성한다 
    creating_table >> is_api_available >> extracting_user >> processing_user >> storing_user
```

#### check sqlite user table 
```
> cd ~/airflow
> sqlite3 airflow.db

# 현재 데이터가 존재하지 않음. 
sqlite> select * from users;
Nieves|Campos|Spain|blackbear407|fudge|nieves.campos@example.com
```


#### Timezone
- 기본 UTC 시간으로 sheduling이 진행됨. 
- Default Timezone 변경은 airflow.cfg 파일 수정
    - default_ui_timezone = UTC



## STEP 3. Database & Executors
### Scheduling policy 
- 기본 airflow 설정은 모든 task를 순서대로 하나씩 실행한다. (병렬 처리 없음)
- 이를 airflow에서 어떻게 설정했는지 확인해 보면
```
## airflow 가 작업을 처리하고 기록하는 Database가 1개 DB만 바라보고 있음.
## 즉 하나의 작업이 끝나야, 다음 작업이 airflow.db에 작업 과정을 기록할 수 있음. 
> airflow config get-value core sql_alchemy_conn
sqlite:////home/freepsw.12/airflow/airflow.db

## airflow의 executor 실행 정책 (Sequential 정책 적ㅇ용)
> airflow config get-value core executor
SequentialExecutor
```

### Parallel dag 실행을 위한 postgresql 구성
#### Postgresql 설치
```
> sudo apt update
> sudo apt install postgresql

## postgresql 접속
> sudo -u postgres psql
psql (12.9 (Ubuntu 12.9-0ubuntu0.20.04.1))
Type "help" for help.

## 패스워드 변경
postgres=# ALTER USER postgres PASSWORD 'postgres';
ALTER ROLE
```

#### Airflow 용 postgresl package 설치 
```
> pip install 'apache-airflow[postgres]'
```

#### Airflow config 변경 
```
> vi ~/airflow/airflow.cfg 
## 1) Executor 변경 
# executor = SequentialExecutor
executor = LocalExecutor

## 2) DB 변경
## 기존 airflow.db를 주석 처리
# sql_alchemy_conn = sqlite:////home/freepsw.12/airflow/airflow.db

## 새로 설치한 postgresql 에 연결 (id:password@localhost/db_name)
sql_alchemy_conn = postgresql+psycopg2://postgres:postgres@localhost/postgres

```
#### 변경된 DB에 접근 가능한지 테스트 
```
> airflow db check
[2022-04-29 07:08:39,319] {db.py:776} INFO - Connection successful.
```

### Airflow 재시작 
- 기존 airflow webserver와 scheduler 중지
```
> cd ~

## DB를 초기화 한다. 
> airflow db init

## User 생성 
> airflow users create -u admin -p admin -f Park -l SW  -r Admin -e admin@airflow.com
Admin user admin created

## Start airflow web server
> airflow webserver

## Start airflow scheduler 
> airflow scheduler
```


## STEP 4. Celery Executor

```
## 1.  현재 airflow 버전에 맞는 celery 패키지 설치
### Airflow 2.1.0 doesn't support Celery 5.
> pip install --upgrade apache-airflow-providers-celery==2.0.0

## 2. redis server 설치 
> sudo apt install redis-server

## 3. redis server가 자동 재시작 하도록 설정 변경
> sudo vi /etc/redis/redis.conf

#supervised no
supervised systemd

## 4. Redis server가 정상 실행 중인지 확인 
> sudo systemctl restart redis.service

> sudo systemctl status redis.service
● redis-server.service - Advanced key-value store
     Loaded: loaded (/lib/systemd/system/redis-server.service; enabled; vendor preset: enabled)
     Active: active (running) since Fri 2022-04-29 07:44:04 UTC; 8s ago


## 5. airflow 환경설정 변경  
> cd ~
> vi airflow/airflow.cfg 

## Executor 변경 
# executor = SequentialExecutor
# executor = LocalExecutor
executor = CeleryExecutor

## Celery에서 Task를 가져올 때 사용하는 redis서버 IP를 localhost로 변경 
# broker_url = redis://redis:6379/0
broker_url = redis://localhost:6379/0

## Celery Worker의 작업결과를 저장할 DB 정보를 변경
## 사전에 설치했던 postgresql 정보를 활용
# result_backend = db+postgresql://postgres:airflow@postgres/airflow
result_backend = db+postgresql://postgres:postgres@localhost/postgres

## 6. Airflow용 redis 패키지 설치 
> pip install 'apache-airflow[redis]==2.1.0'
```

### Start celery flower
- Celery worker 상태를 모니터링 할 수 있는 웹서버
- https://docs.celeryq.dev/en/latest/userguide/monitoring.html#flower-real-time-celery-web-monitor
```
> airflow celery flower
[2022-04-29 07:57:01,043] {command.py:135} INFO - Visit me at http://0.0.0.0:5555
[2022-04-29 07:57:01,056] {command.py:142} INFO - Broker: redis://localhost:6379/0
```
- http://IP:5555로 브라우저로 접속


### Add celery worker to celery cluster 
- 현재 서버를 celery cluster의 worker로 등록한다. 
- 아래 명령어 실행 후 http://IP:5555 로 접속하면 worker가 등록된 것이 보인다. 
```
> airflow celery worker

[2022-04-29 08:04:43,247: INFO/MainProcess] Connected to redis://localhost:6379/0
[2022-04-29 08:04:43,255: INFO/MainProcess] mingle: searching for neighbors
[2022-04-29 08:04:44,274: INFO/MainProcess] mingle: all alone
[2022-04-29 08:04:44,285: INFO/MainProcess] celery@airflow ready.
[2022-04-29 08:04:46,068: INFO/MainProcess] Events of group {task} enabled by remote.
```


### Restart airflow 
- flower와 celery worker 중지
- CTRL + C 입력
```
> airflow webserver
> airflow scheduler
```

### Executor를 LocalExecutor로 변경
```
> cd ~
> vi airflow/airflow.cfg
```


## STEP 5. Advanced Concepts 
### SubDAGs 활용 
- 유사한 task들을 하나의 Task로 통합하여 관리하는 모듈 

```
## Airflow web ui에 있는 샘플 DAG를 삭제한 후 실습
> vi ~/airflow/airflow.cfg 

load_examples = False # 로딩하지 않음으로 변경.
```

#### Restart Airflow 
- webserve와 scheduler 중지 후 다시 시작.
```
> airflow webserver
> airflow scheduler
```


## STEP 6. Creating a airflow plugins with elasticsearch and postgreSQL
- 모든 작업은 python virtual env 환경에서 실행
### Install Elasticsearch
```
> curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -

> echo "deb https://artifacts.elastic.co/packages/7.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-7.x.list

> sudo apt update && sudo apt install elasticsearch

> sudo systemctl start elasticsearch
> curl -X GET 'http://localhost:9200'
{
  "name" : "airflow",
  "cluster_name" : "elasticsearch",
  "cluster_uuid" : "Z8NAXe_3Scaulqg9jB3FpA",
  "version" : {
    "number" : "7.17.3",
    "build_flavor" : "default",
    "build_type" : "deb",
    "build_hash" : "5ad023604c8d7416c9eb6c0eadb62b14e766caff",
    "build_date" : "2022-04-19T08:11:19.070913226Z",
    "build_snapshot" : false,
    "lucene_version" : "8.11.1",
    "minimum_wire_compatibility_version" : "6.8.0",
    "minimum_index_compatibility_version" : "6.0.0-beta1"
  },
  "tagline" : "You Know, for Search"
}
```

### Create Hook for elasticsearch
```
> mkdir -p ~/airflow/plugins/elasticsearch_plugin/hooks

> tree airflow
├── plugins
│   └── elasticsearch_plugin
│       └── hooks
│

> cd  ~/airflow/plugins/elasticsearch_plugin/hooks

> vi elastic_hook.py
```

```python
from airflow.hooks.base import BaseHook

from elasticsearch import Elasticsearch

class ElasticHook(BaseHook):
    # 아직 conn_id인 "elasticsearch_default"는 생성하지 않았음
    def __init__(self, conn_id='elasticsearch_default', *args, **kwards):
        super().__init__(*args, **kwards)
        conn = self.get_connection(conn_id)

        conn_config = {}
        hosts = []

        if conn.host:
            hosts = conn.host.split(',')
        if conn.port:
            conn_config['port'] = int(conn.port)
        if conn.login:
            conn_config['http_auth'] = (conn.login, conn.password)


        self.es = Elasticsearch(hosts, **conn_config)
        self.index = conn.schema

    # elasticsearch에 대한 정보를 전달
    def info(self):
        return self.es.info()

    # 데이터를 저장할 index 지정
    def set_index(self, index):
        self.index = index 
    
    # 데이터를 es에 저장
    def add_doc(self, index, doc_type, doc):
        self.set_index(index)
        res = self.es.index(index=index, doc_type=doc_type, doc=doc)
        return res
```

#### Hook이 정상적으로 구성되었는지 확인  
- airflow 재시작
```
> airflow webserver
> airflow scheduler
```



### STEP 7. Creating Operator for postgres and elasticsearch 
- postgres의 connection 테이블 정보를 조회하여
- elasticsearch connection index에 저장하는 Operator를 생성한다. 
```
> cd airflow
> tree .
dags/
└── elasticsearch_dag.py           # <-- DAG 파일 생성
plugins/
└── elasticsearch_plugin
    ├── hooks
    │   └── elastic_hook.py        # <-- Hook 파일 생성 
    └── operators
        └── postgres_to_elastic.py # <-- Operator 파일 생성 
```
```

#### Airflow Web UI에서 postgreSQL connection 생성
- id : postgres, password : postgres 로 사용자 생성 

#### Postgres 사용자 패스워드 변경 
```
> sudo -u postgres psql

postgres=# ALTER USER postgres PASSWORD 'posgtres';

# 현재 connection 정보 확인 
postgres=# select * from connection where conn_id='postgres_default';

 id |     conn_id      | conn_type |   host    | schema |  login   | password | port |            extra            | is_encrypted | is_extra_encrypted | description
----+------------------+-----------+-----------+--------+----------+----------+------+-----------------------------+--------------+--------------------+-------------
 50 | postgres_default | postgres  | localhsot |        | postgres | postgres | 5432 | {"cursor":"realdictcursor"} | f            | f                  |
(1 row)elp" for help.
```


#### Elasticsearch의 connection index 데이터 확인
- 아직 dag가 실행되지 않아서 connection index에 데이터가 없음.
```
> curl -X GET "http://localhost:9200/connections/_search" -H "Content-type: application/json" -d '{"query":{"match_all":{}}}'

{"error":{"root_cause":[{"type":"index_not_found_exception","reason":"no such index [connections]","resource.type":"index_or_alias","resource.id":"connections","index_uuid":"_na_","index":"connections"}],"type":"index_not_found_exception","reason":"no such index [connections]","resource.type":"index_or_alias","resource.id":"connections","index_uuid":"_na_","index":"connections"},"status":404}
```

#### 생성한 Operator를 실행하는 Dag 생성 
- PostgresToElasticOperator를 task로 실행한다. 
```
> vi airflow/dags/elasticsearch_dag.py
```
- 
- elasticsearch_dag.py
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from elasticsearch_plugin.hooks.elastic_hook import ElasticHook
from elasticsearch_plugin.operators.postgres_to_elastic import PostgresToElasticOperator
from datetime import datetime

default_args = {
    'start_date': datetime(2020, 1, 1)
}

def __print_es_info():
    hook = ElasticHook()
    print(hook.info())

with DAG('elasticsearch_dag', schedule_interval='@daily', 
                     default_args=default_args, 
                     catchup=False) as dag:
    print_es_info = PythonOperator(
        task_id='print_es_info',
        python_callable=__print_es_info
    )

    connections_to_es = PostgresToElasticOperator(
        task_id='connections_to_es',
        sql='SELECT * FROM connection',
        index='connections'
    )

    print_es_info >> connections_to_es
```


#### Elasticsearch의 connection index 데이터 확인
- 위의 dag가 실행 된 후,
- 정상적으로 데이터가 저장됨을 확인
```
> curl -X GET "http://localhost:9200/connections/_search" -H "Content-type: application/json" -d '{"query":{"match_all":{}}}'
{"took":13,"timed_out":false,"_shards":{"total":1,"successful":1,"skipped":0,"failed":0},"hits":{"total":{"value":49,"relation":"eq"},"max_score":1.0,"hits":[{"_index":"connections","_type":"external","_id":"gv_RfYABRq_8jBAUzmeW","_score":1.0,"_source":{
  "id": 1,
  "conn_id": "airflow_db",
  "conn_type": "mysql",
  "host": "mysql",
  "schema": "airflow",
  "login": "root",
  "password": null,
  "port": null,
  "extra": null,
  "is_encrypted": false,
  "is_extra_encrypted": false,
  "description": null
}},{"_index":"connections","_type":"external","_id":"g__RfYABRq_8jBAUzmfu","_score":1.0,"_source":{
```


### STEP 8. Running the airflow on docker.
#### Running airflow on docker with the Celery Executor 

```
> cd ./01.setup/docker/airflow-local
> wget https://airflow.apache.org/docs/apache-airflow/stable/docker-compose.yaml
> mv docker-compose.yaml docker-compose-celery.yaml 
```

- docker-compose.yaml 
```yaml
---
version: '3'
x-airflow-common:
  &airflow-common
  # Comment the image line, place your Dockerfile in the directory where you placed the docker-compose.yaml
  # and uncomment the "build" line below, Then run `docker-compose build` to build the images.
  image: ${AIRFLOW_IMAGE_NAME:-apache/airflow:2.3.0}
  # build: .
  environment:
    &airflow-common-env
    AIRFLOW__CORE__EXECUTOR: CeleryExecutor
    AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
    # For backward compatibility, with Airflow <2.3
    AIRFLOW__CORE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
    AIRFLOW__CELERY__RESULT_BACKEND: db+postgresql://airflow:airflow@postgres/airflow
    AIRFLOW__CELERY__BROKER_URL: redis://:@redis:6379/0
    AIRFLOW__CORE__FERNET_KEY: ''
    AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: 'true'
    AIRFLOW__CORE__LOAD_EXAMPLES: 'true'
    AIRFLOW__API__AUTH_BACKENDS: 'airflow.api.auth.backend.basic_auth'
    _PIP_ADDITIONAL_REQUIREMENTS: ${_PIP_ADDITIONAL_REQUIREMENTS:-}
  volumes: #현재 directory에 아래 디렉토리를 생성하면, docker에서 해당 파일을 인식함.
    - ./dags:/opt/airflow/dags #사용자가 정의한 dag 파일 경로. 
    - ./logs:/opt/airflow/logs
    - ./plugins:/opt/airflow/plugins
  user: "${AIRFLOW_UID:-50000}:0"
  depends_on:
    &airflow-common-depends-on
    redis:
      condition: service_healthy
    postgres:
      condition: service_healthy

services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    volumes:
      - postgres-db-volume:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]
      interval: 5s
      retries: 5
    restart: always

  redis:
    image: redis:latest
    expose:
      - 6379
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 30s
      retries: 50
    restart: always

  airflow-webserver:
    <<: *airflow-common
    command: webserver
    ports:
      - 8080:8080
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:8080/health"]
      interval: 10s
      timeout: 10s
      retries: 5
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  airflow-scheduler:
    <<: *airflow-common
    command: scheduler
    healthcheck:
      test: ["CMD-SHELL", 'airflow jobs check --job-type SchedulerJob --hostname "$${HOSTNAME}"']
      interval: 10s
      timeout: 10s
      retries: 5
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  airflow-worker:
    <<: *airflow-common
    command: celery worker
    healthcheck:
      test:
        - "CMD-SHELL"
        - 'celery --app airflow.executors.celery_executor.app inspect ping -d "celery@$${HOSTNAME}"'
      interval: 10s
      timeout: 10s
      retries: 5
    environment:
      <<: *airflow-common-env
      # Required to handle warm shutdown of the celery workers properly
      # See https://airflow.apache.org/docs/docker-stack/entrypoint.html#signal-propagation
      DUMB_INIT_SETSID: "0"
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  airflow-triggerer:
    <<: *airflow-common
    command: triggerer
    healthcheck:
      test: ["CMD-SHELL", 'airflow jobs check --job-type TriggererJob --hostname "$${HOSTNAME}"']
      interval: 10s
      timeout: 10s
      retries: 5
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  airflow-init:
    <<: *airflow-common
    entrypoint: /bin/bash
    # yamllint disable rule:line-length
    command:
      - -c
      - |
        function ver() {
          printf "%04d%04d%04d%04d" $${1//./ }
        }
        airflow_version=$$(gosu airflow airflow version)
        airflow_version_comparable=$$(ver $${airflow_version})
        min_airflow_version=2.2.0
        min_airflow_version_comparable=$$(ver $${min_airflow_version})
        if (( airflow_version_comparable < min_airflow_version_comparable )); then
          echo
          echo -e "\033[1;31mERROR!!!: Too old Airflow version $${airflow_version}!\e[0m"
          echo "The minimum Airflow version supported: $${min_airflow_version}. Only use this or higher!"
          echo
          exit 1
        fi
        if [[ -z "${AIRFLOW_UID}" ]]; then
          echo
          echo -e "\033[1;33mWARNING!!!: AIRFLOW_UID not set!\e[0m"
          echo "If you are on Linux, you SHOULD follow the instructions below to set "
          echo "AIRFLOW_UID environment variable, otherwise files will be owned by root."
          echo "For other operating systems you can get rid of the warning with manually created .env file:"
          echo "    See: https://airflow.apache.org/docs/apache-airflow/stable/start/docker.html#setting-the-right-airflow-user"
          echo
        fi
        one_meg=1048576
        mem_available=$$(($$(getconf _PHYS_PAGES) * $$(getconf PAGE_SIZE) / one_meg))
        cpus_available=$$(grep -cE 'cpu[0-9]+' /proc/stat)
        disk_available=$$(df / | tail -1 | awk '{print $$4}')
        warning_resources="false"
        if (( mem_available < 4000 )) ; then
          echo
          echo -e "\033[1;33mWARNING!!!: Not enough memory available for Docker.\e[0m"
          echo "At least 4GB of memory required. You have $$(numfmt --to iec $$((mem_available * one_meg)))"
          echo
          warning_resources="true"
        fi
        if (( cpus_available < 2 )); then
          echo
          echo -e "\033[1;33mWARNING!!!: Not enough CPUS available for Docker.\e[0m"
          echo "At least 2 CPUs recommended. You have $${cpus_available}"
          echo
          warning_resources="true"
        fi
        if (( disk_available < one_meg * 10 )); then
          echo
          echo -e "\033[1;33mWARNING!!!: Not enough Disk space available for Docker.\e[0m"
          echo "At least 10 GBs recommended. You have $$(numfmt --to iec $$((disk_available * 1024 )))"
          echo
          warning_resources="true"
        fi
        if [[ $${warning_resources} == "true" ]]; then
          echo
          echo -e "\033[1;33mWARNING!!!: You have not enough resources to run Airflow (see above)!\e[0m"
          echo "Please follow the instructions to increase amount of resources available:"
          echo "   https://airflow.apache.org/docs/apache-airflow/stable/start/docker.html#before-you-begin"
          echo
        fi
        mkdir -p /sources/logs /sources/dags /sources/plugins
        chown -R "${AIRFLOW_UID}:0" /sources/{logs,dags,plugins}
        exec /entrypoint airflow version
    # yamllint enable rule:line-length
    environment:
      <<: *airflow-common-env
      _AIRFLOW_DB_UPGRADE: 'true'
      _AIRFLOW_WWW_USER_CREATE: 'true'
      _AIRFLOW_WWW_USER_USERNAME: ${_AIRFLOW_WWW_USER_USERNAME:-airflow}
      _AIRFLOW_WWW_USER_PASSWORD: ${_AIRFLOW_WWW_USER_PASSWORD:-airflow}
    user: "0:0"
    volumes:
      - .:/sources

  airflow-cli:
    <<: *airflow-common
    profiles:
      - debug
    environment:
      <<: *airflow-common-env
      CONNECTION_CHECK_MAX_COUNT: "0"
    # Workaround for entrypoint issue. See: https://github.com/apache/airflow/issues/16252
    command:
      - bash
      - -c
      - airflow

  flower:
    <<: *airflow-common
    command: celery flower
    ports:
      - 5555:5555
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:5555/"]
      interval: 10s
      timeout: 10s
      retries: 5
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

volumes:
  postgres-db-volume:

```

- run docker compose 
```
> cd ./01.setup/docker/airflow-local
> docker-compose -f docker-compose-celery.yaml up
```
- localhost:8080 접속 (airflow / airflow 로 접속)



#### Running airflow on docker with the Local Executor 

```yaml 
x-airflow-common:
  &airflow-common
  image: ${AIRFLOW_IMAGE_NAME:-apache/airflow:2.3.0}
  environment:
    &airflow-common-env
    AIRFLOW__CORE__EXECUTOR: LocalExecutor
    AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
    # For backward compatibility, with Airflow <2.3
    AIRFLOW__CORE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
    # AIRFLOW__CELERY__RESULT_BACKEND: db+postgresql://airflow:airflow@postgres/airflow
    # AIRFLOW__CELERY__BROKER_URL: redis://:@redis:6379/0
  depends_on:
    &airflow-common-depends-on
    # redis를 사용하지 않으므로 주석 처리
    # redis:
    #   condition: service_healthy
    postgres:
      condition: service_healthy


# LocalExecutor는 redis를 사용하지 않음. 
#   redis:
#     image: redis:latest
#     expose:
#       - 6379
#     healthcheck:
#       test: ["CMD", "redis-cli", "ping"]
#       interval: 5s
#       timeout: 30s
#       retries: 50
#     restart: always


# LocalExecutor는 worker celery worker를 실행하지 않음
#   airflow-worker:
#     <<: *airflow-common
#     command: celery worker
#     healthcheck:
#       test:
#         - "CMD-SHELL"
#         - 'celery --app airflow.executors.celery_executor.app inspect ping -d "celery@$${HOSTNAME}"'
#       interval: 10s
#       timeout: 10s
#       retries: 5
#     environment:
#       <<: *airflow-common-env
#       # Required to handle warm shutdown of the celery workers properly
#       # See https://airflow.apache.org/docs/docker-stack/entrypoint.html#signal-propagation
#       DUMB_INIT_SETSID: "0"
#     restart: always
#     depends_on:
#       <<: *airflow-common-depends-on
#       airflow-init:
#         condition: service_completed_successfully


# Celery flower도 사용하지 않음 
#   flower:
#     <<: *airflow-common
#     command: celery flower
#     ports:
#       - 5555:5555
#     healthcheck:
#       test: ["CMD", "curl", "--fail", "http://localhost:5555/"]
#       interval: 10s
#       timeout: 10s
#       retries: 5
#     restart: always
#     depends_on:
#       <<: *airflow-common-depends-on
#       airflow-init:
#         condition: service_completed_successfully
```

- run the airflow with local executor
```
> cd ./01.setup/docker/airflow-local
> docker-compose -f docker-compose-local.yaml up

> docker ps
CONTAINER ID   IMAGE                  COMMAND                  CREATED         STATUS                   PORTS                              NAMES
eb82ca7754c2   apache/airflow:2.3.0   "/usr/bin/dumb-init …"   5 minutes ago   Up 5 minutes (healthy)   0.0.0.0:8080->8080/tcp             airflow-local_airflow-webserver_1
a9e29d41fe65   apache/airflow:2.3.0   "/usr/bin/dumb-init …"   5 minutes ago   Up 5 minutes (healthy)   8080/tcp                           airflow-local_airflow-triggerer_1
8b622f84bc6f   apache/airflow:2.3.0   "/usr/bin/dumb-init …"   5 minutes ago   Up 5 minutes (healthy)   8080/tcp                           airflow-local_airflow-worker_1
4ed072aa467f   apache/airflow:2.3.0   "/usr/bin/dumb-init …"   5 minutes ago   Up 5 minutes (healthy)   8080/tcp                           airflow-local_airflow-scheduler_1
20412cf73f3b   apache/airflow:2.3.0   "/usr/bin/dumb-init …"   5 minutes ago   Up 5 minutes (healthy)   0.0.0.0:5555->5555/tcp, 8080/tcp   airflow-local_flower_1
865859fe3213   redis:latest           "docker-entrypoint.s…"   6 minutes ago   Up 6 minutes (healthy)   6379/tcp                           airflow-local_redis_1
64c483b575ae   postgres:13            "docker-entrypoint.s…"   6 minutes ago   Up 6 minutes (healthy)   5432/tcp                           airflow-local_postgres_1
```