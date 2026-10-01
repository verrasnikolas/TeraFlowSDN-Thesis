from netmiko import ConnectHandler
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

arista_creds = {
    "device_type": "arista_eos",
    "username": "admin",
    "password": "admin",
    "secret": "", 
    "port": 22,
    "fast_cli": False, 
}

DEVICES = {
    "superspine1": "172.30.30.2", 
    "superspine2": "172.30.30.3",  
    "spine1": "172.30.30.11",
    "spine2": "172.30.30.12",
    "spine3": "172.30.30.13",
    "spine4": "172.30.30.14",
    "leaf1":  "172.30.30.21",
    "leaf2":  "172.30.30.22",
    "leaf3":  "172.30.30.23",
    "leaf4":  "172.30.30.24"
}

ISIS_CONFIGS = {
    # ================= CORE (LEVEL-2 ONLY) =================
    "superspine1": [
        "ip routing",
        "router isis FABRIC",
        "net 49.0000.0100.0000.0001.00",
        "is-type level-2",
        "address-family ipv4 unicast",
        "interface Ethernet1", "isis enable FABRIC", "isis network point-to-point",
        "interface Ethernet2", "isis enable FABRIC", "isis network point-to-point",
        "interface Loopback0", "isis enable FABRIC", "isis passive"
    ],
    "superspine2": [
        "ip routing",
        "router isis FABRIC",
        "net 49.0000.0100.0000.0002.00",
        "is-type level-2",
        "address-family ipv4 unicast",
        "interface Ethernet1", "isis enable FABRIC", "isis network point-to-point",
        "interface Ethernet2", "isis enable FABRIC", "isis network point-to-point",
        "interface Loopback0", "isis enable FABRIC", "isis passive"
    ],

    # ================= POD 1 SPINES (LEVEL-1-2) =================
    "spine1": [
        "ip routing",
        "ip prefix-list LOOPBACKS permit 10.0.0.0/24 eq 32",
        "route-map STRICT_LEAK permit 10",
        "match ip address prefix-list LOOPBACKS",
        "exit",
        "router isis FABRIC",
        "net 49.0001.0100.0000.0011.00",
        "is-type level-1-2",
        "address-family ipv4 unicast",
        "redistribute isis level-2 into level-1 route-map STRICT_LEAK",
        "exit",
        "interface Ethernet1", "isis enable FABRIC", "isis network point-to-point",
        "interface Ethernet2", "isis enable FABRIC", "isis network point-to-point",
        "interface Ethernet3", "isis enable FABRIC", "isis network point-to-point",
        "interface Loopback0", "isis enable FABRIC", "isis passive"
    ],
    "spine2": [
        "ip routing",
        "ip prefix-list LOOPBACKS permit 10.0.0.0/24 eq 32",
        "route-map STRICT_LEAK permit 10",
        "match ip address prefix-list LOOPBACKS",
        "exit",
        "router isis FABRIC",
        "net 49.0001.0100.0000.0012.00",
        "is-type level-1-2",
        "address-family ipv4 unicast",
        "redistribute isis level-2 into level-1 route-map STRICT_LEAK",
        "exit",
        "interface Ethernet1", "isis enable FABRIC", "isis network point-to-point",
        "interface Ethernet2", "isis enable FABRIC", "isis network point-to-point",
        "interface Ethernet3", "isis enable FABRIC", "isis network point-to-point",
        "interface Loopback0", "isis enable FABRIC", "isis passive"
    ],

    # ================= POD 2 SPINES (LEVEL-1-2) =================
    "spine3": [
        "ip routing",
        "ip prefix-list LOOPBACKS permit 10.0.0.0/24 eq 32",
        "route-map STRICT_LEAK permit 10",
        "match ip address prefix-list LOOPBACKS",
        "exit",
        "router isis FABRIC",
        "net 49.0002.0100.0000.0013.00",
        "is-type level-1-2",
        "address-family ipv4 unicast",
        "redistribute isis level-2 into level-1 route-map STRICT_LEAK",
        "exit",
        "interface Ethernet1", "isis enable FABRIC", "isis network point-to-point",
        "interface Ethernet2", "isis enable FABRIC", "isis network point-to-point",
        "interface Ethernet3", "isis enable FABRIC", "isis network point-to-point",
        "interface Loopback0", "isis enable FABRIC", "isis passive"
    ],
    "spine4": [
        "ip routing",
        "ip prefix-list LOOPBACKS permit 10.0.0.0/24 eq 32",
        "route-map STRICT_LEAK permit 10",
        "match ip address prefix-list LOOPBACKS",
        "exit",
        "router isis FABRIC",
        "net 49.0002.0100.0000.0014.00",
        "is-type level-1-2",
        "address-family ipv4 unicast",
        "redistribute isis level-2 into level-1 route-map STRICT_LEAK",
        "exit",
        "interface Ethernet1", "isis enable FABRIC", "isis network point-to-point",
        "interface Ethernet2", "isis enable FABRIC", "isis network point-to-point",
        "interface Ethernet3", "isis enable FABRIC", "isis network point-to-point",
        "interface Loopback0", "isis enable FABRIC", "isis passive"
    ],

    # ================= POD 1 LEAVES (LEVEL-1 ONLY) =================
    "leaf1": [
        "ip routing",
        "router isis FABRIC",
        "net 49.0001.0100.0000.0021.00",
        "is-type level-1",
        "address-family ipv4 unicast",
        "interface Ethernet1", "isis enable FABRIC", "isis network point-to-point",
        "interface Ethernet3", "isis enable FABRIC", "isis network point-to-point",
        "interface Loopback0", "isis enable FABRIC", "isis passive"
    ],
    "leaf2": [
        "ip routing",
        "router isis FABRIC",
        "net 49.0001.0100.0000.0022.00",
        "is-type level-1",
        "address-family ipv4 unicast",
        "interface Ethernet1", "isis enable FABRIC", "isis network point-to-point",
        "interface Ethernet3", "isis enable FABRIC", "isis network point-to-point",
        "interface Loopback0", "isis enable FABRIC", "isis passive"
    ],

    # ================= POD 2 LEAVES (LEVEL-1 ONLY) =================
    "leaf3": [
        "ip routing",
        "router isis FABRIC",
        "net 49.0002.0100.0000.0023.00",
        "is-type level-1",
        "address-family ipv4 unicast",
        "interface Ethernet1", "isis enable FABRIC", "isis network point-to-point",
        "interface Ethernet3", "isis enable FABRIC", "isis network point-to-point",
        "interface Loopback0", "isis enable FABRIC", "isis passive"
    ],
    "leaf4": [
        "ip routing",
        "router isis FABRIC",
        "net 49.0002.0100.0000.0024.00",
        "is-type level-1",
        "address-family ipv4 unicast",
        "interface Ethernet1", "isis enable FABRIC", "isis network point-to-point",
        "interface Ethernet3", "isis enable FABRIC", "isis network point-to-point",
        "interface Loopback0", "isis enable FABRIC", "isis passive"
    ]
}

def push_isis_via_ssh():
    for name, ip in DEVICES.items():
        logging.info(f"Σύνδεση μέσω SSH στο {name} ({ip})...")
        device_params = arista_creds.copy()
        device_params["host"] = ip
        
        try:
            net_connect = ConnectHandler(**device_params)
            
            # Μπαίνουμε ρητά σε Enable mode
            net_connect.enable()
            
            logging.info(f"Επιτυχής σύνδεση στο {name}. Αποστολή ρυθμίσεων IS-IS...")
            
            # Στέλνουμε τις εντολές (το read_timeout δίνει χρόνο στο Containerlab)
            output = net_connect.send_config_set(ISIS_CONFIGS[name], read_timeout=15)
            
            # Save configuration
            net_connect.save_config()
            net_connect.disconnect()
            
            logging.info(f"[ΕΠΙΤΥΧΙΑ] Το IS-IS ρυθμίστηκε πλήρως στον {name}.\n")
        except Exception as e:
            logging.error(f"[ΣΦΑΛΜΑ] Αποτυχία στο {name}: {str(e)}\n")

if __name__ == "__main__":
    push_isis_via_ssh()