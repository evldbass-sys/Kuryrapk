import streamlit as st
import requests
import json
import time
from datetime import datetime, timedelta

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
    "🏬 2. Kassa / Eingabe (C3)",
    "👨‍🍳 3. Küche Monitor (C2)", 
    "🚗 4. Fahrer-Ansicht (Mobil & Finanzen)"
])

menue = {"Oklahoma Burger": 10.90, "Pommes": 4.00, "Curly Fries": 4.00, "Pepsi": 3.00, "Fanta Dose": 3.00}
RESTAURANT_NAME = "Smash Brothers"

# ====== 1. KUNDEN-ANSICHT ======
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
                    "adresa": f"{k_adresse} | Kunde: {k_name} | Tel: {k_telefon}",
                    "stav": "Wartet auf Bestätigung durch Kassa",
                    "kuryr": "Noch kein Fahrer",
                    "cas": datetime.now().strftime("%H:%M:%S"),
                    "dysko": f"{k_trinkgeld:.2f}"
                }
                bestellung_speichern(neue_bestellung)
                st.session_state.kunden_korb = {artikel: 0 for artikel in menue}
                st.success("🎉 Abgesendet! Deine Bestellung wird an der Kassa geprüft.")
                st.rerun()

# ====== 2. KASSA / EINGABE (C3) ======
elif rolle == "🏬 2. Kassa / Eingabe (C3)":
    st.header(f"🏬 Pokladna a příjem objednávek – {RESTAURANT_NAME}")
    docs = bestellungen_laden()
    
    st.subheader("🔔 Příchozí ONLINE objednávky")
    online_gefunden = False
    for d in docs:
        f = d["fields"]
        status = f["stav"]["stringValue"]
        doc_name = d["name"]
        
        if status == "Wartet auf Bestätigung durch Kassa":
            online_gefunden = True
            with st.container(border=True):
                col_o1, col_o2 = st.columns([3, 1])
                with col_o1:
                    st.markdown(f"**📦 {f['obsah']['stringValue']}** ({f['cena']['stringValue']} €)")
                with col_o2:
                    if st.button("✔️ Přijmout & Do kuchyně", key=f"prij_online_{doc_name}", type="primary", use_container_width=True):
                        bestellstatus_aktualisieren(doc_name, "In Zubereitung (Küche)", "Petr (Auto)", f["adresa"]["stringValue"])
                        st.rerun()
                        
    if not online_gefunden:
        st.info("Žádné nové online objednávky.")
        
    st.write("---")
    st.subheader("✍️ Manuální zadání nové objednávky")
    
    if "rest_korb" not in st.session_state:
        st.session_state.rest_korb = {artikel: 0 for artikel in menue}
        
    col_kassa_1, col_kassa_2 = st.columns([1, 1])
    with col_kassa_1:
        for artikel, preis in menue.items():
            cx1, cx2, cx3 = st.columns([2, 1, 1])
            with cx1: st.write(f"**{artikel}** ({preis:.2f}€)")
            with cx2:
                if st.button("➕", key=f"r_add_{artikel}"): st.session_state.rest_korb[artikel] += 1
            with cx3:
                if st.session_state.rest_korb[artikel] > 0:
                    st.write(f"**{st.session_state.rest_korb[artikel]}x**")
                    if st.button("❌", key=f"r_rem_{artikel}"): st.session_state.rest_korb[artikel] = 0
                    
    with col_kassa_2:
        r_artikel = []
        r_summe = 0.0
        for artikel, anzahl in st.session_state.rest_korb.items():
            if anzahl > 0:
                r_artikel.append(f"{anzahl}x {artikel}")
                r_summe += menue[artikel] * anzahl
                
        st.metric("Celkem", f"{r_summe:.2f} €")
        r_name = st.text_input("Jméno zákazníka", "Telefonický zákazník", key="r_name")
        r_adresse = st.text_input("Adresa doručení", "Ennser Straße 5, Steyr", key="r_adr")
        r_zahlung = st.selectbox("Způsob platby", ["Barzahlung", "Online-Karte"], key="r_zahl")
        
        if st.button("📥 POSLAT ROVNOU DO KUCHYNĚ", type="primary", use_container_width=True):
            if r_artikel == []:
                st.error("Prázdný košík!")
            else:
                neue_bestellung = {
                    "obsah": ", ".join(r_artikel),
                    "cena": f"{r_summe:.2f}",
                    "platba": r_zahlung,
                    "adresa": f"{r_adresse} | Kunde: {r_name}",
                    "stav": "In Zubereitung (Küche)",
                    "kuryr": "Petr (Auto)",
                    "cas": datetime.now().strftime("%H:%M:%S"),
                    "dysko": "0.00"
                }
                bestellung_speichern(neue_bestellung)
                st.session_state.rest_korb = {artikel: 0 for artikel in menue}
                st.success("Odesláno kuchařům!")
                st.rerun()

    st.write("---")
    if st.button("🗑️ Resetovat celou testovací databázi"):
        alle_bestellungen_loeschen()
        st.rerun()

# ====== 3. KÜCHE MONITOR ======
elif rolle == "👨‍🍳 3. Küche Monitor (C2)":
    st.header("👨‍🍳 Monitor v kuchyni (Zadní část)")
    docs = bestellungen_laden()
    offene_kueche = False
    
    for d in docs:
        f = d["fields"]
        status = f["stav"]["stringValue"]
        doc_name = d["name"]
        
        if status == "In Zubereitung (Küche)":
            offene_kueche = True
            with st.container(border=True):
                st.markdown(f"### 🍔 **{f['obsah']['stringValue']}**")
                if st.button(f"✅ HOTOVO / ZABALENO NA BAR", key=f"hotovo_kuch_{doc_name}", type="primary", use_container_width=True):
                    bestellstatus_aktualisieren(doc_name, "Ready for Pick-up", "Petr (Auto)", f["adresa"]["stringValue"])
                    st.success("Označeno jako hotové!")
                    time.sleep(0.5)
                    st.rerun()
            st.write("")
            
    if not offene_kueche:
        st.info("V kuchyni aktuálně není nic k vaření. ✨")

