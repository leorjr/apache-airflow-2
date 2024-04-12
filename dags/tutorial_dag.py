from datetime import datetime
import requests
import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.bash import BashOperator

def consumir_api_pokemons():
    url = 'https://pokeapi.co/api/v2/pokemon'
    data = []

    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()['results']
    else:
        print(f"Erro na requisição: {response.status_code}")
        
    return data

def transformar_dados_em_dataframe(ti):
    data = ti.xcom_pull(task_ids='consumir_api_pokemons')
    df = pd.DataFrame(data)
    return df

def obtem_quantidade_pokemons(ti):
    df = ti.xcom_pull(task_ids='transformar_dados_em_dataframe')
    qtd = len(df.index)
    return qtd

def verifica_quantidade_minima_valida_pokemons(ti):
    qtd = ti.xcom_pull(task_ids='obtem_quantidade_pokemons')
    return 'valido' if qtd >= 20 else 'nvalido'

with DAG(
    'tutorial_dag', 
    start_date=datetime(2024, 4, 11), 
    schedule_interval='30 * * * *', 
    catchup=False
) as dag:
    
    t1 = PythonOperator(
        task_id='consumir_api_pokemons', 
        python_callable=consumir_api_pokemons
    )

    t2 = PythonOperator(
        task_id='transformar_dados_em_dataframe', 
        python_callable=transformar_dados_em_dataframe
    )

    t3 = PythonOperator(
        task_id='obtem_quantidade_pokemons', 
        python_callable=obtem_quantidade_pokemons
    )

    t4 = BranchPythonOperator(
        task_id='verifica_quantidade_minima_valida_pokemons', 
        python_callable=verifica_quantidade_minima_valida_pokemons
    )

    valido = BashOperator(
        task_id='valido', 
        bash_command='echo "Quantidade Ok!"'
    )

    nvalido = BashOperator(
        task_id='nvalido', 
        bash_command='echo "Quantidade não Ok!"'
    )

    t1 >> t2 >> t3 >> t4 >> [valido, nvalido]