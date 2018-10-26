1. 确保当前目录是/data1/recommend/airflow，如果不是，需要手动修改airflow.cfg和supervisor/airflow.conf等配置文件
2. 配置好redis和mysql数据库，修改airflow.cfg里的相关连接配置。
   对于全新安装的系统执行airflow initdb执行数据库初始化操作，对于版本升级执行airflow upgradedb宝座 
   在初始化和升级数据库阶段，确保你的拥有对数据库的全部操作权限。
3. 默认配置没有启用用户认证，生产环境建议开启ldap认证，需要[ldap]里配置认证信息，同时开启[webserver]里的authenticate
4. 确保当前目录是python3.6的虚拟环境并且已经激活，python3.6 -m venv `pwd` && source bin/activate
5. ./installAirflow.sh
6. 如果希望直接在airflow目录下运行业务程序，安装./installRuntime.sh 
7. 将supervisor/airflow.conf添加到supervisord的配置中，默认放到/etc/supervisord.d目录
