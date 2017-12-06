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

