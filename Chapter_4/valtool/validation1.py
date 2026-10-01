import json
from os import link
import sys
import re
from attr import attrs
import grpc
from jsonschema import Draft7Validator
import socket

# importing gRPC files (if available)
try:
    from tfs_grpc import context_pb2
    from tfs_grpc import context_pb2_grpc
    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False
    print("[!] Warning: tfs_grpc folder not found. Script is in Offline Mode.")

# REGEX Patterns
IPV4_REGEX = re.compile(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$")
MAC_REGEX = re.compile(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")

def check_tcp_port(ip, port, timeout=1.0):
    "Checks if a TCP port is open on a given IP address."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((ip, int(port)))
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

class TopologyPreValidator:
    def __init__(self, schema_path):
        with open(schema_path, 'r') as file:
            self.schema = json.load(file)
        self.schema_validator = Draft7Validator(self.schema)
        
        # ==============================================================================
        # State Initialization
        # ==============================================================================
        self.tfs_devices = None      # { device_uuid: device_name }
        self.tfs_endpoints = {}      # { device_uuid: set(endpoint_uuids_or_names) }
        self.tfs_configs = {}        # { device_uuid: list(config_resource_keys) }
        self.tfs_links = {}          # { link_uuid: [endpoint_ids] }
        self.tfs_device_types = None # { device_uuid: device_type }  
        self.tfs_contexts = set()    # stores Context UUIDs, e.g. {'admin'}
        self.tfs_topologies = {}     # stores topologies by context, e.g. {'admin': {'admin-topo'}}
        
        self.tfs_devices = None      # { device_uuid: device_name }
        self.tfs_endpoints = {}      # { device_uuid: set(endpoint_uuids_or_names) }
        
        # State Initialization
        self.fetch_all_tfs_data()

    def fetch_all_tfs_data(self):
        """Fetches ALL the ready data from the TFS without doing duplicate work."""
        if not GRPC_AVAILABLE:
            return
            
        try:
            channel = grpc.insecure_channel('localhost:11010')
            stub = context_pb2_grpc.ContextServiceStub(channel)
            empty_request = context_pb2.Empty()
            
            # 0. Fetching CONTEXTS and TOPOLOGIES from the TFS
            context_id_list = stub.ListContextIds(empty_request, timeout=2.0)
            for ctx_id in context_id_list.context_ids:
                self.tfs_contexts.add(ctx_id.context_uuid.uuid)
                
                # Getting the topologies for the specific context
                topology_id_list = stub.ListTopologyIds(ctx_id, timeout=2.0)
                for topo_id in topology_id_list.topology_ids:
                    ctx_uuid = topo_id.context_id.context_uuid.uuid
                    topo_uuid = topo_id.topology_uuid.uuid
                    
                    if ctx_uuid not in self.tfs_topologies:
                        self.tfs_topologies[ctx_uuid] = set()
                    self.tfs_topologies[ctx_uuid].add(topo_uuid)
                    
            # 1. Fetching DEVICES, ENDPOINTS and CONFIGS
            device_response = stub.ListDevices(empty_request, timeout=2.0)
            self.tfs_devices = {}
            self.tfs_device_types = {}
            for dev in device_response.devices:
                d_uuid = dev.device_id.device_uuid.uuid
                self.tfs_devices[d_uuid] = dev.name
                self.tfs_device_types[d_uuid] = dev.device_type 
                
                # Storing the endpoints and creating a Mapping
                self.tfs_endpoints[d_uuid] = set()
                if not hasattr(self, 'port_name_to_hash'):
                    self.port_name_to_hash = {}
                    
                for ep in dev.device_endpoints:
                    ep_hash = ep.endpoint_id.endpoint_uuid.uuid
                    self.tfs_endpoints[d_uuid].add(ep_hash)
                    if ep.name:
                        self.tfs_endpoints[d_uuid].add(ep.name)
                        self.port_name_to_hash[(d_uuid, ep.name)] = ep_hash
                    else:
                        self.port_name_to_hash[(d_uuid, ep_hash)] = ep_hash
                
                # Storing the configurations (Config Rules)
                self.tfs_configs[d_uuid] = []
                if dev.device_config and dev.device_config.config_rules:
                    for rule in dev.device_config.config_rules:
                        if rule.HasField('custom'):
                            self.tfs_configs[d_uuid].append({
                                "key": rule.custom.resource_key,
                                "value": rule.custom.resource_value
                            })

            # 2. Fetching LINKS (CONNECTIONS)
            link_response = stub.ListLinks(empty_request, timeout=2.0)
            for link in link_response.links:
                l_uuid = link.link_id.link_uuid.uuid
                # Keep linked endpoints
                endpoints_in_link = []
                for ep_id in link.link_endpoint_ids:
                    endpoints_in_link.append({
                        "device": ep_id.device_id.device_uuid.uuid,
                        "endpoint": ep_id.endpoint_uuid.uuid
                    })
                self.tfs_links[l_uuid] = endpoints_in_link

        except grpc.RpcError as e:
            # Print exactly why the connection failed
            print(f"[!] gRPC Error while fetching data: {e.details()}")
            self.tfs_devices = None
            self.tfs_device_types = None

    # ==============================================================================
    # LOGIC CHECKING (WITHOUT gRPC INTEGRATION YET)
    # ==============================================================================
    def check_internal_logic(self, json_data):
        logic_errors = []
        logic_warnings = []

        # ==============================================================================
        # LOGIC CHECK: ORPHAN TOPOLOGY
        # ==============================================================================
        declared_contexts = set()
        if "contexts" in json_data:
            for ctx in json_data["contexts"]:
                declared_contexts.add(ctx["context_id"]["context_uuid"]["uuid"])

        if "topologies" in json_data:
            for topo in json_data["topologies"]:
                topo_ctx_uuid = topo["topology_id"]["context_id"]["context_uuid"]["uuid"]
                topo_uuid = topo["topology_id"]["topology_uuid"]["uuid"]
                
                # If not declared in the JSON
                if topo_ctx_uuid not in declared_contexts:
                    if self.tfs_devices is not None: # ONLINE MODE
                        # We check if it exists in TeraFlowSDN (in the database)
                        # Note: Ideally we would compare with the unhashed names (if TFS provides them)
                        if topo_ctx_uuid in self.tfs_contexts:
                            logic_warnings.append(f"- [INFO] The topology '{topo_uuid}' will be added to the existing Context '{topo_ctx_uuid}' of the TeraFlowSDN.")
                        else:
                            logic_errors.append(f"- [ERROR] Stateful Orphan Topology: The Context '{topo_ctx_uuid}' does not exist in either the JSON or the TeraFlowSDN! This will cause a Foreign Key Violation in the CockroachDB.")
                    else: # OFFLINE MODE
                        logic_errors.append(f"- [ERROR] Local Orphan Topology: The topology '{topo_uuid}' declares that it belongs to the context '{topo_ctx_uuid}', which does not exist in the JSON!")

        # ==============================================================================
        # LOGIC CHECK: GHOST DEVICE IN THE TOPOLOGY
        # ==============================================================================
        declared_devices = set()
        if "devices" in json_data:
            for dev in json_data["devices"]:
                declared_devices.add(dev["device_id"]["device_uuid"]["uuid"])

        if "topologies" in json_data:
            for topo in json_data["topologies"]:
                topo_uuid = topo["topology_id"]["topology_uuid"]["uuid"]
                if "device_ids" in topo:
                    for dev_id_obj in topo["device_ids"]:
                        dev_uuid = dev_id_obj["device_uuid"]["uuid"]
                        
                        # We check if it's missing from the local JSON
                        if dev_uuid not in declared_devices:
                            if self.tfs_devices is not None: # ONLINE MODE
                                # We check if it's also missing from the TFS database
                                if dev_uuid not in self.tfs_devices:
                                    logic_errors.append(f"- [ERROR] Stateful Ghost Device: The topology '{topo_uuid}' declares that it contains the device '{dev_uuid}', which does not exist in either the JSON or the TeraFlowSDN!")
                            else: # OFFLINE MODE
                                logic_errors.append(f"- [ERROR] Local Ghost Device: The topology '{topo_uuid}' contains the device '{dev_uuid}', which does not exist in the JSON!")

        # ==============================================================================
        # LOGIC CHECK: GHOST LINK IN THE TOPOLOGY
        # ==============================================================================
        declared_links = set()
        if "links" in json_data:
            for link in json_data["links"]:
                declared_links.add(link["link_id"]["link_uuid"]["uuid"])

        if "topologies" in json_data:
            for topo in json_data["topologies"]:
                topo_uuid = topo["topology_id"]["topology_uuid"]["uuid"]
                if "link_ids" in topo:
                    for link_id_obj in topo["link_ids"]:
                        link_uuid = link_id_obj["link_uuid"]["uuid"]
                        
                        # We check if the link is missing from the local JSON
                        if link_uuid not in declared_links:
                            if self.tfs_devices is not None: # ONLINE MODE
                                # We check if it's also missing from the TFS database
                                if link_uuid not in self.tfs_links:
                                    logic_errors.append(f"- [ERROR] Stateful Ghost Link: Topology '{topo_uuid}' declares that it contains the link '{link_uuid}', which does not exist in either the JSON or the TeraFlowSDN!")
                            else: # OFFLINE MODE
                                logic_errors.append(f"- [ERROR] Local Ghost Link: Topology '{topo_uuid}' contains the link '{link_uuid}', which does not exist in the JSON!")

        # ==============================================================================
        # GLOBAL STATE MAPPING (Who owns what in the live network)
        # ==============================================================================
        tfs_global_ips = {}   # { ip_address: owner_uuid }
        tfs_global_macs = {}  # { mac_address: owner_uuid }
        tfs_occupied_ports = {} # { (device_uuid, endpoint_uuid): link_uuid }

        if self.tfs_configs:  # If online and there exist configurations
            for owner_uuid, rules in self.tfs_configs.items():
                for rule in rules:
                    if rule["key"] == "_connect/address":
                        tfs_global_ips[rule["value"]] = owner_uuid
                    elif "mac" in rule["key"].lower():
                        tfs_global_macs[rule["value"]] = owner_uuid
        
        if self.tfs_links: # Port Collisions Mapping
            for l_uuid, endpoints in self.tfs_links.items():
                for ep in endpoints:
                    dev_uuid = ep["device"]
                    port_uuid = ep["endpoint"]
                    tfs_occupied_ports[(dev_uuid, port_uuid)] = l_uuid

        topology_declared_ids = set()
        if "device_ids" in json_data:
            for d_id in json_data["device_ids"]:
                topology_declared_ids.add(d_id["device_uuid"]["uuid"])

        actual_devices_and_ports = {} 
        seen_mgmt_ips = {} 
        device_mgmt_ips = {} 
        device_connections = {}
        
        if "devices" in json_data:
            for device in json_data["devices"]:
                d_id = device["device_id"]["device_uuid"]["uuid"]
                local_type = device.get("device_type", "")
                
                if d_id in actual_devices_and_ports:
                    logic_errors.append(f"- [ERROR] Duplicity! The device '{d_id}' is declared twice.")
                
                actual_devices_and_ports[d_id] = set()

                # -- CHECK FOR UPDATE DEVICE --
                if self.tfs_devices is not None and d_id in self.tfs_devices:
                    dev_name = self.tfs_devices.get(d_id, d_id)
                    logic_warnings.append(f"- [INFO] Update Operation: Device '{dev_name}' already exists in TeraFlowSDN. The new JSON data will update it (Upsert).")

                # -- CHECK: HARDWARE MISMATCH --
                if self.tfs_device_types is not None and d_id in self.tfs_device_types:
                    tfs_type = self.tfs_device_types[d_id]
                    if local_type and tfs_type and local_type != tfs_type:
                        dev_name = self.tfs_devices.get(d_id, d_id)
                        logic_errors.append(f"- [ERROR] Hardware Mismatch: Device '{dev_name}' is declared in the JSON as '{local_type}', but is already registered in TeraFlowSDN as '{tfs_type}'!")
                
                if "device_endpoints" in device:
                    for ep in device["device_endpoints"]:
                        ep_uuid = ep["endpoint_id"]["endpoint_uuid"]["uuid"]
                        actual_devices_and_ports[d_id].add(ep_uuid)

                if "controller_id" in device:
                    c_id = device["controller_id"]["device_uuid"]["uuid"]
                    if d_id == c_id:
                        logic_errors.append(f"- [ERROR] Paradox! Device '{d_id}' is declared as its own Controller.")

                if "components" in device:
                    comp_names = set()
                    for comp in device["components"]:
                        if "name" in comp:
                            comp_names.add(comp["name"])
                    
                    for comp in device["components"]:
                        if "parent" in comp and comp["parent"] not in comp_names:
                            logic_errors.append(f"- [ERROR] Hardware Error (Device '{d_id}'): The component '{comp.get('name')}' is looking for a non-existent parent '{comp['parent']}'.")

                if "device_config" in device and "config_rules" in device["device_config"]:
                    for rule in device["device_config"]["config_rules"]:
                        if "custom" in rule:
                            key = rule["custom"].get("resource_key", "")
                            val = str(rule["custom"].get("resource_value", ""))
                            
                            # IP ADDRESS CHECK
                            if key == "_connect/address":
                                # --- STORE IP FOR LIVENESS CHECK ---
                                if d_id not in device_connections:
                                    device_connections[d_id] = {}
                                device_connections[d_id]['ip'] = val
                                # -------------------------------------------
                                if not IPV4_REGEX.match(val):
                                    logic_errors.append(f"- [ERROR] Invalid IP Format! Device '{d_id}' has an invalid IP address: '{val}'.")
                                else:
                                    # 1. Local Conflict (in the same JSON file)
                                    if val in seen_mgmt_ips:
                                        logic_errors.append(f"- [ERROR] Local IP Conflict! Device '{d_id}' and '{seen_mgmt_ips[val]}' share the same management IP: '{val}' inside this JSON.")
                                    else:
                                        seen_mgmt_ips[val] = d_id
                                        device_mgmt_ips[d_id] = val
                                        
                                    # 2. GLOBAL Conflict (In the live network)
                                    if val in tfs_global_ips:
                                        owner_in_tfs = tfs_global_ips[val]
                                        owner_name = self.tfs_devices.get(owner_in_tfs, owner_in_tfs) if self.tfs_devices else owner_in_tfs
                                        local_device_name = device.get("name", d_id)
                                        
                                        # Compare names to avoid false positives due to UUID hashing
                                        if owner_name != local_device_name and owner_in_tfs != d_id:
                                            logic_errors.append(f"- [ERROR] Global IP Conflict: JSON assigns IP '{val}' to device '{local_device_name}', but it is already assigned to device '{owner_name}' in TeraFlowSDN!")
                            # ADD: Store the port
                            elif key == "_connect/port":
                                if d_id not in device_connections:
                                    device_connections[d_id] = {}
                                device_connections[d_id]['port'] = val
                            #  MAC ADDRESS CHECK
                            elif "mac" in key.lower():
                                if not MAC_REGEX.match(val):
                                    logic_errors.append(f"- [ERROR] Invalid MAC Format! Device '{d_id}' has an invalid MAC address: '{val}' (Key: {key}).")
                                else:
                                    # GLOBAL MAC Conflict
                                    if val in tfs_global_macs:
                                        owner_in_tfs = tfs_global_macs[val]
                                        if owner_in_tfs != d_id:
                                            owner_name = self.tfs_devices.get(owner_in_tfs, owner_in_tfs) if self.tfs_devices else owner_in_tfs
                                            logic_errors.append(f"- [ERROR] Global MAC Conflict: MAC '{val}' is already in use by device '{owner_name}' in TeraFlowSDN!")

            # ==============================================================================
             # CHECK FOR DATA PLANE REACHABILITY (LIVENESS CHECK)
            # ==============================================================================
            for d_id, conn_info in device_connections.items():
                ip = conn_info.get('ip')
                port = conn_info.get('port')
            
                # CHECK: Only proceed if both IP and Port are available, and Port is not '0' (as in emulated datacenters)
                if ip and port and str(port) != "0":
                    is_online = check_tcp_port(ip, port)
                    if not is_online:
                        dev_name = next((d.get("name", d_id) for d in json_data.get("devices", []) if d["device_id"]["device_uuid"]["uuid"] == d_id), d_id)
                        logic_warnings.append(
                            f"- [WARNING] Liveness Check Failed: Device '{dev_name}' at IP {ip}:{port} "
                            f"is not responding. If you proceed, TeraFlowSDN may fail to establish gNMI sessions."
                        )

        actual_device_ids = set(actual_devices_and_ports.keys())
        if topology_declared_ids and topology_declared_ids != actual_device_ids:
            logic_errors.append(f"- [ERROR] Internal Inconsistency!\n  The topology expects {topology_declared_ids}\n  but you defined {actual_device_ids}.")

        if "links" in json_data:
            for link in json_data["links"]:
                l_id = link["link_id"]["link_uuid"]["uuid"]
                # -- SEARCHING FOR LINK UPDATES --
                if self.tfs_links is not None and l_id in self.tfs_links:
                    logic_warnings.append(f"- [INFO] Update Operation: Link '{l_id}' already exists in TeraFlowSDN. If you proceed, its characteristics will be updated.")
                eps = link.get("link_endpoint_ids", [])
                
                if len(eps) >= 2:
                    ep1 = eps[0]
                    ep2 = eps[1]
                    
                    if "device_id" in ep1 and "endpoint_uuid" in ep1 and "device_id" in ep2 and "endpoint_uuid" in ep2:
                        dev1 = ep1["device_id"]["device_uuid"]["uuid"]
                        port1 = ep1["endpoint_uuid"]["uuid"]
                        dev2 = ep2["device_id"]["device_uuid"]["uuid"]
                        port2 = ep2["endpoint_uuid"]["uuid"]

                        # --- SMART RESOLUTION FOR SELF-LOOP & UPSERT ---
                        def resolve_dev(dev_str):
                            if self.tfs_devices:
                                for tid, tname in self.tfs_devices.items():
                                    if dev_str == tid or dev_str == tname:
                                        return tid
                            return dev_str

                        res_dev1 = resolve_dev(dev1)
                        res_dev2 = resolve_dev(dev2)

                        # If it's the same device (either by Name or UUID) and the same port
                        if res_dev1 == res_dev2 and port1 == port2:
                            dev_display_name = self.tfs_devices.get(res_dev1, dev1) if self.tfs_devices else dev1
                            logic_errors.append(
                                f"- [ERROR] Self-Loop in Link '{l_id}': "
                                f"It connects device '{dev_display_name}' port '{port1}' to itself."
                            )
                        ip1 = device_mgmt_ips.get(dev1)
                        ip2 = device_mgmt_ips.get(dev2)
                        
                        if ip1 and ip2:
                            subnet1 = ".".join(ip1.split(".")[:3])
                            subnet2 = ".".join(ip2.split(".")[:3])
                            if subnet1 != subnet2:
                                logic_warnings.append(f"- [WARNING] Subnet Mismatch in Link '{l_id}': '{dev1}' ({ip1}) and '{dev2}' ({ip2}) appear to be in different /24 subnets. Ensure they can route to each other.")

                # ====================================================================
                # STATEFUL GHOST CHECKS (ROUTERS & PORTS)
                # ====================================================================
                for ep in eps:
                    if "device_id" in ep and "endpoint_uuid" in ep:
                        target_device = ep["device_id"]["device_uuid"]["uuid"]
                        target_port = ep["endpoint_uuid"]["uuid"]
                        
                        device_exists_locally = target_device in actual_devices_and_ports
                        
                        # --- TFS ID RESOLUTION ---
                        # Search for true device Hashed ID in TFS
                        real_tfs_id = None
                        if self.tfs_devices is not None:
                            for tfs_id, tfs_dev in self.tfs_devices.items():
                                # Depending on how it's stored, get the name
                                if isinstance(tfs_dev, str):
                                    dev_name = tfs_dev
                                elif isinstance(tfs_dev, dict):
                                    dev_name = tfs_dev.get('name', '')
                                else:
                                    dev_name = getattr(tfs_dev, 'name', '')
                                    
                                # Strict identification either by Hashed ID or Name
                                if target_device == tfs_id or target_device == dev_name:
                                    real_tfs_id = tfs_id
                                    break
                        # ---------------------------------------------------

                        # -- CHECK 1: GHOST ROUTER --
                        if not device_exists_locally:
                            if self.tfs_devices is not None:  # ONLINE MODE
                                if real_tfs_id is None: # Not found by ID or Name
                                    logic_errors.append(f"- [ERROR] Ghost Router in Link '{l_id}': Device '{target_device}' does not exist in the JSON file and is not onboarded in TeraFlowSDN!")
                            else:  # OFFLINE MODE
                                logic_warnings.append(f"- [WARNING] Ghost Router in Link '{l_id}': Device '{target_device}' is missing from the JSON file. (TFS Offline - Could not verify the database).")
                        
                        # -- CHECK 2: GHOST PORT --
                        # Create a structure with all known ports of the device
                        known_ports = set()
                        
                        # 1. Add ports from the local JSON
                        if device_exists_locally:
                            known_ports.update(actual_devices_and_ports[target_device])
                            
                        # 2. Add ports from the TeraFlowSDN database (USE real_tfs_id)
                        if real_tfs_id is not None and real_tfs_id in self.tfs_endpoints:
                            known_ports.update(self.tfs_endpoints[real_tfs_id])
                            
                        # If the port is not in the structure...
                        if target_port not in known_ports:
                            if self.tfs_devices is not None: # ONLINE MODE
                                logic_errors.append(f"- [ERROR] Ghost Port in Link '{l_id}': Port '{target_port}' of device '{target_device}' was not found in either the JSON file or TeraFlowSDN!")
                            else: # OFFLINE MODE
                                logic_warnings.append(f"- [WARNING] Ghost Port in Link '{l_id}': Port '{target_port}' was not found in the JSON for device '{target_device}'. (TFS Offline).")
                        
                        # -- CHECK 3: PORT COLLISION (Completed & Corrected) --
                        if real_tfs_id is not None:
                            link_type = link.get("link_type", "")
                            is_optical = "OPTICAL" in link_type.upper()
                            is_vlan = "." in target_port or ":" in target_port
                            
                            if not is_optical and not is_vlan:
                                # Transform Ethernet1 into its hidden Hash
                                target_port_hash = getattr(self, 'port_name_to_hash', {}).get((real_tfs_id, target_port), target_port)
                                port_tuple = (real_tfs_id, target_port_hash)
                                
                                # 1. Check if port is occupied
                                if port_tuple in tfs_occupied_ports:
                                    existing_link_uuid = tfs_occupied_ports[port_tuple]
                                    
                                    if existing_link_uuid != l_id: # ignore if it's an update of the same link
                                        
                                        # 2. Search for the peer device in the existing link
                                        ext_peer_dev = None
                                        ext_peer_port_hash = None
                                        for (occ_dev, occ_port), occ_link_id in tfs_occupied_ports.items():
                                            if occ_link_id == existing_link_uuid and (occ_dev != real_tfs_id or occ_port != target_port_hash):
                                                ext_peer_dev = occ_dev
                                                ext_peer_port_hash = occ_port
                                                break
                                                
                                        # 3. Search for the peer device in the new link (from the JSON)
                                        ep_0_dev = eps[0]["device_id"]["device_uuid"]["uuid"]
                                        ep_0_port = eps[0]["endpoint_uuid"]["uuid"]
                                        ep_1_dev = eps[1]["device_id"]["device_uuid"]["uuid"]
                                        ep_1_port = eps[1]["endpoint_uuid"]["uuid"]
                                        
                                        def resolve_id(dev_str):
                                            if self.tfs_devices:
                                                for tid, tname in self.tfs_devices.items():
                                                    if dev_str == tid or dev_str == tname: return tid
                                            return dev_str
                                            
                                        new_dev0_res = resolve_id(ep_0_dev)
                                        new_dev1_res = resolve_id(ep_1_dev)
                                        
                                        if new_dev0_res == real_tfs_id and ep_0_port == target_port:
                                            new_peer_dev = new_dev1_res
                                            new_peer_port = ep_1_port
                                            new_is_source = True # source
                                        else:
                                            new_peer_dev = new_dev0_res
                                            new_peer_port = ep_0_port
                                            new_is_source = False # destination
                                            
                                        # Transform the peer port into its hidden Hash for comparison
                                        new_peer_port_hash = getattr(self, 'port_name_to_hash', {}).get((new_peer_dev, new_peer_port), new_peer_port)
                                            
                                        # 4. ANALYSIS OF THE 3 SCENARIOS
                                        dev_name_display = target_device
                                        
                                        error_msg = None
                                        if ext_peer_dev and new_peer_dev != ext_peer_dev:
                                            error_msg = f"- [ERROR] Port Collision (Third Wheel): Port '{target_port}' of '{dev_name_display}' is already connected to another device in the TFS!"
                                        elif ext_peer_port_hash and new_peer_port_hash != ext_peer_port_hash:
                                            error_msg = f"- [ERROR] Port Collision (Split Ends): Port '{target_port}' of '{dev_name_display}' is already connected to a different port of the same device!"
                                        else:
                                            # For same devices and same ports check the direction
                                            ext_is_source = None
                                            if self.tfs_links and existing_link_uuid in self.tfs_links:
                                                ext_eps_list = self.tfs_links[existing_link_uuid]
                                                if len(ext_eps_list) > 0:
                                                    ext_src_hash = ext_eps_list[0]["device"]
                                                    ext_is_source = (ext_src_hash == real_tfs_id)
                                            
                                            if ext_is_source is not None:
                                                if ext_is_source == new_is_source:
                                                    error_msg = f"- [ERROR] Duplicate Link (Parallel Universe): There is already a link '{existing_link_uuid}' in the same direction! Risk of false bandwidth duplication."
                                                else:
                                                    pass # Bidirectional link, Allowed!
                                            else:
                                                 error_msg = f"- [ERROR] Port Collision: Port '{target_port}' of '{dev_name_display}' is already in use by the link '{existing_link_uuid}'"
                                        
                                        # Add ONLY if it doesn't already exist in the list (Deduplication)
                                        if error_msg and error_msg not in logic_errors:
                                            logic_errors.append(error_msg)

                if "attributes" in link:
                    attrs = link["attributes"]
                    total_cap = attrs.get("total_capacity_gbps")
                    used_cap = attrs.get("used_capacity_gbps")

                    if total_cap is not None and used_cap is not None:
                    # Check 1: Used exceeds Total
                        if used_cap > total_cap:
                            logic_errors.append(
                            f"- [ERROR] Capacity Paradox in Link '{l_id}': "
                            f"Used capacity ({used_cap} Gbps) exceeds total capacity ({total_cap} Gbps)."
                            )
                    # Check 2: Negative Values
                        if total_cap < 0 or used_cap < 0:
                            logic_errors.append(
                            f"- [ERROR] Invalid Capacity in Link '{l_id}': "
                            f"Capacity values cannot be negative (Total: {total_cap}, Used: {used_cap})."
                            )

        return (len(logic_errors) == 0), logic_errors, logic_warnings
    
    def check_topology(self, json_data):
        schema_errors = []
        for error in self.schema_validator.iter_errors(json_data):
            path = " -> ".join([str(p) for p in error.path]) if error.path else "Root"
            schema_errors.append(f"  [Field: {path}]\n  Problem: {error.message}\n")

        if schema_errors:
            error_report = "Syntax (schema) errors found:\n" + "-"*40 + "\n" + "\n".join(schema_errors)
            return False, error_report

        # ==============================================================================
        # PRINT FULL INFRASTRUCTURE REPORT
        # ==============================================================================
        print("\n" + "=" * 60)
        print("🔧 FULL gRPC INFRASTRUCTURE REPORT:")
        if self.tfs_devices is not None:
            print(f"[+] Connection to TFS: SUCCESS!")
            print(f"    - Contexts in the database: {len(self.tfs_contexts)} {self.tfs_contexts}")
            print(f"    - Devices in the database ({len(self.tfs_devices)}):")
            for uid, name in self.tfs_devices.items():
                ports_count = len(self.tfs_endpoints.get(uid, set()))
                configs_count = len(self.tfs_configs.get(uid, []))
                print(f"      * '{name}' -> Found: {ports_count} ports & {configs_count} configurations")
            
            print(f"    - Links in the database: {len(self.tfs_links)}")
        else:
            print("[-] Connection to TFS: FAILED (Offline). Script is running locally.")
        print("=" * 60 + "\n")

        is_logical, logic_errors, logic_warnings = self.check_internal_logic(json_data)
        
        report_lines = []
        
        if logic_warnings:
            report_lines.append("Warnings (Non-blocking):")
            report_lines.append("-" * 40)
            report_lines.extend(logic_warnings)
            report_lines.append("") 
            
        if not is_logical:
            report_lines.append("Logic (semantic) errors found:")
            report_lines.append("-" * 40)
            report_lines.extend(logic_errors)
            return False, "\n".join(report_lines)
            
        report_lines.append("Valid Topology (Syntax & Local Logic OK)")
        return True, "\n".join(report_lines)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide the JSON file. Example: python validation1.py my_topo.json")
        sys.exit(1)

    json_file_to_test = sys.argv[1]

    with open(json_file_to_test, 'r') as file:
        user_topology = json.load(file)

    validator = TopologyPreValidator(schema_path="topology_schema.json")
    is_valid, message = validator.check_topology(user_topology)

    print(message)