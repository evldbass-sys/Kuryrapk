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

# ====== NAVIGATION (Německé menu pro personál) ======
st.title("🚚 Lieferdienst Management System")
rolle = st.sidebar.radio("Bereich auswählen:", [
    "🏠 1. Kunden-Ansicht (Bestellung von zu Hause)", 
    "🏬 2. Kassa / Eingabe (Theke)",
    "👨‍🍳 3. Küche Monitor", 
    "🚗 4. Fahrer-Ansicht (Mobil & Finanzen)"
])

menue = {"Oklahoma Burger": 10.90, "Pommes": 4.00, "Curly Fries": 4.00, "Pepsi": 3.00, "Fanta Dose": 3.00}
RESTAURANT_NAME = "Smash Brothers"

# ====== 1. KUNDEN-ANSICHT (ZÁKAZNÍK DOMA) ======
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
        st.subheader("📋 Meine Bestellung")
        artikel_im_korb = []
        gesamtsumme = 0.0
        
        for artikel, anzahl in st.session_state.kunden_korb.items():
            if anzahl > 0:
                preis_pro_posten = menue[artikel] * anzahl
                artikel_im_korb.append(f"{anzahl}x {artikel}")
                gesamtsumme += preis_pro_posten
                st.text(f"• {anzahl}x {artikel} = {preis_pro_posten:.2f} €")
                
        st.write("---")
        st.metric("Gesamtsumme", f"{gesamtsumme:.2f} €")
        
        k_trinkgeld = st.number_input("Trinkgeld für den Fahrer (€)", min_value=0.0, max_value=20.0, value=0.0, step=0.5, key="k_trinkgeld")
        k_name = st.text_input("Name", "Max Mustermann", key="k_name")
        k_telefon = st.text_input("Telefonnummer", "+43 660 1234567", key="k_tel")
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

# ====== 2. KASSA / EINGABE (POKLADNA NA BARU) ======
elif rolle == "🏬 2. Kassa / Eingabe (Theke)":
    st.header(f"🏬 Kassa & Auftragsannahme – {RESTAURANT_NAME}")
    docs = bestellungen_laden()
    
    st.subheader("🔔 Eingehende ONLINE-Bestellungen (Bestätigung erforderlich)")
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
                    st.markdown(f"**📦 {f['obsah']['stringValue']}** ({f['cena']['stringValue']} € - {f['platba']['stringValue']})")
                    st.text(f"📍 {f['adresa']['stringValue']} | Zeit: {f['cas']['stringValue']}")
                with col_o2:
                    if st.button("✔️ Bestätigen & In Küche senden", key=f"prij_online_{doc_name}", type="primary", use_container_width=True):
                        bestellstatus_aktualisieren(doc_name, "In Zubereitung (Küche)", "Petr (Auto)", f["adresa"]["stringValue"])
                        st.rerun()
                        
    if not online_gefunden:
        st.info("Keine neuen Online-Bestellungen zur Bestätigung.")
        
    st.write("---")

    st.subheader("✍️ Manuelle Bestelleingabe (Telefon / Tresen)")
    if "rest_korb" not in st.session_state:
        st.session_state.rest_korb = {artikel: 0 for artikel in menue}
        
    col_kassa_1, col_kassa_2 = st.columns([1, 1])
    
    with col_kassa_1:
        for artikel, preis in menue.items():
            cx1, cx2, cx3 = st.columns([2, 1, 1])
            with cx1:
                st.write(f"**{artikel}** ({preis:.2f}€)")
            with cx2:
                if st.button("➕", key=f"r_add_{artikel}"):
                    st.session_state.rest_korb[artikel] += 1
            with cx3:
                if st.session_state.rest_korb[artikel] > 0:
                    st.write(f"**{st.session_state.rest_korb[artikel]}x**")
                    if st.button("❌", key=f"r_rem_{artikel}"):
                        st.session_state.rest_korb[artikel] = 0
                    
    with col_kassa_2:
        r_artikel = []
        r_summe = 0.0
        for artikel, anzahl in st.session_state.rest_korb.items():
            if anzahl > 0:
                r_artikel.append(f"{anzahl}x {artikel}")
                r_summe += menue[artikel] * anzahl
                st.text(f"• {anzahl}x {artikel} = {(menue[artikel] * anzahl):.2f} €")
                
        st.write("---")
        st.metric("Gesamtsumme", f"{r_summe:.2f} €")
        r_name = st.text_input("Kundenname", "Telefonischer Kunde", key="r_name")
        r_adresse = st.text_input("Lieferadresse", "Ennser Straße 5, Steyr", key="r_adr")
        r_zahlung = st.selectbox("Zahlungsart", ["Barzahlung", "Online-Karte"], key="r_zahl")
        
        if st.button("📥 DIREKT IN DIE KÜCHE SENDEN", type="primary", use_container_width=True):
            if r_artikel == []:
                st.error("Warenkorb leer!")
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
                st.success("Erfolgreich in die Küche gesendet!")
                st.rerun()

    st.write("---")
    if st.button("🗑️ Gesamte Cloud-Historie löschen (Reset za účelem testování)"):
        alle_bestellungen_loeschen()
        st.rerun()

