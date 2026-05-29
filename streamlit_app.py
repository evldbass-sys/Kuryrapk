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
    # Aktualizuje status, řidiče a případně připíše dýško do pole adresa/detaily
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
st.title("🚚 E-Commerce & Kuriersystem")
rolle = st.sidebar.radio("Rolle auswählen:", [
    "🏠 Kunden-Ansicht (Bestellung von zu Hause)", 
    "🏬 Restaurant-Ansicht (Eingang & Dispatch)", 
    "🚗 Fahrer-Ansicht (Mobil & Trinkgeld)"
])

# DEFINICE MENU PRO VŠECHNY POHLEDY
menue = {"Oklahoma Burger": 10.90, "Pommes": 4.00, "Curly Fries": 4.00, "Pepsi": 3.00, "Fanta Dose": 3.00}

# ====== 1. KUNDEN-ANSICHT (ZÁKAZNÍK DOMA) ======
if rolle == "🏠 Kunden-Ansicht (Bestellung von zu Hause)":
    st.header("🛒 Online-Shop – Essen nach Hause bestellen")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🍔 Speisekarte")
        if "kunden_korb" not in st.session_state:
            st.session_state.kunden_korb = {artikel: 0 for artikel in menue}
            
        for artikel, preis in menue.items():
            cc1, cc2, cc3 = st.columns([2, 1, 1])
            with cc1:
                st.write(f"**{artikel}** ({preis:.2f} €)")
            with cc2:
                if st.button(f"➕", key=f"kunden_add_{artikel}"):
                    st.session_state.kunden_korb[artikel] += 1
            with cc3:
                if st.session_state.kunden_korb[artikel] > 0:
                    st.write(f"**{st.session_state.kunden_korb[artikel]}x**")
                    if st.button(f"❌", key=f"kunden_rem_{artikel}"):
                        st.session_state.kunden_korb[artikel] = 0

    with col2:
        st.subheader("📋 Meine Bestellung")
        artikel_im_korb = []
        gesamtsumme = 0.0
        for artikel, anzahl in st.session_state.warenkorb.items() if "warenkorb" in st.session_state else st.session_state.kunden_korb.items():
            # Použijeme kunden_korb pro čisté zadávání
            pass
        
        # Oprava pro správné načítání košíku zákazníka
        for artikel, anzahl in st.session_state.kunden_korb.items():
            if anzahl > 0:
                preis_pro_posten = menue[artikel] * anzahl
                artikel_im_korb.append(f"{anzahl}x {artikel}")
                gesamtsumme += preis_pro_posten
                st.text(f"• {anzahl}x {artikel} = {preis_pro_posten:.2f} €")
                
        st.write("---")
        st.metric("Gesamtsumme", f"{gesamtsumme:.2f} €")
        
        k_name = st.text_input("Mein Name", "Max Mustermann", key="k_name")
        k_telefon = st.text_input("Meine Telefonnummer", "+43 660 1234567", key="k_tel")
        k_adresse = st.text_input("Lieferadresse (Straße, Hausnummer, Ort)", "Hauptstraße 12, Steyr", key="k_adr")
        k_zahlung = st.selectbox("Zahlungsart", ["Online-Karte", "Barzahlung"], key="k_zahl")
        
        if artikel_im_korb == []:
            st.info("Dein Warenkorb ist leer. Wähle links Produkte aus.")
        else:
            if st.button("🚀 JETZT KOSTENPFLICHTIG BESTELLEN", type="primary", use_container_width=True):
                neue_bestellung = {
                    "obsah": ", ".join(artikel_im_korb),
                    "cena": f"{gesamtsumme:.2f}",
                    "platba": k_zahlung,
                    "adresa": f"{k_adresse} | Kunde: {k_name} | Tel: {k_telefon}",
                    "stav": "Neu eingegangen (Wartet auf Restaurant)",
                    "kuryr": "Noch kein Fahrer",
                    "cas": datetime.now().strftime("%H:%M:%S")
                }
                bestellung_speichern(neue_bestellung)
                st.session_state.kunden_korb = {artikel: 0 for artikel in menue}
                st.success("🎉 Danke für deine Bestellung! Das Restaurant bearbeitet sie jetzt.")
                st.rerun()

