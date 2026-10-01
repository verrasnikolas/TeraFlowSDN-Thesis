from netmiko import ConnectHandler

# Συσκευές: Αφαιρέσαμε τα περιττά arguments και βάλαμε γερό delay factor
spine1 = {
    'device_type': 'arista_eos',
    'host':   'clab-clos3-spine1',
    'username': 'admin',
    'password': 'admin',
    'port': 22,
    'global_delay_factor': 4,
}

leaf1 = {
    'device_type': 'arista_eos',
    'host':   'clab-clos3-leaf1',
    'username': 'admin',
    'password': 'admin',
    'port': 22,
    'global_delay_factor': 4,
}

leaf2 = {
    'device_type': 'arista_eos',
    'host':   'clab-clos3-leaf2',
    'username': 'admin',
    'password': 'admin',
    'port': 22,
    'global_delay_factor': 4,
}

spine_config = [
    'service routing protocols model multi-agent',
    'router bgp 65000',
    'neighbor EVPN-PEERS peer group',
    'neighbor EVPN-PEERS remote-as 65000',
    'neighbor EVPN-PEERS update-source Loopback0',
    'neighbor EVPN-PEERS route-reflector-client',
    'neighbor EVPN-PEERS send-community',
    'neighbor 10.0.0.1 peer group EVPN-PEERS',
    'neighbor 10.0.0.2 peer group EVPN-PEERS',
    'address-family evpn',
    'neighbor EVPN-PEERS activate',
]

leaf_config = [
    'service routing protocols model multi-agent',
    'router bgp 65000',
    # --- ΠΡΟΣΘΗΚΗ BGP NEIGHBOR (SPINE) ---
    'neighbor 10.0.0.3 remote-as 65000',
    'neighbor 10.0.0.3 update-source Loopback0',
    'neighbor 10.0.0.3 send-community',
    # --- ΤΕΛΟΣ ΠΡΟΣΘΗΚΗΣ ---
    'vlan 10',
    'rd 65000:10010',
    'route-target both 65000:10010',
    'exit',
    # --- ΕΝΕΡΓΟΠΟΙΗΣΗ EVPN ADDRESS FAMILY ---
    'address-family evpn',
    'neighbor 10.0.0.3 activate',
    'exit',
    # --- ΡΥΘΜΙΣΗ VXLAN ---
    'interface Vxlan1',
    'vxlan source-interface Loopback0',
    'vxlan udp-port 4789',
    'vxlan vlan 10 vni 10010'
]

def configure_bgp_evpn(device, config_commands):
    print(f"\n[+] Εκκίνηση παραμετροποίησης BGP EVPN στο: {device['host']}...")
    try:
        net_connect = ConnectHandler(**device)
        net_connect.enable()
        
        # Η "μαγική" παράμετρος: cmd_verify=False
        output = net_connect.send_config_set(config_commands, cmd_verify=False)
        print(output)
        
        net_connect.save_config()
        net_connect.disconnect()
        print(f"[✔] Επιτυχής ολοκλήρωση στο: {device['host']}")
        
    except Exception as e:
        print(f"[✘] Σφάλμα στο {device['host']}: {e}")

if __name__ == "__main__":
    print("=== Έναρξη Day-0 BGP/EVPN Automation ===")
    configure_bgp_evpn(spine1, spine_config)
    configure_bgp_evpn(leaf1, leaf_config)
    configure_bgp_evpn(leaf2, leaf_config)
    print("\n=== Ολοκλήρωση ===")