# ====== 3. KÜCHE MONITOR (MONITOR V KUCHYNI) ======
elif rolle == "👨‍🍳 3. Küche Monitor":
    st.header("👨‍🍳 Küche Monitor (Zubereitung)")
    st.write("Aktive Bestellungen, die zubereitet werden müssen. Nach der Fertigstellung bitte auf 'FERTIG' klicken.")
    
    docs = bestellungen_laden()
    offene_kueche = False
    
    for d in docs:
        f = d["fields"]
        status = f["stav"]["stringValue"]
        doc_name = d["name"]
        
        if status == "In Zubereitung (Küche)":
            offene_kueche = True
            
            with st.container(border=True):
                col_k1, col_k2 = st.columns([3, 1])
                with col_k1:
                    st.markdown(f"### 🍔 **{f['obsah']['stringValue']}**")
                    st.text(f"⏱️ Zeit: {f['cas']['stringValue']} | Kassa: {f['platba']['stringValue']}")
                    st.text(f"📍 Details: {f['adresa']['stringValue']}")
                with col_k2:
                    if st.button(f"✅ FERTIG / VERPACKT", key=f"hotovo_kuch_{doc_name}", type="primary", use_container_width=True):
                        bestellstatus_aktualisieren(doc_name, "Ready for Pick-up", "Petr (Auto)", f["adresa"]["stringValue"])
                        st.success("Als FERTIG markiert!")
                        time.sleep(0.5)
                        st.rerun()
            st.write("")
            
    if not offene_kueche:
        st.info("Aktuell keine Bestellungen in der Küche. Gute Arbeit! ✨")

