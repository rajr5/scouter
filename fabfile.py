""" Deployment of your django project.
"""

from fabric.api import *
import os
import time
import xmpp
import ConfigParser
# import requests


env.user = "scouteronglass"
env.remote_user = "scouteronglass"
env.hosts = ["scouteronglass.com"]
env.project = "scouter"
env.password = open('fabric_pass.txt', 'r').read()
env.xmpp_auth = {}
env.xmpp_client = None


def configure_xmpp_message(config_file='/etc/xmpp_credentials.ini', section=None):
    config = ConfigParser.ConfigParser()
    config.read(config_file)
    if section is None:
        section = env.project
    if not config.has_section(section):
        print "Could not find section {0} in config file: {1}".format(section, config_file)
        return

    env.xmpp_auth['username'] = config.get(section, 'username')
    env.xmpp_auth['password'] = config.get(section, 'password')
    env.xmpp_auth['hostname'] = config.get(section, 'hostname')
    env.xmpp_auth['to'] = config.get(section, 'to')
    print env.xmpp_auth


def send_xmpp_message(msg):
    if env.xmpp_client is None:
        # env.xmpp_client = xmpp.Client(env.xmpp_auth['hostname'])
        env.xmpp_client = xmpp.Client(env.xmpp_auth['hostname'], debug=[])
        env.xmpp_client.connect()
        env.xmpp_client.auth(
            env.xmpp_auth['username'], env.xmpp_auth['password'])
        env.xmpp_client.sendInitPresence()
    message = xmpp.Message(env.xmpp_auth['to'], msg)
    message.setAttr('type', 'chat')
    env.xmpp_client.send(message)


def update_django_project(path, branch):
    """ Updates the remote django project. Delete any fiddling we did on the server. That belongs in source control.
    """
    with cd(path):
        sudo('git stash')
        sudo('git pull origin {0}'.format(branch))
        sudo('git checkout {0}'.format(branch))


def django_functions(path, settings):
    with cd(path):
        with prefix('source ' + os.path.join(path, 'bin/activate')):
            run('easy_install -U distribute==0.6.28')
            run('pip install -r ' + os.path.join(path, 'requirements.txt'))
# run('pip install -r ' + os.path.join(path,
# 'production_requirements.txt'))
            run('python manage.py syncdb --settings={0}'.format(settings))
            run('python manage.py migrate --noinput')  # if you use south
            run('python manage.py collectstatic  --noinput --settings={0}'.format(settings))


def update_permissions(path):
    with cd(path):
        sudo('chown -R {0}:{0} '.format(env.remote_user) + path)


def restart_webserver(service):
    """ Restarts remote nginx and uwsgi.
    """
    sudo("stop {0}".format(service))
    # Give uwsgi time to shut down cleanly
    time.sleep(2)
    sudo("start {0}".format(service))
    sudo("/etc/init.d/nginx reload")


def install_packages():
    sudo("apt-get install -yq python-dev mysql-client python-mysqldb libmysqlclient-dev")


def mkdirs(path):
    sudo("mkdir -p {0}staticfiles".format(path))
    sudo("mkdir -p {0}logs".format(path))
    sudo("mkdir -p /var/run/{0}/".format(env.project))


def deploy_server_files(site):
    remote_filename = "/etc/init/{0}.conf".format(site)
    # put("production/init", remote_filename, use_sudo=True)
    sudo("chmod +x {0}".format(remote_filename))


def create_db():
    run("""echo "create database $DB_NAME; grant all privileges on $DB_NAME.* to '$DB_USER'@'localhost' identified by '$DB_PASSWORD' " > db.sql""")
    sudo("mysql -u root -p$(cat /root/mysql) < db.sql")


def deploy():
    """ Deploy Django Project.
    """
    path = '/home/{0}/{1}/'.format(env.remote_user, env.project)
    configure_xmpp_message()
    send_xmpp_message("Starting production deploy for {0}".format(env.project))
    # put_files(path)
    deploy_server_files(env.project)
    install_packages()
    mkdirs(path)
    update_django_project(path, branch='master')
    update_permissions(path)
    django_functions(path, settings='scouter.settings'.format(env.project))
    restart_webserver(service=env.project)
    send_xmpp_message(
        "Production deploy successful for {0}!".format(env.project))


def deploy_test():
    """ Deploy Django Project test version.
    """
    path = '/home/{0}/{1}_testing/'.format(env.remote_user, env.project)

    # put_files(path)
    configure_xmpp_message()
    send_xmpp_message("Starting testing deploy for {0}".format(env.project))
    deploy_server_files('{0}_test'.format(env.project))
    install_packages()
    mkdirs(path)
    update_django_project(path, branch='dev')
    django_functions(path, settings='{0}.testing_settings'.format(env.project))
    update_permissions(path)
    restart_webserver(service='{0}'.format(env.project))
    send_xmpp_message("Testing deploy successful for {0}!".format(env.project))


def logs(path='/home/{0}/{1}/'.format(env.remote_user, env.project)):
    sudo("tail -f {0}".format(os.path.join(path, 'logs/*')))
