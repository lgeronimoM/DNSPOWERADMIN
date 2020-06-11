from flask import render_template, redirect, url_for, request, jsonify, session, Blueprint
import os, requests, json, sys

# APP MVC
from app import app, cf, login_manager, db
from app.models import Users, Hosting, Domain, Register, Master, Slaves, Acls, Forwards

# MAIL
import email, smtplib, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

#packages ansible
from ansible import context
from ansible.cli import CLI
from ansible.module_utils.common.collections import ImmutableDict
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
 
#pagination
from flask_paginate import Pagination, get_page_parameter

# Graficas
import pygal
from pygal.style import NeonStyle
from pygal.style import Style

#Logs
import logging
from datetime import datetime #Fecha logs
from datetime import date
from datetime import timedelta #Graficas

#System
import os, requests, json

#login
from flask_login import UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy.orm import sessionmaker
from sqlalchemy import desc
from sqlalchemy import and_

LOG_FILENAME = datetime.now().strftime(cf.LOG_DIR)
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)
logging.info('Comenzando la aplicacion...')
        
####################### Endpoints #############################

@app.route('/hostedzone')
@login_required
def hostedZone():
    url = cf.APIHOSETD
    headers = {'Content-type': 'application/json'}
    hosting = requests.get(url, headers=headers, verify=False).json()
    user = current_user.username
    logging.info('Access page HostedZone')
    return render_template('hostedzone.html', user = user, zone=hosting)

def registers(registertype,registerdomain):
    reg = db.session.query(Register).filter().order_by(desc(Register.id)).first()
    val=int(reg.register)
    newregister=val+1
    now = datetime.now()
    registerdate = now.strftime("%B")
    register = Register(newregister,registerdate,registertype,registerdomain )
    db.session.add(register)

def zone():
    slaves = db.session.query(Slaves).filter().all()
    if slaves:
        for slave in slaves:
            dif=slave.id
            nameconf_slave(dif)
            tagsexc='configslave'
            ipmanage= slave.ipslave
            passwd= slave.password
            user= slave.user
            install_dns_playbook(tagsexc, ipmanage, passwd, user)
    tagsexc='configmaster'
    master = db.session.query(Master).filter().first()
    ipmanage= master.ipmaster
    passwd= master.password
    user= master.user
    zone_conf()
    nameconf_master()
    zone_domain()
    install_dns_playbook(tagsexc, ipmanage, passwd, user)

@app.route('/core/addhostedzone', methods=['POST'])
@login_required
def addhostedzone():
    hostingf = str(request.form['hostedZone'])
    domainf = str(request.form['domain'])
    insertQuery = Hosting(hostingf,domainf)
    db.session.add(insertQuery)
    registertype='add zone'
    registerdomain=hostingf+'.'+domainf
    registers(registertype,registerdomain)
    zone()
    logging.info('Add Domain'+' '+registerdomain)
    db.session.commit()
    return redirect(url_for('hostedZone'))

@app.route('/deletedomainzone', methods=['POST'])
@login_required
def deletedomainzone():
    idf = int(request.form['id'])
    url = cf.APIHOSETD
    headers = {'Content-type': 'application/json'}
    hosting = requests.get(url, headers=headers, verify=False).json()
    for host in hosting:
        if int(host['id'])==idf:
            db.session.query(Hosting).filter(Hosting.id == idf).delete(synchronize_session=False)
            db.session.query(Domain).filter(Domain.host == idf).delete(synchronize_session=False)
            db.session.commit()
            registertype='delete zone'
            registerdomain=str(host['zones'])
            registers(registertype,registerdomain)
            zone()
    db.session.commit()
    return redirect(url_for('hostedZone'))

@app.route('/editdomainzone', methods=['POST'])
@login_required
def editdomainzone():
    if request.form['update_button']:
        idf = int(request.form['update_button'])
        query = db.session.query(Hosting).filter(Hosting.id == idf).first()
        db.session.commit()
        user = current_user.username
        #return str(query.name)+str(query.host)+str(query.typevalue)+str(query.value)+str(query.active)+' '+"Update"
        return render_template('editZone.html', user=user, value=query.zone, id=idf, domain=query.domain )

