# Openstack pike install guide
## 1 Yum Repo
```shell
yum install centos-release-openstack-pike -y
yum install python-openstackclient openstack-selinux -y
```

## 2 Install MYSQL
```shell
yum install mariadb mariadb-server python2-PyMySQL

cat /etc/my.cnf.d/openstack.cnf
[mysqld]
bind-address = 0.0.0.0

default-storage-engine = innodb
innodb_file_per_table = on
max_connections = 4096
collation-server = utf8_general_ci
character-set-server = utf8

systemctl enable mariadb.service
systemctl start mariadb.service
mysql_secure_installation

# input enter -> y ->  new password -> y -> y -> y -> y 
```

## 3 Install Message queue for RabbitMq
```shell
yum install rabbitmq-server -y
systemctl enable rabbitmq-server.service
systemctl start rabbitmq-server.service
rabbitmqctl add_user openstack password
rabbitmqctl set_permissions openstack ".*" ".*" ".*"
```

## 4 Install and configure for Memcache
```shell
yum install memcached python-memcached -y
cat /etc/sysconfig/memcached

OPTIONS="-l 127.0.0.1,::1,controller"
systemctl enable memcached.service
systemctl start memcached.service
```

# Minimal deployment
## 1. keystone installation for Pike
```shell
mysql -u root -p
CREATE DATABASE keystone;
GRANT ALL PRIVILEGES ON keystone.* TO 'keystone'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON keystone.* TO 'keystone'@'%' IDENTIFIED BY 'password';
flush privileges ;

yum -y install openstack-keystone httpd mod_wsgi
cat /etc/keystone/keystone.conf

[database]
# ...
connection = mysql+pymysql://keystone:password@controller/keystone

[token]
# ...
provider = fernet

su -s /bin/sh -c "keystone-manage db_sync" keystone
keystone-manage fernet_setup --keystone-user keystone --keystone-group keystone
keystone-manage credential_setup --keystone-user keystone --keystone-group keystone

keystone-manage bootstrap --bootstrap-password password \
  --bootstrap-admin-url http://controller:35357/v3/ \
  --bootstrap-internal-url http://controller:5000/v3/ \
  --bootstrap-public-url http://controller:5000/v3/ \
  --bootstrap-region-id RegionOne
  
  
cat /etc/httpd/conf/httpd.conf
 ServerName controller

ln -s /usr/share/keystone/wsgi-keystone.conf /etc/httpd/conf.d/
systemctl enable httpd.service
systemctl start httpd.service

export OS_USERNAME=admin
export OS_PASSWORD=password
export OS_PROJECT_NAME=admin
export OS_USER_DOMAIN_NAME=Default
export OS_PROJECT_DOMAIN_NAME=Default
export OS_AUTH_URL=http://controller:35357/v3
export OS_IDENTITY_API_VERSION=3
```
### 1.1 Create a domain, projects, users, and roles
```shell
openstack project create --domain default \
  --description "Service Project" service
  
openstack project create --domain default \
  --description "Demo Project" demo
  
openstack user create --domain default \
  --password-prompt demo
  
openstack role create user
openstack role add --project demo --user demo user
```

### 1.2 Verify operation
```shell
unset OS_AUTH_URL OS_PASSWORD
openstack --os-auth-url http://controller:35357/v3 \
  --os-project-domain-name Default --os-user-domain-name Default \
  --os-project-name admin --os-username admin token issue
```

### 1.3 Create OpenStack client environment scripts
```shell
cat admin-openrc

export OS_PROJECT_DOMAIN_NAME=Default
export OS_USER_DOMAIN_NAME=Default
export OS_PROJECT_NAME=admin
export OS_USERNAME=admin
export OS_PASSWORD=password
export OS_AUTH_URL=http://controller:35357/v3
export OS_IDENTITY_API_VERSION=3
export OS_IMAGE_API_VERSION=2


cat demo-openrc
export OS_PROJECT_DOMAIN_NAME=Default
export OS_USER_DOMAIN_NAME=Default
export OS_PROJECT_NAME=demo
export OS_USERNAME=demo
export OS_PASSWORD=password
export OS_AUTH_URL=http://controller:5000/v3
export OS_IDENTITY_API_VERSION=3
export OS_IMAGE_API_VERSION=2
```

### 1.4 Using the scripts
```shell
source admin-openrc
openstack token issue
```


## 2. glance installation for Pike
```shell
mysql -u root -p
CREATE DATABASE glance;
GRANT ALL PRIVILEGES ON glance.* TO 'glance'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON glance.* TO 'glance'@'%' IDENTIFIED BY 'password';
flush privileges ;
yum install openstack-glance -y

cat /etc/glance/glance-api.conf
[database]
# ...
connection = mysql+pymysql://glance:GLANCE_DBPASS@controller/glance

[keystone_authtoken]
# ...
auth_uri = http://controller:5000
auth_url = http://controller:35357
memcached_servers = controller:11211
auth_type = password
project_domain_name = default
user_domain_name = default
project_name = service
username = glance
password = GLANCE_PASS

[paste_deploy]
# ...
flavor = keystone


```

### 2.1 Create a domain, projects, users, and roles
```shell
source admin-openrc

openstack user create --domain default --password-prompt glance
openstack role add --project service --user glance admin

openstack service create --name glance \
  --description "OpenStack Image" image

openstack endpoint create --region RegionOne \
  image public http://controller:9292
  
openstack endpoint create --region RegionOne \
  image internal http://controller:9292

openstack endpoint create --region RegionOne \
  image admin http://controller:9292
  
```
## nova installation for Pike
## neutron installation for Pike
## horizon installation for Pike
## cinder installation for Pike


## FAQ
1. su -s /bin/sh -c "keystone-manage db_sync" keystone  #报错
- ImportError: cannot import name offset

```shell
解决：
  1. pip install --upgrade pip
  2. pip uninstall sqlparse
  3. rm -rf  /usr/lib/python2.7/site-packages/sqlparse*
  4. pip install sqlparse
```
