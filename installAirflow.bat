rem set AIRFLOW_HOME=/data1/recommend/airflow
set SLUGIFY_USES_TEXT_UNIDECODE=yes
set V110=no
pip install --upgrade pip

rem 检测当前airflow的版本，根据版本特殊处理
pip search apache-airflow|findstr "apache-airflow"|findstr "1.10.0"
IF %ERRORLEVEL% EQU 0 (
    set V110=yes
    pip install flask-appbuilder==1.11.1
)

pip install apache-airflow
pip install apache-airflow[ssh]
pip install apache-airflow[async]
pip install apache-airflow[celery]
pip install apache-airflow[devel]
pip install apache-airflow[hdfs]
pip install apache-airflow[hive]
pip install apache-airflow[ldap]
pip install apache-airflow[mysql]
pip install apache-airflow[redis]
pip install kazoo


rem 对于1.10版本，打patch，增加webserver对时区的支持，修复cpu占用过高的bug
IF %V110% EQU yes (
    patch  -d %USERPROFILE%\Envs\airflow -p0 < 1.10.0-win.patch
)
