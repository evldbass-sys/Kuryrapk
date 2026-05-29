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
st.title("🚚 Lieferdienst Management System")
rolle = st.sidebar.radio("Rolle auswählen:", [
    "🏠 1. Kunden-Ansicht (Bestellung von zu Hause)", 
    "🏬 2. & 3. Restaurant-Ansicht (Küche & Eingabe)", 
    "🚗 Fahrer-Ansicht (Mobil)"
])

menue = {"Oklahoma Burger": 10.90, "Pommes": 4.00, "Curly Fries": 4.00, "Pepsi": 3.00, "Fanta Dose": 3.00}
RESTAURANT_NAME = "Smash Brothers"

# ====== C1. KUNDEN-ANSICHT (ZÁKAZNÍK DOMA) ======
if rolle == "🏠 1. Kunden-Ansicht (Bestellung von zu Hause)":
    st.header("🛒 Online-Shop – Smash Brothers")
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
        st.subheader("📋 Meine Bestellung (C1)")
        artikel_im_korb = []
        gesamtsumme = 0.0
        
        for artikel, anzahl in st.session_state.kunden_korb.items():
            if anzahl > 0:
                preis_pro_posten = menue[artikel] * anzahl
                artikel_im_korb.append(f"{anzahl}x {artikel}")
                gesamtsumme += preis_pro_posten
                st.text(f"• {anzahl}x {artikel} = {preis_pro_posten:.2f} €")
                
        st.write("---")
        st.metric("Gesamtsumme (Essen)", f"{gesamtsumme:.2f} €")
        
        k_trinkgeld = st.number_input("Trinkgeld für den Fahrer (€)", min_value=0.0, max_value=20.0, value=0.0, step=0.5, key="k_trinkgeld")
        k_name = st.text_input("Mein Name", "Max Mustermann", key="k_name")
        k_telefon = st.text_input("Meine Telefonnummer", "+43 660 1234567", key="k_tel")
        k_adresse = st.text_input("Lieferadresse", "Hauptstraße 12, Steyr", key="k_adr")
        k_zahlung = st.selectbox("Zahlungsart", ["Online-Karte", "Barzahlung"], key="k_zahl")
        
        if artikel_im_korb == []:
            st.info("Dein Warenkorb ist leer.")
        else:
            if st.button("🚀 BESTELLUNG ABSENDEN", type="primary", use_container_width=True):
                neue_bestellung = {
                    "obsah": ", ".join(artikel_im_korb),
                    "cena": f"{gesamtsumme:.2f}",
                    "platba": k_zahlung,
                    "adresa": f"{k_adresse} | Kunde: {k_name} | Tel: {k_telefon} | 💰 Dýško: {k_trinkgeld:.2f} €",
                    "stav": "Neu eingegangen (Wartet auf Küche)",
                    "kuryr": "Noch kein Fahrer",
                    "cas": datetime.now().strftime("%H:%M:%S")
                }
                bestellung_speichern(neue_bestellung)
                st.session_state.kunden_korb = {artikel: 0 for artikel in menue}
                st.success("🎉 Abgesendet! Warte na potvrzení kuchyní.")
                st.rerun()

