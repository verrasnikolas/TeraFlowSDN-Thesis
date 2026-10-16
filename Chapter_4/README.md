# Chapter 4: Topology Validation Tool Development

This directory contains the source code and test suites for the **Validation Tool (`valtool`)** developed as part of **Chapter 4** of the diploma thesis.

The tool performs pre-deployment validation, format verification, and semantic consistency checks on network topology descriptors (e.g., MAC address verification, port collision/link conflict detection, identification of orphan/ghost entities, etc.) prior to onboarding onto the TeraFlowSDN (TFS) controller.

---

## Directory Contents

* `validation1.py`: The main Python executable script of the validation tool.
* `topology_schema.json`: The JSON Schema specifying data formats, structural rules, and constraints for topology descriptors.
* `tfs_grpc/`: Directory containing pre-compiled gRPC stubs/clients for communication with TeraFlowSDN microservices.
* `test_*.json` & `MACTest.json`: Comprehensive test cases used to evaluate and benchmark the validation engine across edge cases and intentional error conditions (e.g., ghost ports, port collisions, structural anomalies).

---

## Prerequisites

The use of an isolated Python virtual environment is recommended:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install jsonschema grpcio grpcio-tools
```

## Usage

To execute the validation engine against a target topology descriptor:

```bash
python3 validation1.py <topology_file>.json
```
