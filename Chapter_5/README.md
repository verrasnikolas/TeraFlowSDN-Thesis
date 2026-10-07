# Κεφάλαιο 5: Σχεδίαση και Εξομοίωση Τοπολογιών

Στον συγκεκριμένο κατάλογο περιλαμβάνονται τα αρχεία διαμόρφωσης, οι τοπολογίες Containerlab (`clab`) και τα σενάρια αυτοματοποίησης που αναπτύχθηκαν για την πειραματική αξιολόγηση του ελεγκτή TeraFlowSDN (TFS) στο **Κεφάλαιο 5** της διπλωματικής εργασίας.

---

## Δομή & Υποενότητες

### 1. Ενότητα 5.2 (`Chapter_5.2/`)
Πειραματική διάταξη βασισμένη στο επίσημο Hackfest#5 του ETSI TFS Group, με εικονικούς δρομολογητές Arista cEOS και βασική υπηρεσία L3VPN.
* `clab-deployment/arista.clab.yml`: Περιγραφή τοπολογίας δικτύου για το Containerlab.
* `JSONs/`: Αρχεία ορισμού συσκευών, ζεύξεων (`hackfest-routers-links.json`) και παραμετροποίησης υπηρεσίας L3VPN (`l3vpn-hackfest.json`) προς εισαγωγή στον TFS.

### 2. Ενότητα 5.3 (`Chapter_5.3/`)
Υλοποίηση αρχιτεκτονικής κέντρου δεδομένων υποδομής 3-Node Clos  (Spine-Leaf) με VXLAN/EVPN.
* `clab-deployment/3nodeclos.clab.yml`: Τοπολογία Containerlab για το δίκτυο 3 κόμβων.
* `JSONs/`: Αρχεία εισαγωγής συσκευών (`3clos-onboarding.json`), συνδέσμων (`links.json`) και υπηρεσιών VXLAN (`3-node-clos-VXLAN.json`).
* `automation-scripts/`: Σενάρια Python για την αυτοματοποιημένη παραμετροποίηση:
  * `is-is.py`: Ρύθμιση Underlay δρομολόγησης (IS-IS).
  * `3-node-clos-BGP.py`: Παραμετροποίηση BGP EVPN Overlay.
  * `ip-registration-script.py`: Απόδοση IP διευθύνσεων διεπαφών.
  * `create_telemetry_subs.py`: Δημιουργία συνδρομών τηλεμετρίας για παρακολούθηση.

### 3. Ενότητα 5.4 (`Chapter_5.4/`)
Κλιμάκωση σε σύνθετη αρχιτεκτονική Clos 5 σταδίων (υποδομή 5-Stage Clos).
* `clab-deployment/5stageclos.clab.yml`: Πλήρης τοπολογία Containerlab για το δίκτυο 5-Stage Clos.
* `JSONs/`:
  * `5-stage-onboarding.json`: Εισαγωγή και καταχώριση των συσκευών στον ελεγκτή TFS.
  * `link-creation.json`: Δημιουργία και ορισμός των φυσικών/λογικών ζεύξεων μεταξύ των κόμβων.
  * `VXLAN.json`: Παραμετροποίηση υπηρεσιών Overlay (VXLAN/EVPN).
* `automation-scripts/`:
  * `is-is.py`: Αυτοματοποιημένη παραμετροποίηση Underlay δρομολόγησης (IS-IS).
  * `BGP.py`: Αυτοματοποιημένη ρύθμιση BGP EVPN Overlay.
  * `ip-registration.py`: Μαζική απόδοση και καταχώριση διευθύνσεων IP στις διεπαφές.

---

## Γενικές Οδηγίες Εκτέλεσης

### Εκκίνηση Τοπολογίας (Containerlab)
Μέσα στον υποφάκελο `clab-deployment/` της εκάστοτε ενότητας:
```bash
sudo containerlab deploy -t <όνομα_αρχείου>.clab.yml
```

### Εκτέλεση Σεναρίων Αυτοματοποίησης
Μέσα στον υποφάκελο `automation-scripts`
```bash
python3 <όνομα_script>.py
```
