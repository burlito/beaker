#if $varExists('sysprofile')
#set listed_snippet_profiles = $getVar('sysprofile','').split(';')
#for $snippet_profile in $listed_snippet_profiles
# Snippet Profile: $snippet_profile
$SNIPPET($snippet_profile)
#end for
#else
#if $varExists('method') and $mgmt_parameters.has_key("method_%s" % $method) and \
 $tree.find("nfs://") != -1
$SNIPPET("install_method")
#else
## Do it the way the tree was imported
url --url=$tree
#end if

#if $getVar('system_name', '') != '' and $getVar('manual', 'False') == 'False'
authconfig  --enableshadow  --enablemd5
# System bootloader configuration
bootloader --location=mbr #slurp
#if $getVar('kernel_options_post','') != ''
    --append="$kernel_options_post"
#end if

# Use text mode install
$getVar('mode','text')
$SNIPPET("network")
## Firewall configuration
## firewall in kickstart metadata will enable the firewall
## firewall=22:tcp,80:tcp will enable the firewall with ports 22 and 80 open.
## always allow port 12432 so that beah harness will support multihost
firewall #slurp
#if $getVar('firewall', 'disabled') == 'disabled':
--disabled
#else
--enabled --port=12432:tcp #slurp
#if $getVar('firewall', '') != '':
,$getVar('firewall')
#end if
#end if

# Run the Setup Agent on first boot
firstboot --disable
# System keyboard
keyboard us
mouse none
# System language
lang $getVar('lang','en_US.UTF-8')
langsupport --default $getVar('lang', 'en_US.UTF-8') $getVar('lang','en_US.UTF-8')
$yum_repo_stanza
reboot
#Root password
rootpw --iscrypted $getVar('password', $default_password_crypted)
#if $getVar('skipx','') != ''
# Do not configure the X Window System
skipx
#end if
# System timezone
timezone  America/New_York
# Install OS instead of upgrade
install

$SNIPPET("rhts_scsi_ethdevices")
$SNIPPET("rhts_partitions")
$SNIPPET("RedHatEnterpriseLinux3")
$SNIPPET("system")

%packages --resolvedeps --ignoremissing
$SNIPPET("rhts_packages")

#end if
#end if
%pre
PATH=/usr/bin:$PATH
$SNIPPET("rhts_pre")
$SNIPPET("RedHatEnterpriseLinux3_pre")
$SNIPPET("system_pre")

%post
PATH=/usr/bin:$PATH
$SNIPPET("rhts_post")
$SNIPPET("RedHatEnterpriseLinux3_post")
$SNIPPET("system_post")

#if $getVar('ks_appends', '') != '':
$SNIPPET("ks_appends")
#end if