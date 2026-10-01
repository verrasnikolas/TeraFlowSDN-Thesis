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
    "spine1": "172.30.30.10",
    "leaf1":  "172.30.30.11",
    "leaf2":  "172.30.30.12"
}

# Εδώ προσθέσαμε το 'ip routing' και το 'address-family ipv4 unicast'
ISIS_CONFIGS = {
    "spine1": [
        "ip routing",
        "router isis FABRIC",
        "net 49.0001.0000.0000.0003.00",
        "is-type level-2",
        "address-family ipv4 unicast",
        "interface Ethernet1",
        "isis enable FABRIC",
        "interface Ethernet2",
        "isis enable FABRIC",
        "interface Loopback0",
        "isis enable FABRIC",
        "isis passive"
    ],
    "leaf1": [
        "ip routing",
        "router isis FABRIC",
        "net 49.0001.0000.0000.0001.00",
        "is-type level-2",
        "address-family ipv4 unicast",
        "interface Ethernet1",
        "isis enable FABRIC",
        "interface Loopback0",
        "isis enable FABRIC",
        "isis passive"
    ],
    "leaf2": [
        "ip routing",
        "router isis FABRIC",
        "net 49.0001.0000.0000.0002.00",
        "is-type level-2",
        "address-family ipv4 unicast",
        "interface Ethernet1",
        "isis enable FABRIC",
        "interface Loopback0",
        "isis enable FABRIC",
        "isis passive"
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