# Openstack pike install guide
### 1 Yum Repo
```shell
yum install centos-release-openstack-pike -y
yum install python-openstackclient openstack-selinux -y
```

### 2 Install MYSQL
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

### 3 Install Message queue for RabbitMq
```shell
yum install rabbitmq-server -y
systemctl enable rabbitmq-server.service
systemctl start rabbitmq-server.service
rabbitmqctl add_user openstack password
rabbitmqctl set_permissions openstack ".*" ".*" ".*"
```

### 4 Install and configure for Memcache
```shell
yum install memcached python-memcached -y
cat /etc/sysconfig/memcached

OPTIONS="-l 127.0.0.1,::1,controller"
systemctl enable memcached.service
systemctl start memcached.service
```

## Minimal deployment
### 1. keystone installation for Pike
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
#### 1.1 Create a domain, projects, users, and roles
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

#### 1.2 Verify operation
```shell
unset OS_AUTH_URL OS_PASSWORD
openstack --os-auth-url http://controller:35357/v3 \
  --os-project-domain-name Default --os-user-domain-name Default \
  --os-project-name admin --os-username admin token issue
```

#### 1.3 Create OpenStack client environment scripts
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

#### 1.4 Using the scripts
```shell
source admin-openrc
openstack token issue
```


### 2. glance installation for Pike
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
connection = mysql+pymysql://glance:password@controller/glance

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
password = password

[paste_deploy]
# ...
flavor = keystone

[glance_store]
# ...
stores = file,http
default_store = file
filesystem_store_datadir = /var/lib/glance/images/


cat /etc/glance/glance-registry.conf

[database]
# ...
connection = mysql+pymysql://glance:password@controller/glance

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
password = password

[paste_deploy]
# ...
flavor = keystone

```

#### 2.1 Create a domain, projects, users, and roles
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

#### 2.2 Sync database And start glance Serivce
```shell
su -s /bin/sh -c "glance-manage db_sync" glance

systemctl enable openstack-glance-api.service openstack-glance-registry.service

systemctl start openstack-glance-api.service openstack-glance-registry.service
```

### 3 nova installation for Pike
```shell
mysql -u root -p
CREATE DATABASE nova_api;
CREATE DATABASE nova;
CREATE DATABASE nova_cell0;

GRANT ALL PRIVILEGES ON nova_api.* TO 'nova'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON nova_api.* TO 'nova'@'%' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON nova.* TO 'nova'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON nova.* TO 'nova'@'%' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON nova_cell0.* TO 'nova'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON nova_cell0.* TO 'nova'@'%' IDENTIFIED BY 'password';

yum install openstack-nova-api openstack-nova-conductor \
  openstack-nova-console openstack-nova-novncproxy \
  openstack-nova-scheduler openstack-nova-placement-api -y
  
cat /etc/nova/nova.conf

[DEFAULT]
# ...
enabled_apis = osapi_compute,metadata

[api_database]
# ...
connection = mysql+pymysql://nova:password@controller/nova_api

[database]
# ...
connection = mysql+pymysql://nova:password@controller/nova

[DEFAULT]
# ...
transport_url = rabbit://openstack:password@controller

[api]
# ...
auth_strategy = keystone

[keystone_authtoken]
# ...
auth_uri = http://controller:5000
auth_url = http://controller:35357
memcached_servers = controller:11211
auth_type = password
project_domain_name = default
user_domain_name = default
project_name = service
username = nova
password = password


[DEFAULT]
# ...
my_ip = 10.0.0.11

[DEFAULT]
# ...
use_neutron = True
firewall_driver = nova.virt.firewall.NoopFirewallDriver

[vnc]
enabled = true
# ...
vncserver_listen = $my_ip
vncserver_proxyclient_address = $my_ip


[glance]
# ...
api_servers = http://controller:9292

[oslo_concurrency]
# ...
lock_path = /var/lib/nova/tmp


[placement]
# ...
os_region_name = RegionOne
project_domain_name = Default
project_name = service
auth_type = password
user_domain_name = Default
auth_url = http://controller:35357/v3
username = placement
password = password

cat /etc/httpd/conf.d/00-nova-placement-api.conf

<Directory /usr/bin>
   <IfVersion >= 2.4>
      Require all granted
   </IfVersion>
   <IfVersion < 2.4>
      Order allow,deny
      Allow from all
   </IfVersion>
</Directory>

```

#### 3.1 Create a domain, projects, users, and roles
```shell
source admin-openrc
openstack user create --domain default --password-prompt nova
openstack role add --project service --user nova admin

openstack service create --name nova \
  --description "OpenStack Compute" compute
  
openstack endpoint create --region RegionOne \
  compute public http://controller:8774/v2.1
  
openstack endpoint create --region RegionOne \
  compute internal http://controller:8774/v2.1

