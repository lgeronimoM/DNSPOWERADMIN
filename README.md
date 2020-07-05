License
-------
BSD

Author Information
------------------
Luis Manuel Geronimo Sandoval 

#SysAdminOne 

Title
------------------
DNSPOWERADMIN

Description
------------------
Service BIND.

Aplicacion web con flask en python version 3 para la administracion de nombres de dominio en una red de intranet. 

It is programmed in python version 3 and uses the flask micro framework for web development, its main configuration engine is the ansible automation tool and a Sqlite 3 database.

Operation System DNS
------------------
master: Centos7/8

slave: Centos7/8

Installation process
------------------
#Dependencie:

sudo yum install git

#Install application:

sudo cd /tmp

sudo git clone https://github.com/lgeronimoM/DNSPOWERADMIN.git

sudo cd DNSPOWERADMIN

sudo chmod u+x install.sh

sudo ./install.sh

sudo systemctl start dnsweb

#Enable port 4000 firewalld:

sudo firewall-cmd --permanent --add-port=4000/tcp

sudo firewall-cmd --reload