@app.route('/updatedomainzone', methods=['POST'])
@login_required
def updatedomainzone():
    idf=int(request.form['id'])
    value=str(request.form['value'])
    domain=str(request.form['domain'])
    db.session.query(Hosting).filter(Hosting.id == idf).update({'zone':value, 'domain':domain})
    db.session.commit()
    registertype='edit zone'
    registerdomain=value+'.'+domain
    registers(registertype,registerdomain)
    zone()
    return redirect(url_for('hostedZone'))

#################################### dns domain ##################################
@app.route('/domain')
@login_required
def domain():
    url=cf.APIHOSETD
    value=request.args.get('res')
    mess=request.args.get('mess')
    domain=db.session.query(Domain).filter().all()
    name=""
    headers = {'Content-type': 'application/json'}
    hosting = requests.get(url, headers=headers, verify=False).json()
    search = False
    data = db.session.query(Domain).filter().all()
    if value:
        search = True
        query = db.session.query(Hosting).filter(Hosting.id == int(value)).first()
        name=query.zone+'.'+query.domain
        logging.info('Consult Domain and show on table')
        domain = db.session.query(Domain).filter(Domain.host==int(value)).all()
    page = request.args.get(get_page_parameter(), type=int, default=1)
    pagination = Pagination(page=page, total=len(data), offset=0, per_page=10, search=search, record_name='Domains')
    logging.info('Access page Domain')
    user = current_user.username
    return render_template('domain.html', user = user, zone=hosting, data=domain, name=name, mess=mess, valueres=value, pagination=pagination)

@app.route('/core/adddomain', methods=['POST'])
@login_required
def adddomain():
    # api hosting
    url=cf.APIHOSETD
    headers = {'Content-type': 'application/json'}
    apihosting = requests.get(url, headers=headers, verify=False).json()
    # form
    hostingf=request.form['zone']
    namef = str(request.form['name'])
    valuef = str(request.form['value'])
    tipof = str(request.form['tipo'])
    domain = db.session.query(Domain).filter(and_(Domain.name==namef,Domain.host==hostingf,Domain.value==valuef)).first()
    if domain:
        mensage="This domain zone have already been added"
        return redirect(url_for('domain', res=hostingf, mess=mensage))
    insertQuery = Domain(namef,tipof,valuef,True,hostingf)
    db.session.add(insertQuery)
    for zone in apihosting:
        if zone['id']==int(hostingf):
            subdomain=zone['zones']
            zone_subdomain(subdomain)
            registerdomain=subdomain
    registertype='add domain'
    registers(registertype,registerdomain)
    master = db.session.query(Master).filter().first()
    ipmanage= master.ipmaster
    passwd= master.password
    user= master.user
    tagsexc='subdomain'
    subdomain_conf(subdomain,hostingf, namef, valuef, tipof)
    install_dns_playbook(tagsexc, ipmanage, passwd, user)
    db.session.commit()
    logging.info('Add Domain'+namef+' '+tipof+' '+valuef+' '+hostingf)
    return redirect(url_for('domain', res=hostingf))

@app.route('/core/editdomain', methods=['POST'])
@login_required
def editdomain():
    if request.form['update_button']:
        iddomain=request.form['iddomain']
        idf = int(request.form['update_button'])
        query = db.session.query(Domain).filter(Domain.id == idf).first()
        user = current_user.username
        #return str(query.name)+str(query.host)+str(query.typevalue)+str(query.value)+str(query.active)+' '+"Update"
        return render_template('edit.html', user=user, 	typef=query.typevalue, name = query.name, value=query.value, id=idf, iddomain=iddomain )

