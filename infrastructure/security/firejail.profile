# Firejail profile for Req2Run benchmark execution
# Alternative to nsjail for systems where firejail is preferred

# Basic configuration
name req2run_sandbox
hostname sandbox

# Resource limits
rlimit-as 2147483648  # 2GB virtual memory
rlimit-cpu 300  # 5 minutes CPU time  
rlimit-fsize 104857600  # 100MB max file size
rlimit-nofile 256  # Max open files
nice 5  # Lower priority

# Filesystem
private
private-dev
private-tmp
private-etc alternatives,fonts,ld.so.cache,ld.so.conf,ld.so.conf.d,locale,locale.alias,locale.conf,localtime,mime.types,passwd,group,resolv.conf,host.conf,hosts,nsswitch.conf

# Whitelist application directory
mkdir ${HOME}/app
whitelist ${HOME}/app
read-write ${HOME}/app

# Blacklist sensitive directories
blacklist /boot
blacklist /media
blacklist /mnt
blacklist /opt
blacklist /root
blacklist /srv
blacklist /sys
blacklist /var

# Network
net none  # No network access
# For problems requiring network:
# net eth0
# netfilter /etc/firejail/webserver.net
# protocol unix,inet,inet6

# Security features
caps.drop all
nonewprivs
noroot
seccomp
x11 none
nodbus
nosound
notv
nodvd
no3d

# Process limits
cpu 2  # Max 2 CPUs
timeout 00:05:00  # 5 minutes timeout

# Memory limits
memory-deny-write-execute

# Seccomp filters
seccomp.drop @clock,@cpu-emulation,@debug,@module,@mount,@obsolete,@privileged,@raw-io,@reboot,@resources,@swap

# Additional restrictions for languages

# Python specific
noblacklist /usr/bin/python3
noblacklist /usr/lib/python3*
noblacklist /usr/local/lib/python3*

# Node.js specific  
noblacklist /usr/bin/node
noblacklist /usr/lib/node_modules

# Go specific
noblacklist /usr/local/go
noblacklist ${HOME}/go

# Shell
shell none

# Environment filtering
env PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
env LANG=C.UTF-8
env LC_ALL=C.UTF-8

# Deterministic mode
deterministic-exit-code
machine-id

# Join existing sandbox or create new
# join-or-start req2run_sandbox