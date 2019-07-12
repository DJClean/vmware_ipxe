#Accept VMware License agreement
accepteula

# Set the root password
rootpw VMware1!

# Install ESXi on the first disk (Local first, then remote then USB)

install --firstdisk=usb,local --overwritevmfs --novmfsondisk

# Set the network
network --bootproto=static --device=$UPLINK0 --ip=$IPADDRESS --gateway=$GATEWAY --nameserver="$DNS" --netmask=$NETMASK --vlanid=$VLAN --addvmportgroup=0 --hostname=$VMHOST

# reboot the host after installation is completed
reboot

# run the following command only on the firstboot
%firstboot --interpreter=busybox

# enable & start remote ESXi Shell (SSH)
vim-cmd hostsvc/enable_ssh
vim-cmd hostsvc/start_ssh

# supress ESXi Shell shell warning - Thanks to Duncan (http://www.yellow-bricks.com/2011/07/21/esxi-5-suppressing-the-localremote-shell-warning/)
esxcli system settings advanced set -o /UserVars/SuppressShellWarning -i 1

# Add extra interface to vSwitch0
esxcli network vswitch standard uplink add --uplink-name $UPLINK1 --vswitch-name vSwitch0

# Set vSwitch0 Fail-over Policy
esxcli network vswitch standard policy failover set --active-uplinks $UPLINK0,$UPLINK1 --vswitch-name vSwitch0

#Disable ipv6
esxcli network ip set --ipv6-enabled=0

# restart a last time
reboot
