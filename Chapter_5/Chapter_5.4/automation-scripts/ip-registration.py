import sys
import os
import grpc
import json
import logging

# Προσθέτει το tfs-ctrl στο path της Python για να βρει τα Protobufs
sys.path.append(os.path.expanduser("~/tfs-ctrl/src"))
sys.path.append(os.path.expanduser("~/tfs-ctrl"))

# Τα imports των Protobufs του TeraFlowSDN
from common.proto.context_pb2 import Device, ConfigRule, ConfigActionEnum
from common.proto.device_pb2_grpc import DeviceServiceStub

# --- 1. ΡΥΘΜΙΣΕΙΣ ΣΥΝΔΕΣΗΣ ---
TFS_GRPC_ADDRESS = "127.0.0.1" 
DEVICE_SERVICE_PORT = "2020"  

# --- 2. UPDATED 5-STAGE CLOS IP ADDRESS PLAN ---
IP_PLAN = {
    # --- SuperSpines (Core Stage) ---
    "superspine1": {
        "Loopback0": ("10.0.0.1", 32),
        "Ethernet1": ("10.100.10.0", 31),  # -> spine1:Ethernet3
        "Ethernet2": ("10.100.10.4", 31)   # -> spine3:Ethernet3
    },
    "superspine2": {
        "Loopback0": ("10.0.0.2", 32),
        "Ethernet1": ("10.100.10.2", 31),  # -> spine2:Ethernet3
        "Ethernet2": ("10.100.10.6", 31)   # -> spine4:Ethernet3
    },

    # --- Spines ---
    "spine1": {
        "Loopback0": ("10.0.0.11", 32),
        "Ethernet1": ("10.100.20.1", 31),  # -> leaf1:Ethernet1
        "Ethernet2": ("10.100.20.5", 31),  # -> leaf2:Ethernet1
        "Ethernet3": ("10.100.10.1", 31)   # -> superspine1:Ethernet1
    },
    "spine2": {
        "Loopback0": ("10.0.0.12", 32),
        "Ethernet1": ("10.100.20.3", 31),  # -> leaf1:Ethernet3
        "Ethernet2": ("10.100.20.7", 31),  # -> leaf2:Ethernet3
        "Ethernet3": ("10.100.10.3", 31)   # -> superspine2:Ethernet1
    },
    "spine3": {
        "Loopback0": ("10.0.0.13", 32),
        "Ethernet1": ("10.100.30.1", 31),  # -> leaf3:Ethernet1
        "Ethernet2": ("10.100.30.5", 31),  # -> leaf4:Ethernet1
        "Ethernet3": ("10.100.10.5", 31)   # -> superspine1:Ethernet2
    },
    "spine4": {
        "Loopback0": ("10.0.0.14", 32),
        "Ethernet1": ("10.100.30.3", 31),  # -> leaf3:Ethernet3
        "Ethernet2": ("10.100.30.7", 31),  # -> leaf4:Ethernet3
        "Ethernet3": ("10.100.10.7", 31)   # -> superspine2:Ethernet2
    },

    # --- Leaves ---
    "leaf1": {
        "Loopback0": ("10.0.0.21", 32),
        "Ethernet1": ("10.100.20.0", 31),  # -> spine1:Ethernet1
        "Ethernet3": ("10.100.20.2", 31)   # -> spine2:Ethernet1
    },
    "leaf2": {
        "Loopback0": ("10.0.0.22", 32),
        "Ethernet1": ("10.100.20.4", 31),  # -> spine1:Ethernet2
        "Ethernet3": ("10.100.20.6", 31)   # -> spine2:Ethernet2
    },
    "leaf3": {
        "Loopback0": ("10.0.0.23", 32),
        "Ethernet1": ("10.100.30.0", 31),  # -> spine3:Ethernet1
        "Ethernet3": ("10.100.30.2", 31)   # -> spine4:Ethernet1
    },
    "leaf4": {
        "Loopback0": ("10.0.0.24", 32),
        "Ethernet1": ("10.100.30.4", 31),  # -> spine3:Ethernet2
        "Ethernet3": ("10.100.30.6", 31)   # -> spine4:Ethernet2
    }
}

def create_ip_config_rule(interface_name, ip_address, prefix_length):
    """
    Δημιουργεί ένα ConfigRule χρησιμοποιώντας το abstraction του 
    OpenConfig driver.
    """
    resource_key = f"/interface[{interface_name}]/subinterface[0]"
    
    resource_value = {
        "name": interface_name,
        "index": 0,
        "address_ip": ip_address,
        "address_prefix": prefix_length
    }

    config_rule = ConfigRule()
    config_rule.action = ConfigActionEnum.CONFIGACTION_SET
    config_rule.custom.resource_key = resource_key
    config_rule.custom.resource_value = json.dumps(resource_value)
    
    return config_rule

def push_configs_to_tfs():
    # Δημιουργία gRPC Channel στο DeviceService (2020)
    channel = grpc.insecure_channel(f"{TFS_GRPC_ADDRESS}:{DEVICE_SERVICE_PORT}")
    device_client = DeviceServiceStub(channel)

    for device_uuid, interfaces in IP_PLAN.items():
        logging.info(f"Προετοιμασία ρυθμίσεων για τη συσκευή: {device_uuid}")
        
        device_req = Device()
        device_req.device_id.device_uuid.uuid = device_uuid
        
        for iface, (ip, prefix) in interfaces.items():
            rule = create_ip_config_rule(iface, ip, prefix)
            device_req.device_config.config_rules.append(rule)
            logging.info(f"  -> Έτοιμο rule για {iface}: {ip}/{prefix}")

        try:
            logging.info(f"Αποστολή στο TeraFlowSDN για το {device_uuid}...")
            response = device_client.ConfigureDevice(device_req)
            logging.info(f"[ΕΠΙΤΥΧΙΑ] Η συσκευή {device_uuid} ενημερώθηκε.\n")
        except grpc.RpcError as e:
            logging.error(f"[ΣΦΑΛΜΑ] Αποτυχία για {device_uuid}: {e.details()}\n")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    push_configs_to_tfs()