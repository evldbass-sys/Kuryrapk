import streamlit as st
import requests
import json
import time
from datetime import datetime

# ====== FIREBASE SETTINGS ======
PROJECT_ID = "volt-a-value" 
FIRESTORE_URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents"

st.set_page_config(page_title="Smash Brothers Delivery", layout="wide")

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
rolle = st.sidebar.radio("Bereich auswählen:", [
    "🏠 1. Kunden-Ansicht", 
    "🏬 2. Kassa / Eingabe (Theke)",
    "👨‍🍳 3. Küche Monitor", 
    "🚗 4. Fahrer-Ansicht (Mobil & Finanzen)"
])

menue = {"Oklahoma Burger": 10.90, "Pommes": 4.00, "Curly Fries": 4.00, "Pepsi": 3.00, "Fanta Dose": 3.00}
RESTAURANT_NAME = "Smash Brothers"

# ====== 1. KUNDEN-ANSICHT ======
if rolle == "🏠 1. Kunden-Ansicht":
    st.header("🛒 Online-Shop – Smash Brothers")
    if "kunden_korb" not in st.session_state: st.session_state.kunden_korb = {a: 0 for a in menue}
    for a, p in menue.items():
        c1, c2, c3 = st.columns([2,1,1])
        c1.write(f"**{a}** ({p:.2f} €)"); c2.button("➕", key=f"k_add_{a}", on_click=lambda a=a: st.session_state.kunden_korb.update({a: st.session_state.kunden_korb[a]+1}))
        if st.session_state.kunden_korb[a] > 0: c3.write(f"{st.session_state.kunden_korb[a]}x")
    if st.button("🚀 BESTELLUNG ABSENDEN"):
        bestellung_speichern({"obsah": str(st.session_state.kunden_korb), "cena": "15.00", "platba": "Online", "adresa": "Musterstr 1", "stav": "Wartet auf Bestätigung durch Kassa", "kuryr": "Petr (Auto)", "cas": datetime.now().strftime("%H:%M:%S"), "dysko": "0"})
        st.success("Gesendet!")

# ====== 2. KASSA / EINGABE ======
elif rolle == "🏬 2. Kassa / Eingabe (Theke)":
    st.header("🏬 Kassa & Auftragsannahme")
    for d in bestellungen_laden():
        f = d["fields"]
        if f["stav"]["stringValue"] == "Wartet auf Bestätigung durch Kassa":
            with st.container(border=True):
                st.write(f"📦 {f['obsah']['stringValue']}")
                if st.button(f"✔️ Bestätigen: {d['name'][-5:]}"):
                    bestellstatus_aktualisieren(d['name'], "In Zubereitung (Küche)", "Petr (Auto)", f["adresa"]["stringValue"])
                    st.rerun()

# ====== 3. KÜCHE MONITOR ======
elif rolle == "👨‍🍳 3. Küche Monitor":
    st.header("👨‍🍳 Küche Monitor (Zubereitung)")
    for d in bestellungen_laden():
        f = d["fields"]
        if f["stav"]["stringValue"] == "In Zubereitung (Küche)":
            with st.container(border=True):
                st.markdown(f"### 🍔 {f['obsah']['stringValue']}")
                if st.button(f"✅ FERTIG / VERPACKT: {d['name'][-5:]}"):
                    bestellstatus_aktualisieren(d['name'], "Ready for Pick-up", "Petr (Auto)", f["adresa"]["stringValue"])
                    st.rerun()

# ====== 4. FAHRER-ANSICHT (KOMPLETT) ======
elif rolle == "🚗 4. Fahrer-Ansicht (Mobil & Finanzen)":
    st.header("Kurier-App (Meine Aufträge)")
    if "bargeld_eur" not in st.session_state: st.session_state.bargeld_eur = 0.0
    
    docs = bestellungen_laden()
    aktive_auftraege = [d for d in docs if d["fields"]["kuryr"]["stringValue"] == "Petr (Auto)" and d["fields"]["stav"]["stringValue"] in ["In Zubereitung (Küche)", "Ready for Pick-up", "Auf dem Weg zum Kunden"]]
    
    if not aktive_auftraege:
        st.info("Kein aktiver Auftrag. Warte auf Kassa...")
    else:
        for d in aktive_auftraege:
            f = d["fields"]
            stav = f["stav"]["stringValue"]
            doc_name = d["name"]
            
            # Barevné stavy
            border_color = "#ffc107" if stav == "In Zubereitung (Küche)" else ("#28a745" if stav == "Ready for Pick-up" else "#007bff")
            header_text = "⏳ VAŘÍ SE" if stav == "In Zubereitung (Küche)" else ("🚨 HOTOVO - BĚŽ NA BAR" if stav == "Ready for Pick-up" else "🚚 NA CESTĚ")
            
            with st.container(border=True):
                st.markdown(f"<h4 style='color:{border_color};'>{header_text}</h4>", unsafe_allow_html=True)
                st.write(f"**Inhalt:** {f['obsah']['stringValue']}")
                st.write(f"**Adresse:** {f['adresa']['stringValue']}")
                
                if stav == "Ready for Pick-up":
                    if st.button(f"🚀 VYZVEDNUTO {doc_name[-5:]}"):
                        bestellstatus_aktualisieren(doc_name, "Auf dem Weg zum Kunden", "Petr (Auto)", f["adresa"]["stringValue"])
                        st.rerun()
                elif stav == "Auf dem Weg zum Kunden":
                    if st.button(f"✅ DORUČENO {doc_name[-5:]}"):
                        st.session_state.bargeld_eur += float(f.get("cena", {"stringValue": "0"}).get("stringValue"))
                        bestellstatus_aktualisieren(doc_name, "Geliefert", "Petr (Auto)", f["adresa"]["stringValue"])
                        st.rerun()
