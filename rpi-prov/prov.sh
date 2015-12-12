#!/usr/bin/env bash


apt-get update
apt-get install -y python-pip git htop


checksum=$(sha256sum ${BASH_SOURCE[0]})


if [ ! -d  /usr/local/src/epifpm ]; then
    git clone https://github.com/Epi10/epifpm /usr/local/src/epifpm
else
    cd /usr/local/src/epifpm
    git pull
fi

new_checksum=$(sha256sum /usr/local/src/epifpm/rpi-prov/prov.sh)

if [ "{$checksum}" != "${new_checksum}" ];then
    chmod a+x /usr/local/src/epifpm/rpi-prov/prov.sh
    /usr/local/src/epifpm/rpi-prov/prov.sh
    exit
fi

## DISABLE ttyAMA0

CHANGE_BOOT_CMDLINE=$(grep ttyAMA0 /boot/cmdline.txt 2>&1 > /dev/null  && echo yes)

grep ttyAMA0 /boot/cmdline.txt 2>&1 > /dev/null  && sed -i 's/console=ttyAMA0,[0-9]*//g' /boot/cmdline.txt

CHANGE_SECURETTY=$(grep ttyAMA0 /etc/securetty 2>&1 > /dev/null  && echo yes)

grep ttyAMA0 /etc/securetty 2>&1 > /dev/null  && sed -i '/ttyAMA0/d' /etc/securetty

### Verify if we need restart

if [ ! -z ${CHANGE_BOOT_CMDLINE} ]; then
    shutdown -r now
fi

if [ ! -z ${CHANGE_SECURETTY} ]; then
    shutdown -r now
fi

exit

apt-get install -y hostapd tcpdump python-pip git htop tcpdump

cat >/etc/hostapd/hostapd.conf  << EOL

interface=wlan0
driver=rtl871xdrv
ssid=epifpm
hw_mode=g
channel=6
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=raspberry
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP

EOL


### CONFIG IPTABLE

iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
iptables -A FORWARD -i eth0 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT
iptables -A FORWARD -i wlan0 -o eth0 -j ACCEPT

iptables-save > /etc/iptables.ipv4.nat

cat >/etc/sysctl.conf  << EOL

#kernel.domainname = example.com

# Uncomment the following to stop low-level messages on console
kernel.printk = 3 4 1 3

##############################################################3
# Functions previously found in netbase
#

# Uncomment the next two lines to enable Spoof protection (reverse-path filter)
# Turn on Source Address Verification in all interfaces to
# prevent some spoofing attacks
#net.ipv4.conf.default.rp_filter=1
#net.ipv4.conf.all.rp_filter=1

# Uncomment the next line to enable TCP/IP SYN cookies
# See http://lwn.net/Articles/277146/
# Note: This may impact IPv6 TCP sessions too
#net.ipv4.tcp_syncookies=1

# Uncomment the next line to enable packet forwarding for IPv4
net.ipv4.ip_forward=1

# Uncomment the next line to enable packet forwarding for IPv6
#  Enabling this option disables Stateless Address Autoconfiguration
#  based on Router Advertisements for this host
#net.ipv6.conf.all.forwarding=1


###################################################################
# Additional settings - these settings can improve the network
# security of the host and prevent against some network attacks
# including spoofing attacks and man in the middle attacks through
# redirection. Some network environments, however, require that these
# settings are disabled so review and enable them as needed.
#
# Do not accept ICMP redirects (prevent MITM attacks)
#net.ipv4.conf.all.accept_redirects = 0
#net.ipv6.conf.all.accept_redirects = 0
# _or_
# Accept ICMP redirects only for gateways listed in our default
# gateway list (enabled by default)
# net.ipv4.conf.all.secure_redirects = 1
#
# Do not send ICMP redirects (we are not a router)
#net.ipv4.conf.all.send_redirects = 0
#
# Do not accept IP source route packets (we are not a router)
#net.ipv4.conf.all.accept_source_route = 0
#net.ipv6.conf.all.accept_source_route = 0
#
# Log Martian Packets
#net.ipv4.conf.all.log_martians = 1
#

# rpi tweaks
vm.swappiness=1
vm.min_free_kbytes = 8192
EOL

### save interface file

cat >/etc/network/interfaces << EOL
auto lo
iface lo inet loopback

auto eth0
allow-hotplug eth0
iface eth0 inet manual

iface wlan0 inet static
    address 192.168.42.1
    netmask 255.255.255.0


up iptables-restore < /etc/iptables.ipv4.nat


EOL

#delete the pseudo tty so we can use it
sed -i '/ttyAMA0/d' /etc/inittab
## Restart device

shutdown -r now
