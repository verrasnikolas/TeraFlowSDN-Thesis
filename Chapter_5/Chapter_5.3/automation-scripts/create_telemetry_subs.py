import sys
import os
import grpc
import uuid

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../tfs-ctrl/src')))

from common.proto.kpi_sample_types_pb2 import KpiSampleType
from common.proto.kpi_manager_pb2 import KpiDescriptor
import common.proto.kpi_manager_pb2_grpc as kpi_manager_grpc
from common.proto.telemetry_frontend_pb2 import Collector
import common.proto.telemetry_frontend_pb2_grpc as telemetry_frontend_grpc

LEAF1_UUID = "50c36ec0-09ba-546a-b18f-27f9776ce876"

# Τα αληθινά UUIDs των Endpoints από το Context Service του TFS
ENDPOINTS = [
    {"name": "Ethernet1", "uuid": "ae1a7c50-38a8-53c6-bce5-0be7246ddbdf"},
    {"name": "Ethernet2", "uuid": "d28fac93-24c7-54fa-92bd-7dd485382241"}
]

sample_types = [
    (KpiSampleType.KPISAMPLETYPE_BYTES_RECEIVED, "BytesReceived"),
    (KpiSampleType.KPISAMPLETYPE_BYTES_TRANSMITTED, "BytesTransmitted")
]

def main():
    print("=== Βήμα 1: Εγγραφή KPI στο KpiManager | Βήμα 2: Εκκίνηση Collector ===")
    
    kpi_channel = grpc.insecure_channel('127.0.0.1:30010')
    kpi_stub = kpi_manager_grpc.KpiManagerServiceStub(kpi_channel)

    tel_channel = grpc.insecure_channel('127.0.0.1:30050')
    tel_stub = telemetry_frontend_grpc.TelemetryFrontendServiceStub(tel_channel)

    for ep in ENDPOINTS:
        for st, st_name in sample_types:
            try:
                # 1. Δημιουργία KpiDescriptor με έγκυρα UUIDs
                kpi_desc = KpiDescriptor()
                kpi_desc.kpi_id.kpi_id.uuid = str(uuid.uuid4())  # Παράγουμε έγκυρο KPI UUID
                kpi_desc.kpi_description = f"KPI for Leaf1 {ep['name']} {st_name}"
                kpi_desc.kpi_sample_type = st
                kpi_desc.device_id.device_uuid.uuid = LEAF1_UUID
                
                # --- Η ΔΙΟΡΘΩΣΗ ΕΙΝΑΙ ΕΔΩ ---
                # 1. Απαραίτητο: Το endpoint_id πρέπει να ξέρει σε ποιο device ανήκει (αλλιώς είναι ορφανό)
                kpi_desc.endpoint_id.device_id.device_uuid.uuid = LEAF1_UUID
                
                # 2. Βάζουμε απευθείας το 'name' (π.χ. Ethernet1) αντί για το UUID για να κάνει match με τον Arista!
                kpi_desc.endpoint_id.endpoint_uuid.uuid = ep["name"]
                # -----------------------------
                
                # Εγγραφή στη βάση
                kpi_id = kpi_stub.SetKpiDescriptor(kpi_desc)
                print(f"\n[+] KPI Δημιουργήθηκε επιτυχώς!")
                print(f"    ID: {kpi_id.kpi_id.uuid} | Interface: {ep['name']} | Type: {st_name}")
                
                # 2. Εκκίνηση του Telemetry Collector
                collector = Collector()
                collector.collector_id.collector_id.uuid = str(uuid.uuid4())
                collector.kpi_id.CopyFrom(kpi_id)
                collector.duration_s = -1.0  # Συνεχής συλλογή
                collector.interval_s = 5.0   # Κάθε 5 δευτερόλεπτα
                
                tel_stub.StartCollector(collector)
                print(f"  [✔] Ο Collector ξεκίνησε για {ep['name']} ({st_name})")
                
            except grpc.RpcError as e:
                print(f"  [✘] gRPC Error: {e.details()}")

if __name__ == "__main__":
    main()