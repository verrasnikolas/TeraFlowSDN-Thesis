# Creation of Clos Topologies and Development of Validation Mechanism on ETSI TeraFlowSDN

This repository hosts the official source code, configuration files, Containerlab topology descriptors, and automation scripts developed for the diploma thesis conducted at the **School of Electrical and Computer Engineering, National Technical University of Athens (NTUA)**.

---

## Repository Overview

The artifacts in this repository accompany the experimental methodology and validation framework proposed in the thesis:
* **`Chapter_3/`**: Parameterization and custom microservice deployment scripts for the ETSI TeraFlowSDN (TFS) controller in microK8s.
* **`Chapter_4/`**: Implementation of the proactive multi-tier Validation Tool (`valtool`) along with schema definitions, gRPC stubs, and unit/edge test cases.
* **`Chapter_5/`**: Containerlab (`clab`) network emulation topologies (Arista cEOS), onboarding JSON descriptors, and Python automation workflows for 3-Node Clos and 5-Stage Clos fabrics.

---

## Abstract

The subject of this diploma thesis is the implementation and automated management of modern data center Clos network topologies under the scope of the cloud-native SDN controller ETSI TeraFlowSDN, as well as the development of a proactive validation mechanism for JSON descriptors prior to their onboarding into the system.

Initially, the theoretical and technological background supporting the thesis is analyzed, focusing on the principles of SDN, communication and data modeling protocols (gRPC, JSON Schema, etc.), as well as Data Center fabric architectures. In parallel, the architecture of ETSI TeraFlowSDN is examined, analyzing the role of its core mechanisms, along with the orchestration of the system via microK8s.

Subsequently, the methodology for designing and implementing a multi-tier proactive validation mechanism in Python is detailed. The tool intervenes prior to descriptor submission to the controller, sequentially executing validation checks to detect syntactic and semantic errors in real time.

The experimental part of the thesis involves the emulation of scalable topologies in Containerlab using virtual Arista cEOS routers, starting from a simple reference setup and progressing to 3-Node Clos and 5-Stage Clos Fabric topologies. Through a hybrid model leveraging TeraFlowSDN and external network automation tools, network convergence and end-to-end communication are achieved.

The primary findings of the thesis demonstrate that TeraFlowSDN is susceptible to administrative errors, necessitating the existence of an extensive proactive validation mechanism. At the same time, the practical evaluation highlighted the operational limits of TeraFlowSDN, as it offers incomplete support for holistic automation.

---

## Keywords

Software-Defined Networking (SDN), ETSI TeraFlowSDN, Clos, JSON, Validation Tool, IS-IS, MP-BGP EVPN, VXLAN, Containerlab, microK8s.

---

## Navigation & Detailed Documentation

For specific setup and execution guides, refer to the corresponding subdirectories:
* [Chapter 3: Deployment & Setup Guide](./Chapter_3/)
* [Chapter 4: Validation Engine & Tests](./Chapter_4/)
* [Chapter 5: Emulation Topologies & Automation Scripts](./Chapter_5/)