@app.route('/core/updatedomain', methods=['POST'])
@login_required
def updatedomain():
    # api hosting
    url=cf.APIHOSETD
    headers = {'Content-type': 'application/json'}
    apihosting = requests.get(url, headers=headers, verify=False).json()

    idf=int(request.form['id'])
    zoneid=int(request.form['iddomain'])
    valuef=str(request.form['valuef'])
    namef=str(request.form['namef'])
    typef=str(request.form['typevalue'])
    domain = db.session.query(Domain).filter(and_(Domain.name==namef,Domain.host==zoneid,Domain.value==valuef)).first()

    if domain:
        mensage="This domain have already been added"
        return redirect(url_for('domain', res=zoneid, mess=mensage))
    else:
        db.session.query(Domain).filter(Domain.id == idf).update({'value':valuef,'name':namef})
        db.session.commit()
        for zone in apihosting:
            if zone['id']==zoneid:
                subdomain=zone['zones']
                zone_subdomain(subdomain)
                registerdomain=subdomain
        registertype='edit domain'
        registers(registertype,registerdomain)
        master = db.session.query(Master).filter().first()
        ipmanage= master.ipmaster
        passwd= master.password
        user= master.user
        tagsexc='subdomain'
        subdomain_conf(subdomain, zoneid, namef, valuef, typef)
        install_dns_playbook(tagsexc, ipmanage, passwd, user)
        return redirect(url_for('domain', res=zoneid))

@app.route('/core/deletedomain', methods=['POST'])
@login_required
def deletedomain():
    if request.form['delete_button']:
        # api hosting
        url=cf.APIHOSETD
        headers = {'Content-type': 'application/json'}
        apihosting = requests.get(url, headers=headers, verify=False).json()

        zoneid=request.form['iddomain']
        idf = int(request.form['delete_button'])
        db.session.query(Domain).filter(Domain.id == idf).delete(synchronize_session=False)
        db.session.commit()
        for zone in apihosting:
            if int(zone['id']) == int(zoneid):
                subdomain=zone['zones']
                zone_subdomain(subdomain)
                registerdomain=subdomain
        registertype='delete domain'
        registers(registertype,registerdomain)
        master = db.session.query(Master).filter().first()
        ipmanage= master.ipmaster
        passwd= master.password
        user= master.user
        tagsexc='subdomain'
        namef=""
        valuef=""
        typef=""
        subdomain_conf(subdomain,zoneid, namef, valuef, typef)
        install_dns_playbook(tagsexc, ipmanage, passwd, user)
        return redirect(url_for('domain', res=zoneid))


########################################### API Ansible-Playbooks ###################################################

def install_dns_playbook(tagsexc, ipmanage, passwd, user):
    logging.info('runnig ansible-playbook install dns')
    file = open('app/ansible/hosts','w')
    file.write('[dnsservers]\n')
    file.write(ipmanage)
    file.close()
    loader = DataLoader()
    context.CLIARGS = ImmutableDict(tags={tagsexc}, listtags=False, listtasks=False, listhosts=False, syntax=False, connection='ssh',
                    module_path=None, forks=10, remote_user='ansadmin', private_key_file=None,
                    ssh_common_args=None, ssh_extra_args=None, sftp_extra_args=None, scp_extra_args=None, become=True,
                    become_method='sudo', become_user='root', verbosity=True, check=False, start_at_task=None,
                    extra_vars={'ansible_ssh_user='+user+'', 'ansible_ssh_pass='+passwd+'', 'ansible_become_pass='+passwd+''})
    inventory = InventoryManager(loader=loader, sources=('app/ansible/hosts'))
    variable_manager = VariableManager(loader=loader, inventory=inventory, version_info=CLI.version_info(gitinfo=False))
    pbex = PlaybookExecutor(playbooks=['app/ansible/webadmindns.yml'], inventory=inventory, variable_manager=variable_manager, loader=loader, passwords={})
    results = pbex.run()
    db.session.commit() 

####################################### File config named.conf #############################################################

