""" Deployment of your django project.
"""

from fabric.api import *
import os
import time
# import requests


env.user = "scouteronglass"
env.remote_user = "scouteronglass"
env.hosts = ["scouteronglass.com"]
env.project = "scouter"
env.password = open('fabric_pass.txt', 'r').read()


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
#            run('pip install -r ' + os.path.join(path, 'production_requirements.txt'))
            run('python manage.py syncdb --settings={0}'.format(settings))
            run('python manage.py migrate --noinput') # if you use south
            run('python manage.py collectstatic -c --noinput --settings={0}'.format(settings))


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

def deploy():
    """ Deploy Django Project.
    """
    path = '/home/{0}/{1}/'.format(env.remote_user, env.project)

    #put_files(path)
    deploy_server_files(env.project)
    install_packages()
    mkdirs(path)
    update_django_project(path, branch='master')
    update_permissions(path)
    django_functions(path, settings='glass_scouter.settings'.format(env.project))
    restart_webserver(service=env.project)


def deploy_test():
    """ Deploy Django Project test version.
    """
    path = '/home/{0}/{1}_testing/'.format(env.remote_user, env.project)

    #put_files(path)
    deploy_server_files('{0}_test'.format(env.project))
    install_packages()
    mkdirs(path)
    update_django_project(path, branch='dev')
    django_functions(path, settings='{0}.testing_settings'.format(env.project))
    update_permissions(path)
    restart_webserver(service='{0}'.format(env.project))

def logs(path='/home/{0}/{1}/'.format(env.remote_user, env.project)):
    sudo("tail -f {0}".format(os.path.join(path, 'logs/*')))