# ====== C2 + C3. RESTAURANT ANSICHT (ZADÁVÁNÍ + KUCHYŇ) ======
elif rolle == "🏬 2. & 3. Restaurant-Ansicht (Küche & Eingabe)":
    st.header(f"🏬 Dashboard – {RESTAURANT_NAME}")
    
    col_eingabe, col_kueche = st.columns([1, 1])
    
    # --- C3: RESTAURANT EINGABE (LEVÝ SLOUPEC) ---
    with col_eingabe:
        st.subheader("✍️ 3. Manuelle Eingabe (Restaurant)")
        if "rest_korb" not in st.session_state:
            st.session_state.rest_korb = {artikel: 0 for artikel in menue}
            
        for artikel, preis in menue.items():
            cx1, cx2, cx3 = st.columns([2, 1, 1])
            with cx1:
                st.write(f"{artikel} ({preis:.2f}€)")
            with cx2:
                if st.button("➕", key=f"r_add_{artikel}"):
                    st.session_state.rest_korb[artikel] += 1
            with cx3:
                if st.session_state.rest_korb[artikel] > 0:
                    st.write(f"**{st.session_state.rest_korb[artikel]}x**")
                    
        st.write("---")
        r_artikel = []
        r_summe = 0.0
        for artikel, anzahl in st.session_state.rest_korb.items():
            if anzahl > 0:
                r_artikel.append(f"{anzahl}x {artikel}")
                r_summe += menue[artikel] * anzahl
                
        st.metric("Summe", f"{r_summe:.2f} €")
        r_name = st.text_input("Kundenname", "Telefonischer Kunde", key="r_name")
        r_telefon = st.text_input("Telefonnummer", "+43 ", key="r_tel")
        r_adresse = st.text_input("Lieferadresse", "Ennser Straße 5, Steyr", key="r_adr")
        r_zahlung = st.selectbox("Zahlung", ["Barzahlung", "Online-Karte"], key="r_zahl")
        
        if st.button("📥 AN DIE KÜCHE SENDEN (C3)", type="primary", use_container_width=True):
            if r_artikel == []:
                st.error("Warenkorb leer!")
            else:
                neue_bestellung = {
                    "obsah": ", ".join(r_artikel),
                    "cena": f"{r_summe:.2f}",
                    "platba": r_zahlung,
                    "adresa": f"{r_adresse} | Kunde: {r_name} | Tel: {r_telefon} | 💰 Dýško: 0.00 €",
                    "stav": "Neu eingegangen (Wartet auf Küche)",
                    "kuryr": "Noch kein Fahrer",
                    "cas": datetime.now().strftime("%H:%M:%S")
                }
                bestellung_speichern(neue_bestellung)
                st.session_state.rest_korb = {artikel: 0 for artikel in menue}
                st.success("An Küche übermittelt!")
                st.rerun()

    # --- C2: KÜCHE (PRAVÝ SLOUPEC) ---
    with col_kueche:
        st.subheader("👨‍🍳 2. Küche Monitor")
        docs = bestellungen_laden()
        offene_kueche = False
        
        for d in docs:
            f = d["fields"]
            status = f["stav"]["stringValue"]
            doc_name = d["name"]
            
            if status in ["Neu eingegangen (Wartet auf Küche)", "In Zubereitung / Akzeptiert"]:
                offene_kueche = True
                st.info(f"⏱️ **Zeit:** {f['cas']['stringValue']} | **Status:** `{status}`")
                st.write(f"📦 **Essen:** {f['obsah']['stringValue']}")
                st.write(f"📍 **Details:** {f['adresa']['stringValue']}")
                
                if status == "Neu eingegangen (Wartet auf Küche)":
                    if st.button(f"✔️ Přijmout do kuchyně (C2)", key=f"prij_kuch_{doc_name}", use_container_width=True):
                        # Změní stav na Akzeptiert, v tom momentě to naskočí řidiči!
                        bestellstatus_aktualisieren(doc_name, "In Zubereitung / Akzeptiert", "Petr (Auto)", f["adresa"]["stringValue"])
                        st.rerun()
                elif status == "In Zubereitung / Akzeptiert":
                    st.success("🍳 Essen wird zubereitet... (Wartet auf Kurier-Abholung)")
                st.write("---")
                
        if not offene_kueche:
            st.text("Keine Aufträge in der Küche.")
            
    st.write("---")
    if st.button("🗑️ Gesamte Cloud-Historie löschen"):
        alle_bestellungen_loeschen()
        st.rerun()

# ====== KURIER INTERFACE ======
elif rolle == "🚗 Fahrer-Ansicht (Mobil)":
    st.header("Kurier-App (Unterwegs)")
    fahrer_name = "Petr (Auto)"
    st.info(f"Eingeloggt als: **{fahrer_name}**")
    
    docs = bestellungen_laden()
    auftrag_gefunden = False
    
    for d in docs:
        f = d["fields"]
        status = f["stav"]["stringValue"]
        doc_name = d["name"]
        
        # Kurýr vidí zakázku, jakmile ji kuchyň přijme (nebo už je na cestě)
        if status in ["In Zubereitung / Akzeptiert", "Auf dem Weg zum Kunden"]:
            if f["kuryr"]["stringValue"] == fahrer_name:
                auftrag_gefunden = True
                st.warning(f"🔔 AUFTRAG BEREIT!")
                st.subheader(f"📍 Abholen bei: {RESTAURANT_NAME}")
                st.write(f"🍱 **Inhalt:** {f['obsah']['stringValue']}")
                st.write(f"💶 **Wert:** {f['cena']['stringValue']} € ({f['platba']['stringValue']})")
                
                if status == "In Zubereitung / Akzeptiert":
                    st.info("ℹ️ Adressendetails werden nach Bestätigung der Abholung angezeigt.")
                    if st.button("👍 Potvrdit vyzvednutí (Kurýr)", type="primary", use_container_width=True):
                        bestellstatus_aktualisieren(doc_name, "Auf dem Weg zum Kunden", fahrer_name, f["adresa"]["stringValue"])
                        st.rerun()
                        
                elif status == "Auf dem Weg zum Kunden":
                    st.success("🔓 ADRESSE FREIGESCHALTET:")
                    st.write(f"➡️ **Wohin du fährst:** {f['adresa']['stringValue']}")
                    
                    if st.button("✅ Geliefert (Erledigt)", use_container_width=True):
                        bestellstatus_aktualisieren(doc_name, "Geliefert", fahrer_name, f["adresa"]["stringValue"])
                        st.success("Abgeschlossen!")
                        time.sleep(1)
                        st.rerun()
                break
                
    if not auftrag_gefunden:
        st.info("Kein neuer Auftrag. Warte darauf, dass die Küche eine Bestellung annimmt...")