# ====== 4. FAHRER-ANSICHT (APLIKACE KURÝRA - PODPORUJE PENDL S VÍCE OBJEDNÁVKAMI) ======
elif rolle == "🚗 4. Fahrer-Ansicht (Mobil & Finanzen)":
    st.header("Kurier-App (Unterwegs)")
    fahrer_name = "Petr (Auto)"
    st.info(f"Eingeloggt als: **{fahrer_name}**")
    
    if "bargeld_eur" not in st.session_state:
        st.session_state.bargeld_eur = 0.0
        st.session_state.provision_eur = 0.0
        st.session_state.trinkgeld_eur = 0.0

    st.subheader("📊 Meine Finanzübersicht")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Meine Provision (Fix 4€/Fahrt)", f"{st.session_state.provision_eur:.2f} €")
    with c2:
        st.metric("Erhaltenes Trinkgeld (Dýško)", f"{st.session_state.trinkgeld_eur:.2f} €")
    with c3:
        st.metric("Eingenommenes Bargeld (Limit 200€)", f"{st.session_state.bargeld_eur:.2f} / 200.00 €")
        
    st.write("---")
    
    # STOPKA PŘI 200 EURO - SMĚROVÁNÍ NA HLAVNÍ STANICI VOLT AND VALUE
    if st.session_state.bargeld_eur >= 200.0:
        st.error("🛑 BARGELDLIMIT ERREICHT! Du hast mehr als 200€ in bar. Es werden KEINE weiteren Bestellungen empfangen!")
        st.warning("⚠️ Fahre bitte sofort zur Hauptstation (Volt and value), um das Geld abzurechnen.")
        
        if st.button("💰 Geld in der Hauptstation (Volt and value) abgegeben (Reset Cash)", type="primary", use_container_width=True):
            st.session_state.bargeld_eur = 0.0
            st.success("Geld erfolgreich abgerechnet! Du bist wieder einsatzbereit.")
            time.sleep(1)
            st.rerun()
            
    else:
        st.subheader("Aktuelle Aufträge in der Pipeline")
        
        docs = bestellungen_laden()
        # Vytáhneme všechny objednávky, které patří Petrovi a nejsou ještě doručené
        aktive_auftraege = [d for d in docs if d["fields"]["kuryr"]["stringValue"] == fahrer_name 
                            and d["fields"]["stav"]["stringValue"] in ["In Zubereitung (Küche)", "Ready for Pick-up", "Auf dem Weg zum Kunden"]]
        
        if not aktive_auftraege:
            st.info("Kein aktiver Auftrag. Warte auf die Kassa...")
        else:
            # Projíždíme všechny aktivní zakázky najednou (každá dostane samostatnou pendl kartu)
            for d in aktive_auftraege:
                f = d["fields"]
                status = f["stav"]["stringValue"]
                doc_name = d["name"]
                dysko_val = f.get("dysko", {}).get("stringValue", "0.00")
                
                # Barevné a textové rozlišení stavu pro bleskový přehled na mobilu
                if status == "Ready for Pick-up":
                    border_color = "#28a745"   # Zelená - jídlo je hotové, seber ho
                    header_text = "🚨 DER KOCH WAR SCHNELLER! DAS ESSEN IST FERTIG!"
                elif status == "Auf dem Weg zum Kunden":
                    border_color = "#007bff"   # Modrá - vezeš k zákazníkovi
                    header_text = "🚚 AUF DEM WEG ZUM KUNDEN (ADRESSE OFFEN)"
                else:
                    border_color = "#ffc107"   # Žlutá - jídlo se ještě vaří
                    header_text = "⏳ IN ZUBEREITUNG (KÜCHE KOCHT NOCH)"

                with st.container(border=True):
                    st.markdown(f"<h3 style='color:{border_color}; margin-top:0;'>{header_text}</h3>", unsafe_allow_html=True)
                    st.markdown(f"**📍 Abholen bei:** {RESTAURANT_NAME}")
                    st.write(f"🍱 **Inhalt:** {f['obsah']['stringValue']}")
                    st.write(f"💶 **Zu kassieren:** {f['cena']['stringValue']} € ({f['platba']['stringValue']})")
                    st.write(f"💰 **Trinkgeld:** {dysko_val} €")
                    
                    # 1. STAV: Jídlo se vaří (Kuriér vidí standardní časový box)
                    if status == "In Zubereitung (Küche)":
                        st.markdown(
                            "<div style='padding:10px; background-color:#FFF3CD; border-radius:5px; margin-bottom:10px;'>"
                            "<b style='color:#856404;'>⏱️ Standard-Zeit: cca. 10 Minuten.</b> Du kannst in Ruhe hinfahren."
                            "</div>", 
                            unsafe_allow_html=True
                        )
                        if st.button("🔄 Aktualisieren", key=f"refresh_{doc_name}"):
                            st.rerun()
                            
                    # 2. STAV: Kuchyň klikla hotovo (Zelená karta, kurýr potvrdí pendl a naloží)
                    elif status == "Ready for Pick-up":
                        st.markdown("<b style='color:#28a745;'>Das Essen wartet verpackt an der Theke!</b>", unsafe_allow_html=True)
                        if st.button("👍 Abholung an der Theke bestätigen", key=f"pick_{doc_name}", type="primary", use_container_width=True):
                            bestellstatus_aktualisieren(doc_name, "Auf dem Weg zum Kunden", fahrer_name, f["adresa"]["stringValue"])
                            st.rerun()
                            
                    # 3. STAV: Rozvoz na adresu (Kurýr odemkl adresu a může ji dokončit nezávisle na druhé)
                    elif status == "Auf dem Weg zum Kunden":
                        st.success("🔓 LIEFERADRESSE FREIGESCHALTET:")
                        st.markdown(f"➡️ **Wohin du fährst:** `{f['adresa']['stringValue']}`")
                        
                        if st.button("✅ Geliefert & Kassiert (Abschließen)", key=f"deliver_{doc_name}", type="primary", use_container_width=True):
                            st.session_state.provision_eur += 4.00
                            st.session_state.trinkgeld_eur += float(dysko_val)
                            
                            if f["platba"]["stringValue"] == "Barzahlung":
                                st.session_state.bargeld_eur += float(f["cena"]["stringValue"])
                            
                            bestellstatus_aktualisieren(doc_name, "Geliefert", fahrer_name, f["adresa"]["stringValue"])
                            st.success("Erfolgreich abgeschlossen!")
                            time.sleep(0.5)
                            st.rerun()
