#!/bin/bash

cd ~
mkdir .ssh
ssh-keygen -q -f .ssh/id_rsa -N ""

#-------------------------------

cd .ssh
cat id_rsa.pub >> authorized_keys
ssh -o StrictHostKeyChecking=no 127.0.0.1 echo "connected to 127.0.0.1"

for i in `seq 1 $1`; do
	ssh-copy-id -i id_rsa root@10.10.20.$i
	ssh -o StrictHostKeyChecking=no 10.10.20.$i echo "connected to 10.10.20.$i"
done

#-------------------------------

cd ~
cat <<EOM >> /etc/ansible/hosts
[master]
127.0.0.1 ansible_connection=local ansible_python_interpreter=/usr/bin/python3

[workers]
EOM

for i in `seq 2 $1`; do
cat <<EOM >> /etc/ansible/hosts
10.10.20.$i ansible_ssh_extra_args='-o StrictHostKeyChecking=no' ansible_python_interpreter=/usr/bin/python3
EOM
done

#-------------------------------

cd ~
cp Distrinet/mininet/mininet/provision/playbooks/install-lxd.yml ./
cp ~/Distrinet/mininet/mininet/provision/playbooks/configure-lxd-no-clustering.yml ./
ansible-playbook ~/install-lxd.yml
ansible-playbook ~/configure-lxd-no-clustering.yml

cd ~/.distrinet
key=`cat ~/.ssh/id_rsa.pub`
cat <<EOM > conf.yml
---


ssh:
  pub_id: "$key"
  user: "root"
  client_keys: ["/root/.ssh/id_rsa"]
  bastion: "Bastion host IP 'xxx.xxx.xxx.xxx'"

aws:
  region: "eu-central-1"
  user: "ubuntu"
  volumeSize: "8"
  image_name: "ubuntu/images/hvm-ssd/ubuntu-bionic-18.04-amd64-server-20190722.1"
  key_name_aws: "id_rsa"
  network_acl:
    - IpProtocol: "-1"
      FromPort: 1
      ToPort: 65353
      IpRanges:
        - CidrIp: "0.0.0.0/0"

g5k:
  g5k_user: "your username"
  g5k_password: "your password"
  image_name: "ubuntu1804-x64-python3"
  location: "nancy"
  cluster: "grisou"

cluster:
  user: "root"

mapper:
  physical_infrastructure_path: "PATH TO JSON FILE (do not include .json)"
  cloud_instances_prices: "PATH TO JSON FILE (do not include .json)"

EOM

