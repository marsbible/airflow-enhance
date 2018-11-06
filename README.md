1. 确认当前目录是/data1/recommend/airflow，如果不是，需要手动修改airflow.cfg和supervisor/airflow.conf等配置文件
2. 确保使用的是python3.6的虚拟环境并且已经激活，
   python3.6 -m venv airflow && source bin/activate
3. 设置AIRFLOW_HOME=/data1/recommend/airflow
   配置好redis和mysql数据库，修改airflow.cfg里的相关连接配置。
   对于全新安装的系统执行airflow initdb执行数据库初始化操作，对于版本升级执行airflow upgradedb 
   在初始化和升级数据库阶段，确保你拥有对数据库的全部操作权限，mysql必须配置explicit_defaults_for_timestamp=true
4. 默认配置没有启用用户认证，生产环境建议开启ldap认证，需要[ldap]里配置认证信息，同时开启[webserver]里的authenticate
5. 执行./installAirflow.sh
6. 如果希望直接在airflow目录下运行业务程序，可以执行./installRuntime.sh 
7. 生产环境将supervisor/airflow.conf添加到supervisord的配置中，默认放到/etc/supervisord.d目录
   同时修改airflow.cfg中ramoi.py相关的参数，包括zk地址和服务名称，确保同一集群的scheduler参数相同，不同集群的不同
