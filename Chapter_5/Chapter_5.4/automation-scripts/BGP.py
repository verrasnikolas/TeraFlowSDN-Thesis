from netmiko import ConnectHandler
import logging

# Απενεργοποίηση των περιττών netmiko logs για πιο καθαρό output στο terminal
logging.getLogger("netmiko").setLevel(logging.WARNING)

arista_creds = {
    "device_type": "arista_eos",
    "username": "admin",
    "password": "admin",
    "port": 22,
    "global_delay_factor": 4, 
}

# Μόνο τα Leaves συμμετέχουν στο BGP EVPN
LEAVES = {
    "leaf1": {"ip": "172.30.30.21", "loopback": "10.0.0.21"},
    "leaf2": {"ip": "172.30.30.22", "loopback": "10.0.0.22"},
    "leaf3": {"ip": "172.30.30.23", "loopback": "10.0.0.23"},
    "leaf4": {"ip": "172.30.30.24", "loopback": "10.0.0.24"},
}

ACTIVE_SERVICE_LEAVES = ["leaf1", "leaf4"]

def generate_evpn_config(leaf_name):
    my_loopback = LEAVES[leaf_name]["loopback"]
    
    # --- Βασική παραμετροποίηση BGP EVPN για ΟΛΑ τα Leaves ---
    config = [
        "service routing protocols model multi-agent",
        "router bgp 65000",
        f"router-id {my_loopback}",
        "no bgp default ipv4-unicast",
        "neighbor EVPN-PEERS peer group",
        "neighbor EVPN-PEERS remote-as 65000",
        "neighbor EVPN-PEERS update-source Loopback0",
        "neighbor EVPN-PEERS send-community extended",
    ]
    
    # Full Mesh iBGP: Προσθήκη όλων των άλλων Leaves
    for name, data in LEAVES.items():
        if name != leaf_name:
            config.append(f"neighbor {data['loopback']} peer group EVPN-PEERS")
            
    config.extend([
        "address-family evpn",
        "neighbor EVPN-PEERS activate",
        "exit",
        "exit"
    ])
    
    # --- Παραμετροποίηση VXLAN & MAC-VRF ΜΟΝΟ για τα ενεργά Leaves ---
    if leaf_name in ACTIVE_SERVICE_LEAVES:
        config.extend([
            # 1. Global Config: Ορισμός L2 VLAN & Access Port
            "vlan 10",
            "name TENANT_A_L2VPN",
            "exit",
            "interface Ethernet2",
            "switchport mode access",
            "switchport access vlan 10",
            "exit",
            
            # 2. Overlay Config: VXLAN VTEP Interface
            "interface Vxlan1",
            "vxlan source-interface Loopback0",
            "vxlan udp-port 4789",
            "vxlan vlan 10 vni 10010",
            "exit",

            # 3. Control Plane Config: BGP MAC-VRF για το VLAN 10
            "router bgp 65000",
            "vlan 10",
            "rd auto",
            "route-target both 10010:10010",
            "redistribute learned",
            "exit",
            "exit"
        ])
        
    return config

def configure_bgp_evpn():
    print("=== Έναρξη Day-0 BGP/EVPN Automation για 5-Stage Clos ===")
    
    for leaf_name, data in LEAVES.items():
        print(f"\n[+] Εκκίνηση παραμετροποίησης στο: {leaf_name} ({data['ip']})...")
        device_params = arista_creds.copy()
        device_params["host"] = data["ip"]
        
        commands = generate_evpn_config(leaf_name)
        
        try:
            net_connect = ConnectHandler(**device_params)
            net_connect.enable()
            
            output = net_connect.send_config_set(commands, cmd_verify=False)
            print(output)
            
            net_connect.save_config()
            net_connect.disconnect()
            print(f"[✔] Επιτυχής ολοκλήρωση στο: {leaf_name}")
            
        except Exception as e:
            print(f"[✘] Σφάλμα στο {leaf_name}: {e}")
            
    print("\n=== Ολοκλήρωση ===")

if __name__ == "__main__":
    configure_bgp_evpn()