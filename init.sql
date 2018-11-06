create database airflow DEFAULT CHARACTER SET latin1 COLLATE latin1_bin;
grant all privileges on airflow.* to 'airflow'@'%' identified by 'airflow';
