import streamlit as st
import requests
import json
import time
from datetime import datetime

# ====== FIREBASE SETTINGS ======
PROJECT_ID = "volt-a-value" 
FIRESTORE_URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents"

st.set_page_config(page_title="Lieferdienst MVP", layout="wide")

# ====== DATABASE FUNCTIONS ======
def bestellung_speichern(daten):
    url = f"{FIRESTORE_URL}/objednavky"
    payload = {"fields": {k: {"stringValue": str(v)} for k, v in daten.items()}}
    requests.post(url, json=payload)

def bestellungen_laden():
    url = f"{FIRESTORE_URL}/objednavky"
    res = requests.get(url)
    if res.status_code == 200 and "documents" in res.json():
        return res.json()["documents"]
    return []

def bestellstatus_aktualisieren(doc_name, neuer_status, fahrer_name="", lieferdetails=""):
    url = f"https://firestore.googleapis.com/v1/{doc_name}?updateMask.fieldPaths=stav&updateMask.fieldPaths=kuryr&updateMask.fieldPaths=adresa"
    payload = {
        "fields": {
            "stav": {"stringValue": neuer_status},
            "kuryr": {"stringValue": fahrer_name},
            "adresa": {"stringValue": lieferdetails}
        }
    }
    requests.patch(url, json=payload)

def alle_bestellungen_loeschen():
    docs = bestellungen_laden()
    for d in docs:
        requests.delete(f"https://firestore.googleapis.com/v1/{d['name']}")

# ====== NAVIGATION ======
st.sidebar.title("Navigation")
rolle = st.sidebar.radio("Bereich auswählen:", [
    "🏠 1. Kunden-Ansicht", 
    "🏬 2. Kassa / Eingabe (Theke)",
    "👨‍🍳 3. Küche Monitor", 
    "🚗 4. Fahrer-Ansicht (Mobil)"
])

menue = {"Oklahoma Burger": 10.90, "Pommes": 4.00, "Curly Fries": 4.00, "Pepsi": 3.00, "Fanta Dose": 3.00}
RESTAURANT_NAME = "Smash Brothers"

# ====== 1. KUNDEN-ANSICHT ======
if rolle == "🏠 1. Kunden-Ansicht":
    st.header("🛒 Online-Shop – Smash Brothers")
    # ... (kod pro zákazníka zůstává stejný)
    st.info("Kunden-Shop ist aktiv.")

# ====== 2. KASSA / EINGABE ======
elif rolle == "🏬 2. Kassa / Eingabe (Theke)":
    st.header(f"🏬 Kassa & Auftragsannahme")
    docs = bestellungen_laden()
    
    st.subheader("🔔 Eingehende Bestellungen")
    for d in docs:
        f = d["fields"]
        status = f["stav"]["stringValue"]
        doc_name = d["name"]
        if status == "Wartet auf Bestätigung durch Kassa":
            with st.container(border=True):
                st.write(f"📦 {f['obsah']['stringValue']}")
                if st.button(f"Bestätigen & In Küche: {doc_name[-5:]}", key=f"prij_{doc_name}"):
                    bestellstatus_aktualisieren(doc_name, "In Zubereitung (Küche)", "Petr (Auto)", f["adresa"]["stringValue"])
                    st.rerun()

# ====== 3. KÜCHE MONITOR ======
elif rolle == "👨‍🍳 3. Küche Monitor":
    st.header("👨‍🍳 Küche Monitor")
    docs = bestellungen_laden()
    for d in docs:
        f = d["fields"]
        if f["stav"]["stringValue"] == "In Zubereitung (Küche)":
            with st.container(border=True):
                st.markdown(f"### 🍔 {f['obsah']['stringValue']}")
                if st.button(f"✅ FERTIG: {d['name'][-5:]}", key=f"kuch_{d['name']}"):
                    bestellstatus_aktualisieren(d['name'], "Ready for Pick-up", "Petr (Auto)", f["adresa"]["stringValue"])
                    st.rerun()

# ====== 4. FAHRER-ANSICHT (BATCHING LOGIKA) ======
elif rolle == "🚗 4. Fahrer-Ansicht (Mobil)":
    st.header("Kurier-App (Meine Aufträge)")
    fahrer_name = "Petr (Auto)"
    
    if "bargeld_eur" not in st.session_state:
        st.session_state.bargeld_eur = 0.0
        st.session_state.provision_eur = 0.0

    st.subheader(f"📊 Übersicht für {fahrer_name}")
    c1, c2 = st.columns(2)
    c1.metric("Provision", f"{st.session_state.provision_eur:.2f} €")
    c2.metric("Cash", f"{st.session_state.bargeld_eur:.2f} €")
    
    if st.session_state.bargeld_eur >= 200.0:
        st.error("🛑 BARGELDLIMIT ERREICHT!")
        if st.button("Geld abgerechnet"): st.session_state.bargeld_eur = 0.0; st.rerun()
    else:
        docs = bestellungen_laden()
        aktive_auftraege = [d for d in docs if d["fields"]["kuryr"]["stringValue"] == fahrer_name 
                            and d["fields"]["stav"]["stringValue"] in ["In Zubereitung (Küche)", "Ready for Pick-up", "Auf dem Weg zum Kunden"]]
        
        if not aktive_auftraege:
            st.info("Keine aktiven Aufträge.")
        else:
            for d in aktive_auftraege:
                f = d["fields"]
                status = f["stav"]["stringValue"]
                doc_name = d["name"]
                
                with st.expander(f"📦 Auftrag {doc_name[-5:]} - {status}", expanded=True):
                    st.write(f"**Essen:** {f['obsah']['stringValue']}")
                    st.write(f"**Adresse:** {f['adresa']['stringValue']}")
                    
                    if status == "In Zubereitung (Küche)":
                        st.info("⏳ Wird noch zubereitet.")
                    elif status == "Ready for Pick-up":
                        st.warning("🚨 HOTOVO! Hol es dir am Tresen!")
                        if st.button(f"Vyzvednuto (Auftrag {doc_name[-5:]})", key=f"vyz_{doc_name}"):
                            bestellstatus_aktualisieren(doc_name, "Auf dem Weg zum Kunden", fahrer_name, f["adresa"]["stringValue"])
                            st.rerun()
                    elif status == "Auf dem Weg zum Kunden":
                        st.success("🚚 Auf dem Weg zum Kunden")
                        if st.button(f"Doručeno (Auftrag {doc_name[-5:]})", key=f"dor_{doc_name}"):
                            st.session_state.provision_eur += 4.00
                            if f["platba"]["stringValue"] == "Barzahlung":
                                st.session_state.bargeld_eur += float(f["cena"]["stringValue"])
                            bestellstatus_aktualisieren(doc_name, "Geliefert", fahrer_name, f["adresa"]["stringValue"])
                            st.rerun()
