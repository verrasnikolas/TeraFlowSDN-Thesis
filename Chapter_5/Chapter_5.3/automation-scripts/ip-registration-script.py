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
# Αφού στέλνουμε ρυθμίσεις συσκευής, μιλάμε ΜΟΝΟ στο DeviceService!
DEVICE_SERVICE_PORT = "2020"  

# --- 2. IP ADDRESS PLAN ---
IP_PLAN = {
    "spine1": {
        "Loopback0": ("10.0.0.3", 32),
        "Ethernet1": ("10.0.1.0", 31),
        "Ethernet2": ("10.0.1.2", 31)
    },
    "leaf1": {
        "Loopback0": ("10.0.0.1", 32),
        "Ethernet1": ("10.0.1.1", 31)
    },
    "leaf2": {
        "Loopback0": ("10.0.0.2", 32),
        "Ethernet1": ("10.0.1.3", 31)
    }
}

def create_ip_config_rule(interface_name, ip_address, prefix_length):
    """
    Δημιουργεί ένα ConfigRule χρησιμοποιώντας το abstraction του 
    OpenConfig driver.
    """
    resource_key = f"/interface[{interface_name}]/subinterface[0]"
    
    # Προσθέσαμε το "name" στο JSON payload για να μην "σκάει" το template του TFS
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
    # Δημιουργία του gRPC Channel ΑΠΕΥΘΕΙΑΣ στο DeviceService (2020)
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