def nameconf_master():
    file = open('app/ansible/roles/webadmindns/templates/named.conf.master.j2','w')
    file.write('acl "allowed" {\n')
    acls = db.session.query(Acls).filter().all()
    for acl in acls:
        file.write('        '+acl.ipacl+';\n')
    file.write('};\n')
    file.write('acl "slaves" {\n')
    slaves = db.session.query(Slaves).filter().all()
    for slave in slaves:
        file.write('        '+slave.ipslave+';\n')
    file.write('};\n')
    file.write('options {\n')
    file.write('        directory "/etc/named";\n')
    master = db.session.query(Master).filter().first()
    file.write('        listen-on port 53 { '+master.ipmaster+'; 127.0.0.1; };\n')
    file.write('        listen-on-v6 { none; };\n')
    file.write('        allow-query  { allowed; 127.0.0.0/8; };\n')
    forwards = db.session.query(Forwards).filter().all()
    if forwards:
        file.write('        forwarders {\n')
        for forward in forwards:
            file.write('                '+forward.ipforward+'; \n')
        file.write('        };\n')
    else:
        file.write('        recursion no;\n')   
    file.write('        version "No disponible";\n')
    file.write('        check-names master ignore;\n')
    file.write('        check-names response ignore;\n')
    file.write('};\n')
    url = cf.APIHOSETD
    headers = {'Content-type': 'application/json'}
    hosting = requests.get(url, headers=headers, verify=False).json()
    for zone in hosting:
        file.write('zone "'+zone['zones']+'" {\n') 
        file.write('        type master;\n')
        file.write('        file "/etc/named/zones/'+zone['zones']+'.zone";\n')
        file.write('        allow-transfer { slaves; };\n')
        file.write('};\n')
    db.session.commit()
    file.close() 

def nameconf_slave(id):
    file = open('app/ansible/roles/webadmindns/templates/named.conf.slave.j2','w')
    file.write('acl "allowed" {\n')
    acls = db.session.query(Acls).filter().all()
    for acl in acls:
        file.write('        '+acl.ipacl+';\n')
    file.write('};\n')
    file.write('options {\n')
    file.write('        directory "/etc/named";\n')
    slave = db.session.query(Slaves).filter(Slaves.id == id).first()
    file.write('        listen-on port 53 { '+slave.ipslave+'; 127.0.0.1; };\n')
    file.write('        listen-on-v6 { none; };\n')
    file.write('        allow-query  { allowed; 127.0.0.0/8; };\n')
    forwards = db.session.query(Forwards).filter().all()
    if forwards:
        file.write('        forwarders {\n')
        for forward in forwards:
            file.write('                '+forward.ipforward+'; \n')
        file.write('        };\n')
    else:
        file.write('        recursion no;\n')    
    file.write('        version "No disponible";\n')
    file.write('};\n')
    url = cf.APIHOSETD
    headers = {'Content-type': 'application/json'}
    hosting = requests.get(url, headers=headers, verify=False).json()
    master = db.session.query(Master).filter().first()
    for zone in hosting:
        file.write('zone "'+zone['zones']+'" {\n') 
        file.write('        type slave;\n')
        file.write('        file "/etc/named/cache/'+zone['zones']+'.zone";\n')
        file.write('        masters { '+master.ipmaster+'; };\n')
        file.write('};\n')
    db.session.commit()
    file.close()

####################################### File config mydomain.zone #############################################################

def zone_conf():
    logging.info('creating YML file')
    url = cf.APIHOSETD
    headers = {'Content-type': 'application/json'}
    hosting = requests.get(url, headers=headers, verify=False).json()
    for zone in hosting:
        zonedomain = zone['zones']
        file = open('app/ansible/roles/webadmindns/templates/'+zonedomain+'.zone.j2','w')
        file.write('$ORIGIN '+zonedomain+'.\n')
        file.write('$TTL 86400\n')
        file.write('@   IN  SOA     masterdns.'+zonedomain+'. root.'+zonedomain+'. (\n')
        #serial = db.session.query(Register).filter().first()
        serial = db.session.query(Register).filter().order_by(desc(Register.id)).first()
        file.write('        '+str(serial.register)+'    ;Serial\n')
        file.write('        3600        ;Refresh\n')
        file.write('        1800        ;Retry\n')
        file.write('        604800      ;Expire\n')
        file.write('        86400       ;Minimum TTL )\n')
        file.write(')\n')
        file.write('        NS      masterdns.'+zonedomain+'.\n')
        slaves = db.session.query(Slaves).filter().all()
        con=0
        for slave in slaves:
            con=con+1
            file.write('@   IN  NS   slavedns'+str(con)+'.'+zonedomain+'.\n')
            file.write('slavedns'+str(con)+'       IN  A   '+slave.ipslave+'\n')
        master = db.session.query(Master).filter().first()
        file.write('masterdns   IN  A   '+master.ipmaster+'\n')
        dif=zone['id']
        url2 = cf.APIDOMAIN+str(dif)
        domains = requests.get(url2, headers=headers, verify=False).json()
        for domain in domains:
            file.write(domain['name']+'   '+domain['typevalue']+'  '+domain['value']+'\n')
    db.session.commit()
    file.close() 

