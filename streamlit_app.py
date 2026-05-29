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

def bestellstatus_aktualisieren(doc_name, neuer_status, fahrer_name=""):
    url = f"https://firestore.googleapis.com/v1/{doc_name}?updateMask.fieldPaths=stav&updateMask.fieldPaths=kuryr"
    payload = {"fields": {"stav": {"stringValue": neuer_status}, "kuryr": {"stringValue": fahrer_name}}}
    requests.patch(url, json=payload)

def alle_bestellungen_loeschen():
    docs = bestellungen_laden()
    for d in docs:
        requests.delete(f"https://firestore.googleapis.com/v1/{d['name']}")

# ====== NAVIGATION ======
st.title("🚚 Kuriersystem & Restaurant Dashboard")
rolle = st.sidebar.radio("Rolle auswählen:", ["🏬 Restaurant-Ansicht", "🚗 Fahrer-Ansicht (Mobil)"])

# ====== 1. RESTAURANT DASHBOARD ======
if rolle == "🏬 Restaurant-Ansicht":
    st.header("Restaurant Administration – Neue Bestellung")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🍔 Menü")
        menue = {"Oklahoma Burger": 10.90, "Pommes": 4.00, "Curly Fries": 4.00, "Pepsi": 3.00, "Fanta Dose": 3.00}
        if "warenkorb" not in st.session_state:
            st.session_state.warenkorb = {artikel: 0 for artikel in menue}
            
        for artikel, preis in menue.items():
            cc1, cc2, cc3 = st.columns([2, 1, 1])
            with cc1:
                st.write(f"**{artikel}** ({preis:.2f} €)")
            with cc2:
                if st.button(f"➕ Hinzufügen", key=f"add_{artikel}"):
                    st.session_state.warenkorb[artikel] += 1
            with cc3:
                if st.session_state.warenkorb[artikel] > 0:
                    st.write(f"im Korb: **{st.session_state.warenkorb[artikel]}x**")
                    if st.button(f"❌", key=f"remove_{artikel}"):
                        st.session_state.warenkorb[artikel] = 0

    with col2:
        st.subheader("🛒 Übersicht & Absenden")
        artikel_im_korb = []
        gesamtsumme = 0.0
        for artikel, anzahl in st.session_state.warenkorb.items():
            if anzahl > 0:
                preis_pro_posten = menue[artikel] * anzahl
                artikel_im_korb.append(f"{anzahl}x {artikel}")
                gesamtsumme += preis_pro_posten
                st.text(f"• {anzahl}x {artikel} = {preis_pro_posten:.2f} €")
                
        st.write("---")
        st.metric("Gesamtsumme", f"{gesamtsumme:.2f} €")
        
        kunde_name = st.text_input("Name des Kunden", "Max Mustermann")
        kunde_telefon = st.text_input("Telefonnummer", "+43 660 1234567")
        adresse = st.text_input("Lieferadresse", "Hauptstraße 12, Stadt")
        zahlung = st.selectbox("Zahlungsart des Kunden", ["Online-Karte", "Barzahlung"])
        
        if artikel_im_korb == []:
            st.info("Der Warenkorb ist leer. Klicke links auf die Produkte, um eine Bestellung aufzugeben.")
        else:
            if st.button("🚀 AN DEN NÄCHSTEN KURIER SENDEN", type="primary", use_container_width=True):
                naechster_fahrer = "Petr (Auto)"
                neue_bestellung = {
                    "obsah": ", ".join(artikel_im_korb),
                    "cena": f"{gesamtsumme:.2f}",
                    "platba": zahlung,
                    "adresa": f"{adresse} | Kunde: {kunde_name} | Tel: {kunde_telefon}",
                    "stav": "Wartet auf Bestätigung",
                    "kuryr": naechster_fahrer,
                    "cas": datetime.now().strftime("%H:%M:%S")
                }
                bestellung_speichern(neue_bestellung)
                st.session_state.warenkorb = {artikel: 0 for artikel in menue}
                st.success(f"Gesendet! Der Fahrer {naechster_fahrer} hat gerade eine Benachrichtigung erhalten.")
                st.rerun()
                
        st.write("---")
        if st.button("🗑️ Bestellhistorie in der Cloud löschen"):
            alle_bestellungen_loeschen()
            st.rerun()

# ====== 2. DRIVER INTERFACE ======
elif rolle == "🚗 Fahrer-Ansicht (Mobil)":
    st.header("Kurier-App (Unterwegs)")
    fahrer_name = "Petr (Auto)"
    st.info(f"Eingeloggt als Fahrer: **{fahrer_name}**")
    
    if "bargeld_eur" not in st.session_state:
        st.session_state.bargeld_eur = 0.0
        st.session_state.provision_eur = 0.0

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Meine heutige Provision (fix)", f"{st.session_state.provision_eur:.2f} €")
    with c2:
        st.metric("Eingenommenes Bargeld (Limit 200€)", f"{st.session_state.bargeld_eur:.2f} / 200.00 €")
    
    if st.session_state.bargeld_eur >= 200:
        st.error("🛑 Bargeldlimit erreicht! Du musst das Geld im Restaurant abgeben.")

    st.write("---")
    st.subheader("Aktuell zugewiesener Auftrag")
    
    docs = bestellungen_laden()
    auftrag_gefunden = False
    
    for d in docs:
        f = d["fields"]
        if f["kuryr"]["stringValue"] == fahrer_name and f["stav"]["stringValue"] != "Geliefert":
            auftrag_gefunden = True
            doc_name = d["name"]
            
            st.warning(f"🔔 NEUER AUFTRAG ZUGEWIESEN (Zeit: {f['cas']['stringValue']})")
            st.write(f"🍱 **Inhalt:** {f['obsah']['stringValue']}")
            st.write(f"📍 **Lieferdetails:** {f['adresa']['stringValue']}")
            st.write(f"💶 **Zu kassierender Betrag:** {f['cena']['stringValue']} € ({f['platba']['stringValue']})")
            st.write(f"Aktueller Status: `{f['stav']['stringValue']}`")
            
            if f["stav"]["stringValue"] == "Wartet auf Bestätigung":
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("👍 Akzeptieren & zum Restaurant fahren", use_container_width=True):
                        bestellstatus_aktualisieren(doc_name, "Abgeholt / Auf dem Weg zum Kunden", fahrer_name)
                        st.rerun()
                with col_b:
                    if st.button("👎 Ablehnen", use_container_width=True):
                        bestellstatus_aktualisieren(doc_name, "Wartet auf Bestätigung", "Ersatzkurier (Honza)")
                        st.rerun()
                        
            elif f["stav"]["stringValue"] == "Abgeholt / Auf dem Weg zum Kunden":
                if st.button("✅ An Kunden geliefert (Abschließen)", type="primary", use_container_width=True):
                    bestellstatus_aktualisieren(doc_name, "Geliefert", fahrer_name)
                    st.session_state.provision_eur += 4.00
                    if f["platba"]["stringValue"] == "Barzahlung":
                        st.session_state.bargeld_eur += float(f["cena"]["stringValue"])
                    st.success("Erledigt! Das Geld wurde in deiner Übersicht gutgeschrieben.")
                    st.rerun()
            break
            
    if not auftrag_gefunden:
        st.info("Kein neuer Auftrag. Warte darauf, dass das Restaurant eine Bestellung sendet...")