# ====== 2. RESTAURANT DASHBOARD (ADMINISTRACE) ======
elif rolle == "🏬 Restaurant-Ansicht (Eingang & Dispatch)":
    st.header("Restaurant Dashboard – Bestellungen verwalten")
    
    st.subheader("📥 Offene Bestellungen von Kunden")
    docs = bestellungen_laden()
    neue_auftraege_da = False
    
    for d in docs:
        f = d["fields"]
        if f["stav"]["stringValue"] in ["Neu eingegangen (Wartet auf Restaurant)", "Wartet auf Bestätigung"]:
            neue_auftraege_da = True
            doc_name = d["name"]
            
            with st.container():
                st.write(f"**Zeit:** {f['cas']['stringValue']} | **Betrag:** {f['cena']['stringValue']} € ({f['platba']['stringValue']})")
                st.write(f"📦 **Inhalt:** {f['obsah']['stringValue']}")
                st.write(f"📍 **Details:** {f['adresa']['stringValue']}")
                st.write(f"Aktueller Status: `{f['stav']['stringValue']}`")
                
                if f["stav"]["stringValue"] == "Neu eingegangen (Wartet auf Restaurant)":
                    if st.button(f"✈️ AN KURIER PETR ZUWEISEN", key=f"disp_{doc_name}"):
                        bestellstatus_aktualisieren(doc_name, "Wartet auf Bestätigung", "Petr (Auto)", f["adresa"]["stringValue"])
                        st.success("An den Kurier übermittelt!")
                        st.rerun()
                st.write("---")
                
    if not neue_auftraege_da:
        st.info("Aktuell keine neuen Bestellungen im Eingang.")
        
    st.write("---")
    if st.button("🗑️ Gesamte Cloud-Historie löschen"):
        alle_bestellungen_loeschen()
        st.rerun()

# ====== 3. DRIVER INTERFACE (KURIER S DÝŠKEM) ======
elif rolle == "🚗 Fahrer-Ansicht (Mobil & Trinkgeld)":
    st.header("Kurier-App (Unterwegs)")
    fahrer_name = "Petr (Auto)"
    st.info(f"Eingeloggt als Fahrer: **{fahrer_name}**")
    
    if "bargeld_eur" not in st.session_state:
        st.session_state.bargeld_eur = 0.0
        st.session_state.provision_eur = 0.0
        st.session_state.trinkgeld_gesamt = 0.0

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Meine Provision (fix)", f"{st.session_state.provision_eur:.2f} €")
    with c2:
        st.metric("Mein erhaltenes Dýško (Trinkgeld)", f"{st.session_state.trinkgeld_gesamt:.2f} €")
    with c3:
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
                    if st.button("👍 Akzeptieren & hinfahren", use_container_width=True):
                        bestellstatus_aktualisieren(doc_name, "Abgeholt / Auf dem Weg zum Kunden", fahrer_name, f["adresa"]["stringValue"])
                        st.rerun()
                with col_b:
                    if st.button("👎 Ablehnen", use_container_width=True):
                        bestellstatus_aktualisieren(doc_name, "Neu eingegangen (Wartet auf Restaurant)", "Noch kein Fahrer", f["adresa"]["stringValue"])
                        st.rerun()
                        
            elif f["stav"]["stringValue"] == "Abgeholt / Auf dem Weg zum Kunden":
                # Kolonka na dýško před dokončením
                trinkgeld_input = st.number_input("Trinkgeld erhalten (€)", min_value=0.0, max_value=50.0, value=0.0, step=0.5)
                
                if st.button("✅ An Kunden geliefert (Abschließen)", type="primary", use_container_width=True):
                    # Přičteme fixní odměnu 4€ a dýško
                    st.session_state.provision_eur += 4.00
                    st.session_state.trinkgeld_gesamt += trinkgeld_input
                    
                    # Pokud platil hotově, přičteme peníze do peněženky kurýra
                    if f["platba"]["stringValue"] == "Barzahlung":
                        st.session_state.bargeld_eur += float(f["cena"]["stringValue"])
                    
                    # Uložíme informaci o dýšku přímo k adrese do databáze pro kontrolu v restauraci
                    neue_details = f"{f['adresa']['stringValue']} | 💰 Dýško: {trinkgeld_input:.2f} €"
                    bestellstatus_aktualisieren(doc_name, "Geliefert", fahrer_name, neue_details)
                    
                    st.success(f"Erledigt! +4.00 € Provision und +{trinkgeld_input:.2f} € Trinkgeld wurden verbucht.")
                    time.sleep(1)
                    st.rerun()
            break
            
    if not auftrag_gefunden:
        st.info("Kein neuer Auftrag. Warte auf Bestellungen...")