openstack endpoint create --region RegionOne \
  compute admin http://controller:8774/v2.1


openstack user create --domain default --password-prompt placement
openstack role add --project service --user placement admin
openstack service create --name placement --description "Placement API" placement
openstack endpoint create --region RegionOne placement public http://controller:8778
openstack endpoint create --region RegionOne placement internal http://controller:8778
openstack endpoint create --region RegionOne placement admin http://controller:8778

```


#### 3.2 Sync Database And start
```shell
systemctl restart httpd
su -s /bin/sh -c "nova-manage api_db sync" nova

su -s /bin/sh -c "nova-manage cell_v2 map_cell0" nova
su -s /bin/sh -c "nova-manage cell_v2 create_cell --name=cell1 --verbose" nova
su -s /bin/sh -c "nova-manage db sync" nova
nova-manage cell_v2 list_cells

systemctl enable openstack-nova-api.service \
  openstack-nova-consoleauth.service openstack-nova-scheduler.service \
  openstack-nova-conductor.service openstack-nova-novncproxy.service

systemctl start openstack-nova-api.service \
  openstack-nova-consoleauth.service openstack-nova-scheduler.service \
  openstack-nova-conductor.service openstack-nova-novncproxy.service

```

### 4 Compute node install Nova
```shell
yum install centos-release-openstack-pike -y
yum install python-openstackclient openstack-selinux -y
yum install openstack-nova-compute

cat /etc/nova/nova.conf

[DEFAULT]
# ...
enabled_apis = osapi_compute,metadata

[DEFAULT]
# ...
transport_url = rabbit://openstack:RABBIT_PASS@controller

[api]
# ...
auth_strategy = keystone

[keystone_authtoken]
# ...
auth_uri = http://controller:5000
auth_url = http://controller:35357
memcached_servers = controller:11211
auth_type = password
project_domain_name = default
user_domain_name = default
project_name = service
username = nova
password = password

[DEFAULT]
# ...
my_ip = MANAGEMENT_INTERFACE_IP_ADDRESS (nova controller node)

[DEFAULT]
# ...
use_neutron = True
firewall_driver = nova.virt.firewall.NoopFirewallDriver

[vnc]
# ...
enabled = True
vncserver_listen = 0.0.0.0
vncserver_proxyclient_address = $my_ip
novncproxy_base_url = http://controller:6080/vnc_auto.html

[glance]
# ...
api_servers = http://controller:9292

[oslo_concurrency]
# ...
lock_path = /var/lib/nova/tmp

[placement]
# ...
os_region_name = RegionOne
project_domain_name = Default
project_name = service
auth_type = password
user_domain_name = Default
auth_url = http://controller:35357/v3
username = placement
password = password

egrep -c '(vmx|svm)' /proc/cpuinfo
'''
If this command returns a value of one or greater, your compute node supports hardware acceleration which typically requires no additional configuration.

If this command returns a value of zero, your compute node does not support hardware acceleration and you must configure libvirt to use QEMU instead of KVM.

Edit the [libvirt] section in the /etc/nova/nova.conf file as follows:

[libvirt]
# ...
virt_type = qemu
'''

systemctl enable libvirtd.service openstack-nova-compute.service
systemctl start libvirtd.service openstack-nova-compute.service

```

#### At controller node run command Add the compute node to the cell database
```shell
. admin-openrc
openstack compute service list --service nova-compute
su -s /bin/sh -c "nova-manage cell_v2 discover_hosts --verbose" nova

```

### 5 neutron installation for Pike
```shell
mysql -u root -p
CREATE DATABASE neutron;
GRANT ALL PRIVILEGES ON neutron.* TO 'neutron'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON neutron.* TO 'neutron'@'%' IDENTIFIED BY 'password';
```
#### 5.1 Create OpenStack client environment scripts
```shell
. admin-openrc
openstack user create --domain default --password-prompt neutron
openstack role add --project service --user neutron admin

openstack service create --name neutron \
  --description "OpenStack Networking" network
  
openstack endpoint create --region RegionOne \
  network public http://controller:9696
  
openstack endpoint create --region RegionOne \
  network internal http://controller:9696

openstack endpoint create --region RegionOne \
  network admin http://controller:9696
  
```

#### 5.2 Configure Networking Option 2: Self-service networks
```shell
yum install openstack-neutron openstack-neutron-ml2 \
  openstack-neutron-linuxbridge ebtables

cat /etc/neutron/neutron.conf

[database]
# ...
connection = mysql+pymysql://neutron:NEUTRON_DBPASS@controller/neutron

[DEFAULT]
# ...
core_plugin = ml2
service_plugins = router
allow_overlapping_ips = true

[DEFAULT]
# ...
transport_url = rabbit://openstack:RABBIT_PASS@controller

[DEFAULT]
# ...
auth_strategy = keystone

