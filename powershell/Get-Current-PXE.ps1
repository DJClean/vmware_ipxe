param(
  [Parameter(Mandatory=$true)][string]$vcenter,
  [Parameter(Mandatory=$true)][string]$version,
  [Parameter(Mandatory=$true)][string]$template,
  [Parameter(Mandatory=$true)][string]$datacenter
)

function Test-IPv4MaskString {
  <#
  .SYNOPSIS
  Tests whether an IPv4 network mask string (e.g., "255.255.255.0") is valid.

  .DESCRIPTION
  Tests whether an IPv4 network mask string (e.g., "255.255.255.0") is valid.

  .PARAMETER MaskString
  Specifies the IPv4 network mask string (e.g., "255.255.255.0").
  #>
  param(
    [parameter(Mandatory=$true)]
    [String] $MaskString
  )
  $validBytes = '0|128|192|224|240|248|252|254|255'
  $maskPattern = ('^((({0})\.0\.0\.0)|'      -f $validBytes) +
         ('(255\.({0})\.0\.0)|'      -f $validBytes) +
         ('(255\.255\.({0})\.0)|'    -f $validBytes) +
         ('(255\.255\.255\.({0})))$' -f $validBytes)
  $MaskString -match $maskPattern
}

function ConvertTo-IPv4MaskBits {
  <#
  .SYNOPSIS
  Returns the number of bits (0-32) in a network mask string (e.g., "255.255.255.0").

  .DESCRIPTION
  Returns the number of bits (0-32) in a network mask string (e.g., "255.255.255.0").

  .PARAMETER MaskString
  Specifies the IPv4 network mask string (e.g., "255.255.255.0").
  #>
  param(
    [parameter(Mandatory=$true)]
    [ValidateScript({Test-IPv4MaskString $_})]
    [String] $MaskString
  )
  $mask = ([IPAddress] $MaskString).Address
  for ( $bitCount = 0; $mask -ne 0; $bitCount++ ) {
    $mask = $mask -band ($mask - 1)
  }
  $bitCount
}

$Host_List =@()

Foreach ($VMHost in (Get-Datacenter $datacenter | Get-VMHost | Sort-Object Name)) {

  if ($VMhost.Parent.GetType().Name -ne "FolderImpl") {
    continue
  }

  $cluster = "Standalone"
  $esxcli = Get-Esxcli -VMHost $VMHost -V2
  $mgmtinterface = $VMHost | Get-VMHostNetworkAdapter | Where { $_.ManagementTrafficEnabled -eq "True" } | Select Name
  $nwconf = $EsxCli.network.ip.interface.ipv4.get.Invoke() | Where { $_.Name -eq $mgmtinterface.Name }
  $vmnic = ($EsxCli.network.vswitch.standard.list.Invoke() | Where { $_.Name -eq "vSwitch0" }).Uplinks  -Join ","
  $dns = ($EsxCli.network.ip.dns.server.list.Invoke()).DNSServers -Join ","
  $vmhostip = $nwconf.IPv4Address
  $vmhostsubnet = ConvertTo-IPv4MaskBits $nwconf.IPv4Netmask
  $gateway = ($EsxCli.network.ip.route.ipv4.list.Invoke() | Where { $_.Network -eq "default" } ).Gateway
  $vmhostipinterface = "${vmhostip}/${vmhostsubnet}"
  $vlan =($VMHost | Get-VirtualPortGroup -Name $(($VMHost | Get-VMHostNetworkAdapter -Name $mgmtinterface.Name).PortgroupName)).VlanId

  $HostInfo = New-Object PSObject
  $HostInfo | Add-Member -Name "VCENTER" -Value $vcenter -MemberType NoteProperty
  $HostInfo | Add-Member -Name "CLUSTER" -Value $cluster -MemberType NoteProperty
  $HostInfo | Add-Member -Name "HOST" -Value $VMHost.Name -MemberType NoteProperty
  $HostInfo | Add-Member -Name "IP" -Value $vmhostipinterface -MemberType NoteProperty
  $HostInfo | Add-Member -Name "GATEWAY" -Value $gateway -MemberType NoteProperty
  $HostInfo | Add-Member -Name "DNS" -Value $dns -MemberType NoteProperty
  $HostInfo | Add-Member -Name "VLAN" -Value $vlan -MemberType NoteProperty
  $HostInfo | Add-Member -Name "VMNIC" -Value $vmnic -MemberType NoteProperty
  $HostInfo | Add-Member -Name "VERSION" -Value $version -MemberType NoteProperty
  $HostInfo | Add-Member -Name "TEMPLATE" -Value $template -MemberType Noteproperty

  $Host_List += $HostInfo

}

$Host_List
