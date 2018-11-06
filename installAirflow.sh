#! /bin/bash

export AIRFLOW_HOME=/data1/recommend/airflow
export SLUGIFY_USES_TEXT_UNIDECODE=yes

# 安装mysql客户端
if [ -e '/usr/bin/apt-get' ]; then
    sudo apt-get install libmysqlclient-dev
elif [ -e '/usr/bin/yum' ]; then    
    sudo yum install -y mysql-devel
fi
pip install --upgrade pip

# 检测当前airflow的版本，根据版本特殊处理
v=`pip search apache-airflow | grep '^apache-airflow' | awk -F' ' '{print $2}'`
if [ "$v" = "(1.10.0)" ]; then
    pip install flask-appbuilder==1.11.1
fi


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
a='\\\/'
pyp=$(echo "$py" | sed "s/\//$a/g")
sed "s/\#\!.*/#!$pyp/" ramoi.py > bin/ramoi.py
chmod a+x bin/ramoi.py

# 对于1.10版本，打patch，增加webserver对时区的支持，修复cpu占用过高的bug
if [ "$v" = "(1.10.0)" ]; then
    patch -p0 < 1.10.0.patch
fi
