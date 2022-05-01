from airflow.models import DAG
from airflow.providers.sqlite.operators.sqlite import SqliteOperator
from airflow.providers.http.sensors.http import HttpSensor
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

from datetime import datetime
import json
from pandas import json_normalize


default_args = {
    'start_date': datetime(2020,1,1)
}

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


# 1) 모든 입력 변수를 함수에 정의하는 방법
# with DAG('user_processing', schedule_interval='@daily', 
#                             start_date=datetime(2020,1,1), 
#                             catchcup=False) as dag:

# 2) defalut_args라는 변수에 공통으로 사용하는 입력 변수를 정의하는 방법
with DAG('user_processing', schedule_interval='@daily', 
                            default_args=default_args, 
                            catchup=False) as dag:
    # Operator 1. Creating table
    creating_table = SqliteOperator(
        task_id='creating_table',
        sqlite_conn_id='db_sqlite',
        sql='''
            CREATE TABLE IF NOT EXISTS users (
                firstname TEXT NOT NULL,
                lastname TEXT NOT NULL,
                country TEXT NOT NULL,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                email TEXT NOT NULL PRIMARY KEY
            );
            '''
    )

    # Operator 2. Wait until api is available
    is_api_available = HttpSensor(
        task_id='is_api_available',
        http_conn_id='user_api',
        endpoint='api/'
    )

    # Operator 3. Extracting user info
    extracting_user = SimpleHttpOperator(
        task_id='extracting_user',
        http_conn_id='user_api',
        endpoint='api/',
        method='GET',
        response_filter=lambda response: json.loads(response.text),
        log_response=True
    )

    # Operator 4. Processing user info
    # 위 extracting_user Task의 결과로 저장된 json 파일을 처리해야 한다. 
    # {"results":[{"gender":"female","name":{"title":"Ms","first":"Afet","last":"Topçuoğlu"},"location":{"street":{"number":7092,"name":"Filistin Cd"},"city":"Çanakkale","state":"Kırklareli","country":"Turkey","postcode":35349,"coordinates":{"latitude":"70.2797","longitude":"174.9225"},"timezone":{"offset":"+5:30","description":"Bombay, Calcutta, Madras, New Delhi"}},"email":"afet.topcuoglu@example.com","login":{"uuid":"0cfbb937-440e-49a5-9be1-a357b67ffbe8","username":"beautifulostrich278","password":"tang","salt":"sb5LOuhT","md5":"3067d7223aae480c07dc27f3aa744ea4","sha1":"2df20fcccfeb571781c4b27669c538c28dc4e22a","sha256":"130da433c87a2e7e948f17386da6daa218879f970bc7e9c7804e3121dc5b6c26"},"dob":{"date":"1964-01-27T07:30:21.109Z","age":58},"registered":{"date":"2010-12-02T08:18:12.655Z","age":12},"phone":"(449)-978-5240","cell":"(260)-901-5402","id":{"name":"","value":null},"picture":{"large":"https://randomuser.me/api/portraits/women/69.jpg","medium":"https://randomuser.me/api/portraits/med/women/69.jpg","thumbnail":"https://randomuser.me/api/portraits/thumb/women/69.jpg"},"nat":"TR"}],"info":{"seed":"f12b92752e709c9b","results":1,"page":1,"version":"1.3"}}
    processing_user = PythonOperator(
        task_id='processing_user',
        python_callable=_processing_user
    )


    # Operator 5. Store the processed use info
    # file example 
    # Afet,Topçuoğlu,Turkey,beautifulostrich278,tang,afet.topcuoglu@example.com
    storing_user = BashOperator(
        task_id='storing_user',
        bash_command='echo -e ".separator ","\n.import /tmp/processed_user.csv users" | sqlite3 /home/freepsw.12/airflow/airflow.db'
    )

    ## 위에서 정의한 operator의 실행 순서를 지정하여 하나의 pipeline으로 구성한다 
    creating_table >> is_api_available >> extracting_user >> processing_user >> storing_user

