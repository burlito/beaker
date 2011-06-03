if options[:vmrun]
  vmserver = options[:vmrun]
  # VM snapshots are named to match the type of Puppet install;
  # the VMs have specific configs to test each install type
  # 'git' = install from git
  # 'pe' = install Puppet Enterpise
  snapshot = options[:type]
  step "Reverting to #{snapshot} on VM Server #{vmserver}"

  vminfo_h = Hash.new
  # get list of VMs
  hlist=`lib/virsh_exec.exp #{vmserver} list`

  # interate through the VMs...
  hlist.split("\n").each do |line|
    Log.debug("VM: considering '#{line}'")
    hosts.each do |host|  # only add VMs that match a hostname
      if line.index(host)
        if line =~ /(\d+\s\S+)\s/ then
          k,v = line.split(" ")
          vminfo_h[v]=k
        end
      end
    end
  end

  # Revert the VMs
  vminfo_h.each do |key, val|
    step "Reverting VM: #{key} with Domain: #{val} on VM server #{vmserver}"
    system("lib/virsh_exec.exp #{vmserver} snapshot-revert #{val} #{snapshot}")
  end
end