def zone_domain():
    logging.info('creating YML file')
    url = cf.APIHOSETD
    headers = {'Content-type': 'application/json'}
    hosting = requests.get(url, headers=headers, verify=False).json()
    file = open('app/ansible/roles/webadmindns/vars/main.yml','w')
    file.write('---\n')
    file.write('#configuracion zonas\n')
    file.write('zoneDomain:\n')
    for zone in hosting:
        file.write('  - '+zone['zones']+'\n')
    file.close() 

def subdomain_conf(zone, dif, namef, valuef, tipof):
    logging.info('creating YML file')
    file = open('app/ansible/roles/webadmindns/templates/'+zone+'.zone.j2','w')
    file.write('$ORIGIN '+zone+'.\n')
    file.write('$TTL 86400\n')
    file.write('@   IN  SOA     masterdns.'+zone+'. root.'+zone+'. (\n')
    #serial = db.session.query(Register).filter().first()
    serial = db.session.query(Register).filter().order_by(desc(Register.id)).first()
    file.write('        '+str(serial.register)+'    ;Serial\n')
    file.write('        3600        ;Refresh\n')
    file.write('        1800        ;Retry\n')
    file.write('        604800      ;Expire\n')
    file.write('        86400       ;Minimum TTL )\n')
    file.write(')\n')
    file.write('        NS      masterdns.'+zone+'.\n')
    slaves = db.session.query(Slaves).filter().all()
    con=0
    for slave in slaves:
        con=con+1
        file.write('@   IN  NS   slavedns'+str(con)+'.'+zone+'.\n')
        file.write('slavedns'+str(con)+'       IN  A   '+slave.ipslave+'\n')
    master = db.session.query(Master).filter().first()
    file.write('masterdns   IN  A   '+master.ipmaster+'\n')
    headers = {'Content-type': 'application/json'}
    url2 = cf.APIDOMAIN+str(dif)
    domains = requests.get(url2, headers=headers, verify=False).json()
    for domain in domains:
        file.write(domain['name']+'           '+domain['typevalue']+'          '+domain['value']+'\n')
        #file.write('};\n')
    if namef:
        file.write(namef+'           '+tipof+'          '+valuef+'\n')
    db.session.commit()
    file.close() 

def zone_subdomain(zone):
    logging.info('creating YML file')
    url = cf.APIHOSETD
    headers = {'Content-type': 'application/json'}
    hosting = requests.get(url, headers=headers, verify=False).json()
    file = open('app/ansible/webadmindns.yml','w')
    file.write('---\n')
    file.write('- hosts: dnsservers\n')
    file.write('  name: "Playbook Webadmin DNS server slaves and masters"\n')
    file.write('  gather_facts: no\n')
    file.write('  vars:\n')
    file.write('    subDomain: '+zone+'\n')
    file.write('  roles:\n')
    file.write('    - roles/webadmindns\n')
    file.close()

#################################### API ###################################

@app.route('/core/v1.0/hostedzone')
def apihostedzone():
    resul = db.session.query(Hosting).all()
    art=[]
    for res in resul:
        zone=res.zone+"."+res.domain
        value=res.zone
        idf=res.id
        dict ={'zones': zone, 'value': value, 'domain': res.domain, 'id':idf }
        art.append(dict)
    db.session.commit()
    return jsonify(art), 200

@app.route('/core/v1.0/domain/<domain>')
def apidomain(domain):
    art=[]
    resul = db.session.query(Domain).filter(Domain.host.in_([domain])).all()
    for res in resul:
        idf = res.id
        dom = res.name
        tipe = res.typevalue
        value = res.value
        active = res.active
        host = res.host
        dict ={'name' : dom, 'typevalue' : tipe, 'value' : value, 'active' : active, 'zone': host, 'id': idf}
        art.append(dict)
    db.session.commit()
    return jsonify(art), 200