#!/bin/sh

# Copyright (c) 2006 Red Hat, Inc. All rights reserved. This copyrighted material 
# is made available to anyone wishing to use, modify, copy, or
# redistribute it subject to the terms and conditions of the GNU General
# Public License v.2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Author: Bill Peck, Gurhan Ozen

. /usr/bin/rhts-environment.sh
. /usr/lib/beakerlib/beakerlib.sh

if [ -z "$HOSTNAME" ]; then
    hostname=$(hostname)
else
    hostname=$HOSTNAME
fi
if [ -z "$server" ]; then
    server="http://$LAB_CONTROLLER:8000/server"
fi

rlJournalStart
    rlPhaseStartSetup
        rlRun "modprobe kvm" 
        # Its ok for the vendor specific  modprobes to fail..
	rlRun "modprobe kvm_amd" 0,1
	rlRun "modprobe kvm_intel" 0,1
	rlRun "yum -y install smolt"
	rlAssertRpm "smolt"
    rlPhaseEnd

    rlPhaseStartTest
	rlRun "./push-inventory.py --server $server -h $hostname"
	rlRun "./pushInventory.py --server $server -h $hostname"
    rlPhaseEnd
rlJournalPrintText
rlJournalEnd