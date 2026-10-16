# Chapter 5: Network Topology Design & Emulation

This directory contains the configuration files, Containerlab (`clab`) network topologies, and automation scripts developed for the experimental evaluation of the TeraFlowSDN (TFS) controller in **Chapter 5** of the diploma thesis.

---

## Structure & Subsections

### 1. Section 5.2 (`Chapter_5.2/`)
Experimental setup based on the official ETSI TFS Group Hackfest#5, featuring Arista cEOS virtual routers and basic L3VPN service provisioning.
* `clab-deployment/arista.clab.yml`: Network topology descriptor for Containerlab.
* `JSONs/`: Device and link descriptors (`hackfest-routers-links.json`) and L3VPN service configuration files (`l3vpn-hackfest.json`) for onboarding into TFS.

### 2. Section 5.3 (`Chapter_5.3/`)
Implementation of a 3-Node Clos (Spine-Leaf) datacenter fabric with VXLAN/EVPN.
* `clab-deployment/3nodeclos.clab.yml`: Containerlab topology descriptor for the 3-node network.
* `JSONs/`: Device onboarding (`3clos-onboarding.json`), link definitions (`links.json`), and VXLAN service descriptors (`3-node-clos-VXLAN.json`).
* `automation-scripts/`: Python scripts for automated network configuration:
  * `is-is.py`: Underlay routing configuration using IS-IS.
  * `3-node-clos-BGP.py`: BGP EVPN Overlay configuration.
  * `ip-registration-script.py`: Interface IP address assignment.
  * `create_telemetry_subs.py`: Creation of telemetry subscriptions for network monitoring.

### 3. Section 5.4 (`Chapter_5.4/`)
Scaling to a complex 5-Stage Clos datacenter fabric architecture.
* `clab-deployment/5stageclos.clab.yml`: Full Containerlab topology descriptor for the 5-Stage Clos network.
* `JSONs/`:
  * `5-stage-onboarding.json`: Device onboarding and registration into the TFS controller.
  * `link-creation.json`: Creation and definition of physical and logical links between nodes.
  * `VXLAN.json`: Overlay service provisioning (VXLAN/EVPN).
* `automation-scripts/`:
  * `is-is.py`: Automated Underlay routing configuration (IS-IS).
  * `BGP.py`: Automated BGP EVPN Overlay configuration.
  * `ip-registration.py`: Bulk IP address assignment to network interfaces.

---

## Execution Guidelines

### Launching Topologies (Containerlab)
From within the `clab-deployment/` subdirectory of the respective section:
```bash
sudo containerlab deploy -t <filename>.clab.yml
```

### Running Automation Scripts
From within the automation-scripts/ subdirectory of the respective section
```bash
python3 <script_name>.py
```
