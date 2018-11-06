1. airflow不支持在windows下运行，它依赖一些只能在unix上运行的python模块
2. 可行的方式是在windows上开发代码，在linux上进行调测
3. windows上的具体步骤如下：
   * 安装windows版python虚拟环境
       pip install virtualenvwrapper-win; mkvirtualenv airflow
   * 激活airflow虚拟环境
       %USERPROFILE%\Envs\airflow\Scripts\activate.bat
   * 在虚拟环境安装airflow：
       .\installAirflow.bat; .\installRuntime.bat
   * 后续配置python ide使用这套虚拟环境即可
4. 调测可以使用远程linux开发机，也可以使用wsl，安装airflow的方式请参考README.md   
5. 注意airflow创建的日志目录名字包含冒号，Windows上无法创建成功，使用wsl的时候不要把日志放在windows目录上  
