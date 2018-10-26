export AIRFLOW_HOME=/data1/recommend/airflow
export SLUGIFY_USES_TEXT_UNIDECODE=yes
pip install --upgrade pip

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

# 安装ramoi程序，用来支持scheduler做ha
py=`which python`
pyp=${py//\//\\\/}
sed "s/\#\!.*/#!$pyp/" ramoi.py > bin/ramoi.py
chmod a+x bin/ramoi.py

v110=`grep '1.10.0'  lib/python3.6/site-packages/airflow/version.py`

# 对于1.10版本，打patch，增加webserver对时区的支持，修复cpu占用过高的bug
if [[ ! -z "$v110" ]];then
    patch -p0 < 1.10.0.patch
fi
