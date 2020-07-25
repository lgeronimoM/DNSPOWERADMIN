#!/bin/bash

sudo yum clean all

sudo yum install epel-release -y

sudo yum install python3 python3-pip python3-devel gcc -y

sudo pip3 install --upgrade pip

sudo pip3 install virtualenv

sudo groupadd dnsweb

sudo useradd -s /usr/sbin/nologin udnsweb

sudo usermod -G dnsweb udnsweb

sudo mkdir -p /etc/dnsweb

sudo mkdir -p /var/log/dnsweb

sudo cp main.py /etc/dnsweb/
sudo cp wsgi.py /etc/dnsweb/
sudo cp -r app /etc/dnsweb/
sudo cp properties.py /etc/dnsweb/
sudo cp README.md /etc/dnsweb/
sudo cp requirements.txt /etc/dnsweb/
sudo cp -r env /etc/dnsweb/

sudo chown udnsweb.dnsweb /var/log/dnsweb -R
sudo chown udnsweb.dnsweb /etc/dnsweb -R

#sudo python3 -m venv /etc/dnsweb/env
#sudo source /etc/dnsweb/env/bin/activate
#sudo pip3 install -r /etc/dnsweb/requirements.txt

sudo echo -e "
[Unit]
Description=Gunicorn instance to serve myproject
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/etc/dnsweb
#Environment=PATH=/usr/local/bin
ExecStart=/etc/dnsweb/env/bin/uwsgi --http-socket :4000 --plugin python3 --module main:app --processes 2 --threads 2

[Install]
WantedBy=multi-user.target" > /etc/systemd/system/dnsweb.service

sudo deactivate

sudo systemctl daemon-reload