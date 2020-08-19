Licencia
-------
BSD

Autor
------------------
Luis Manuel Geronimo Sandoval 

Canal de youtube #SysAdminOne

Titulo
------------------
DNS Web

Descripción
------------------
Servicio de dns a instalar "BIND".

Aplicacion web con flask en python version 3 para la administracion de nombres de dominio en una red de intranet. 

Sistema Operativo
------------------
Para el maestro: Centos7/8 
 
Para el esclavo: Centos7/8

Recursos
------------------
2 cpu
2GB RAM
10GB HDD
internet

Procesos de instalación
------------------
sudo yum install git

sudo cd /tmp

sudo git clone https://github.com/lgeronimoM/DNSPOWERADMIN.git

sudo cd DNSPOWERADMIN

sudo chmod u+x install.sh

sudo ./install.sh

#Habilitar puerto 4000 en el firewall

sudo firewall-cmd --permanent --add-port=4000/tcp

sudo firewall-cmd --reload

sudo systemctl start dnsweb

acceso web
------------------
usuario: admin
contraseña: dnsadmin