# ====== 4. FAHRER-ANSICHT S DYNAMICKÝM ČASEM A ALARMEM ======
elif rolle == "🚗 4. Fahrer-Ansicht (Mobil & Finanzen)":
    st.header("Kurier-App (Unterwegs)")
    fahrer_name = "Petr (Auto)"
    
    if "bargeld_eur" not in st.session_state:
        st.session_state.bargeld_eur = 0.0
        st.session_state.provision_eur = 0.0
        st.session_state.trinkgeld_eur = 0.0

    # Statistiky financí
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Meine Provision", f"{st.session_state.provision_eur:.2f} €")
    with c2: st.metric("Erhaltenes Dýško", f"{st.session_state.trinkgeld_eur:.2f} €")
    with c3: st.metric("Cash (Limit 200€)", f"{st.session_state.bargeld_eur:.2f} / 200.00 €")
    st.write("---")
    
    if st.session_state.bargeld_eur >= 200.0:
        st.error("🛑 BARGELDLIMIT ERREICHT! Žádné další zakázky.")
        if st.button("💰 Geld in der Hauptstation (Volt and value) abgegeben"):
            st.session_state.bargeld_eur = 0.0
            st.rerun()
    else:
        st.subheader("Aktuell zugewiesener Auftrag")
        docs = bestellungen_laden()
        auftrag_gefunden = False
        
        for d in docs:
            f = d["fields"]
            status = f["stav"]["stringValue"]
            doc_name = d["name"]
            dysko_val = f.get("dysko", {}).get("stringValue", "0.00")
            
            if status in ["In Zubereitung (Küche)", "Ready for Pick-up", "Auf dem Weg zum Kunden"]:
                if f["kuryr"]["stringValue"] == fahrer_name:
                    auftrag_gefunden = True
                    
                    st.markdown(f"### 📍 Vyzvednout v: **{RESTAURANT_NAME}**")
                    st.write(f"🍱 **Jídlo:** {f['obsah']['stringValue']}")
                    st.write(f"💰 **Dýško:** {dysko_val} €")
                    
                    # === SCÉNÁŘ A: JÍDLO SE VAŘÍ (Standardní odpočet času) ===
                    if status == "In Zubereitung (Küche)":
                        st.info("⏳ Jídlo se připravuje.")
                        # Simulace: Kurýr vidí standardní čas, dokud kuchař nemáchne rukou
                        st.markdown(
                            "<div style='padding:20px;background-color:#FFF3CD;border-radius:10px;text-align:center;'>"
                            "<h2 style='color:#856404;margin:0;'>⏱️ Plánovaný čas přípravy: cca 10 minut</h2>"
                            "<p style='margin:5px 0 0 0;'>Máš čas, jeď v klidu k restauraci.</p>"
                            "</div>", 
                            unsafe_allow_html=True
                        )
                        if st.button("🔄 Aktualizovat stav (Přijelo jídlo už?)"):
                            st.rerun()
                        
                    # === SCÉNÁŘ B: KUCHAŘ KLIKNUL HOTOVO (Změna na poplach!) ===
                    elif status == "Ready for Pick-up":
                        # Ostrý červeno-blikající box, který kurýra donutí kopnout do vrtule
                        st.markdown(
                            "<div style='padding:20px;background-color:#F8D7DA;border-left:8px solid #DC3545;border-radius:5px;'>"
                            "<h2 style='color:#721C24;margin:0;'>🚨 KUCHAŘ BYL RYCHLEJŠÍ! JÍDLO JE HOTOVÉ!</h2>"
                            "<p style='color:#721C24;font-size:16px;margin:5px 0 0 0;'><b>Urychleně doraž na bar Smash Brothers! Jídlo už na tebe čeká zabalené a chladne!</b></p>"
                            "</div>", 
                            unsafe_allow_html=True
                        )
                        st.write("")
                        if st.button("👍 Potvrdit převzetí jídla na baru", type="primary", use_container_width=True):
                            bestellstatus_aktualisieren(doc_name, "Auf dem Weg zum Kunden", fahrer_name, f["adresa"]["stringValue"])
                            st.rerun()
                            
                    # === SCÉNÁŘ C: ROZVOZ NA ADRESU ===
                    elif status == "Auf dem Weg zum Kunden":
                        st.success("🔓 ADRESA ODEMČENA:")
                        st.write(f"➡️ **Kam jedeš:** {f['adresa']['stringValue']}")
                        
                        if st.button("✅ Doručeno & Kassiert (Ukončit)", type="primary", use_container_width=True):
                            st.session_state.provision_eur += 4.00
                            st.session_state.trinkgeld_eur += float(dysko_val)
                            if f["platba"]["stringValue"] == "Barzahlung":
                                st.session_state.bargeld_eur += float(f["cena"]["stringValue"])
                            
                            bestellstatus_aktualisieren(doc_name, "Geliefert", fahrer_name, f["adresa"]["stringValue"])
                            st.success("Hotovo!")
                            time.sleep(0.5)
                            st.rerun()
                    break
                    
        if not auftrag_gefunden:
            st.info("Žádný aktivní rozvoz. Čekej na bar...")