[keystone_authtoken]
# ...
auth_uri = http://controller:5000
auth_url = http://controller:35357
memcached_servers = controller:11211
auth_type = password
project_domain_name = default
user_domain_name = default
project_name = service
username = neutron
password = NEUTRON_PASS

[DEFAULT]
# ...
notify_nova_on_port_status_changes = true
notify_nova_on_port_data_changes = true

[nova]
# ...
auth_url = http://controller:35357
auth_type = password
project_domain_name = default
user_domain_name = default
region_name = RegionOne
project_name = service
username = nova
password = NOVA_PASS

[oslo_concurrency]
# ...
lock_path = /var/lib/neutron/tmp

cat /etc/neutron/plugins/ml2/ml2_conf.ini

[ml2]
# ...
type_drivers = flat,vlan,vxlan

[ml2]
# ...
tenant_network_types = vxlan

[ml2]
# ...
mechanism_drivers = linuxbridge,l2population

[ml2]
# ...
extension_drivers = port_security

[ml2_type_flat]
# ...
flat_networks = provider

[ml2_type_vxlan]
# ...
vni_ranges = 1:1000

[securitygroup]
# ...
enable_ipset = true


cat /etc/neutron/plugins/ml2/linuxbridge_agent.ini

[linux_bridge]
physical_interface_mappings = provider:eth0

[vxlan]
enable_vxlan = true
local_ip = OVERLAY_INTERFACE_IP_ADDRESS (controller node ip)
l2_population = true

[securitygroup]
# ...
enable_security_group = true
firewall_driver = neutron.agent.linux.iptables_firewall.IptablesFirewallDriver

cat /etc/neutron/l3_agent.ini

[DEFAULT]
# ...
interface_driver = linuxbridge


cat /etc/neutron/dhcp_agent.ini

[DEFAULT]
# ...
interface_driver = linuxbridge
dhcp_driver = neutron.agent.linux.dhcp.Dnsmasq
enable_isolated_metadata = true


```

#### 5.3 Configure the metadata agent
```shell
cat /etc/neutron/metadata_agent.ini
[DEFAULT]
# ...
nova_metadata_host = controller
metadata_proxy_shared_secret = 123456

cat /etc/nova/nova.conf

[neutron]
# ...
url = http://controller:9696
auth_url = http://controller:35357
auth_type = password
project_domain_name = default
user_domain_name = default
region_name = RegionOne
project_name = service
username = neutron
password = password
service_metadata_proxy = true
metadata_proxy_shared_secret = 123456

ln -s /etc/neutron/plugins/ml2/ml2_conf.ini /etc/neutron/plugin.ini

su -s /bin/sh -c "neutron-db-manage --config-file /etc/neutron/neutron.conf \
  --config-file /etc/neutron/plugins/ml2/ml2_conf.ini upgrade head" neutron
  
systemctl restart openstack-nova-api.service

systemctl enable neutron-server.service \
  neutron-linuxbridge-agent.service neutron-dhcp-agent.service \
  neutron-metadata-agent.service

systemctl start neutron-server.service \
  neutron-linuxbridge-agent.service neutron-dhcp-agent.service \
  neutron-metadata-agent.service
  
systemctl enable neutron-l3-agent.service
systemctl start neutron-l3-agent.service
```

### 6 Install and configure neutron at compute node
```shell
yum install openstack-neutron-linuxbridge ebtables ipset -y
cat /etc/neutron/neutron.conf

[DEFAULT]
# ...
transport_url = rabbit://openstack:password@controller

[DEFAULT]
# ...
auth_strategy = keystone

[keystone_authtoken]
# ...
auth_uri = http://controller:5000
auth_url = http://controller:35357
memcached_servers = controller:11211
auth_type = password
project_domain_name = default
user_domain_name = default
project_name = service
username = neutron
password = password

[oslo_concurrency]
# ...
lock_path = /var/lib/neutron/tmp

cat /etc/nova/nova.conf

[neutron]
# ...
url = http://controller:9696
auth_url = http://controller:35357
auth_type = password
project_domain_name = default
user_domain_name = default
region_name = RegionOne
project_name = service
username = neutron
password = password


cat /etc/neutron/plugins/ml2/linuxbridge_agent.ini

[linux_bridge]
physical_interface_mappings = provider:eth0

[vxlan]
enable_vxlan = true
local_ip = OVERLAY_INTERFACE_IP_ADDRESS (compute node ip)
l2_population = true


[securitygroup]
# ...
enable_security_group = true
firewall_driver = neutron.agent.linux.iptables_firewall.IptablesFirewallDriver

systemctl restart openstack-nova-compute.service
systemctl enable neutron-linuxbridge-agent.service
systemctl start neutron-linuxbridge-agent.service
```
### 7 horizon installation for Pike
### 8 cinder installation for Pike


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
