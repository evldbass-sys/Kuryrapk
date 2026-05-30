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

def bestellstatus_aktualisieren(doc_name, neuer_status, fahrer_name="", lieferdetails="", zubereitungszeit="10"):
    # Aktualizujeme stav, řidiče, adresu a dynamický čas přípravy
    url = f"https://firestore.googleapis.com/v1/{doc_name}?updateMask.fieldPaths=stav&updateMask.fieldPaths=kuryr&updateMask.fieldPaths=adresa&updateMask.fieldPaths=cas_pripravy"
    payload = {
        "fields": {
            "stav": {"stringValue": neuer_status},
            "kuryr": {"stringValue": fahrer_name},
            "adresa": {"stringValue": lieferdetails},
            "cas_pripravy": {"stringValue": str(zubereitungszeit)}
        }
    }
    requests.patch(url, json=payload)

def alle_bestellungen_loeschen():
    docs = bestellungen_laden()
    for d in docs:
        requests.delete(f"https://firestore.googleapis.com/v1/{d['name']}")

# ====== NAVIGATION ======
st.title("🚚 Lieferdienst Management System")
rolle = st.sidebar.radio("Bereich auswählen:", [
    "🏠 1. Kunden-Ansicht (Bestellung von zu Hause)", 
    "🏬 2. Kassa / Eingabe (Theke)",
    "👨‍🍳 3. Küche Monitor", 
    "🚗 4. Fahrer-Ansicht (Mobil & Finanzen)"
])

# Kompletní menu z letáku
menue = {
    "Cheese Burger": {"preis": 9.00, "icon": "🍔", "kat": "Smash Burger"},
    "Chili Cheese Burger": {"preis": 10.00, "icon": "🌶️", "kat": "Smash Burger"},
    "Double Trouble Burger": {"preis": 12.90, "icon": "🔥", "kat": "Smash Burger"},
    "Oklahoma Double Burger": {"preis": 12.90, "icon": "🧅", "kat": "Smash Burger"},
    "Double Beast Burger": {"preis": 12.90, "icon": "👹", "kat": "Smash Burger"},
    "Smash 'n' Egg": {"preis": 12.50, "icon": "🍳", "kat": "Smash Burger"},
    "OG SMASH": {"preis": 10.00, "icon": "👑", "kat": "Smash Burger"},
    "Classic Chicken Burger": {"preis": 10.00, "icon": "🍗", "kat": "Smash Burger"},
    "Spicy Chicken Burger": {"preis": 10.00, "icon": "💥", "kat": "Smash Burger"},
    "Green Dream Burger": {"preis": 10.00, "icon": "🌱", "kat": "Smash Burger"},
    "Vegan Leaf Burger": {"preis": 10.00, "icon": "🍃", "kat": "Smash Burger"},
    "Chicken Wrap": {"preis": 9.90, "icon": "🌯", "kat": "Wraps"},
    "Beef Wrap": {"preis": 9.90, "icon": "🥩", "kat": "Wraps"},
    "Green Wrap": {"preis": 9.90, "icon": "🥗", "kat": "Wraps"}
}
RESTAURANT_NAME = "Smash Brothers"

def rendering_menue_grid(session_key):
    kategorien = ["Smash Burger", "Wraps"]
    for kat in kategorien:
        st.markdown(f"#### ++ {kat} ++")
        items = [item for item in menue.items() if item[1]["kat"] == kat]
        for i in range(0, len(items), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(items):
                    artikel, info = items[i + j]
                    with cols[j]:
                        with st.container(border=True):
                            st.markdown(f"**{info['icon']} {artikel}**")
                            st.markdown(f"<code style='font-size: 14px; background-color: #f0f2f6; padding: 1px 5px; border-radius: 4px;'>{info['preis']:.2f} €</code>", unsafe_allow_html=True)
                            st.write("")
                            btn_col1, btn_col2 = st.columns([1, 1])
                            with btn_col1:
                                if st.button("➕", key=f"{session_key}_add_{artikel}", use_container_width=True):
                                    st.session_state[session_key][artikel] += 1
                                    st.rerun()
                            with btn_col2:
                                if st.session_state[session_key][artikel] > 0:
                                    if st.button("❌", key=f"{session_key}_rem_{artikel}", use_container_width=True):
                                        st.session_state[session_key][artikel] = 0
                                        st.rerun()
                            if st.session_state[session_key][artikel] > 0:
                                st.markdown(f"🛒 **{st.session_state[session_key][artikel]}x**")

# ====== 1. KUNDEN-ANSICHT ======
if rolle == "🏠 1. Kunden-Ansicht (Bestellung von zu Hause)":
    st.header("🛒 Online-Shop – Smash Brothers")
    col1, col2 = st.columns([2, 1])
    if "kunden_korb" not in st.session_state:
        st.session_state.kunden_korb = {artikel: 0 for artikel in menue}
        
    with col1:
        rendering_menue_grid("kunden_korb")

    with col2:
        st.subheader("📋 Meine Bestellung")
        artikel_im_korb = []
        gesamtsumme = 0.0
        for artikel, anzahl in st.session_state.kunden_korb.items():
            if anzahl > 0:
                preis_pro_posten = menue[artikel]["preis"] * anzahl
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
                    "dysko": f"{k_trinkgeld:.2f}",
                    "cas_pripravy": "10"
                }
                bestellung_speichern(neue_bestellung)
                st.session_state.kunden_korb = {artikel: 0 for artikel in menue}
                st.success("🎉 Abgesendet!")
                st.rerun()

# ====== 2. KASSA / EINGABE ======
elif rolle == "🏬 2. Kassa / Eingabe (Theke)":
    st.header(f"🏬 Kassa & Auftragsannahme – {RESTAURANT_NAME}")
    docs = bestellungen_laden()
    
    # Inicializace časovačů pro příjem zakázek, pokud neexistují
    if "zeit_online" not in st.session_state: st.session_state.zeit_online = {}
    if "zeit_manuell" not in st.session_state: st.session_state.zeit_manuell = 10

    st.subheader("🔔 Eingehende ONLINE-Bestellungen")
    online_gefunden = False
    
    for d in docs:
        f = d["fields"]
        status = f["stav"]["stringValue"]
        doc_name = d["name"]
        
        if status == "Wartet auf Bestätigung durch Kassa":
            online_gefunden = True
            if doc_name not in st.session_state.zeit_online:
                st.session_state.zeit_online[doc_name] = 10
                
            with st.container(border=True):
                col_o1, col_o2, col_o3 = st.columns([2, 1, 1])
                with col_o1:
                    st.markdown(f"**📦 {f['obsah']['stringValue']}** ({f['cena']['stringValue']} €)")
                    st.text(f"📍 {f['adresa']['stringValue']} | Zeit: {f['cas']['stringValue']}")
                
                with col_o2:
                    st.markdown(f"⏱️ **Zubereitungszeit:** `{st.session_state.zeit_online[doc_name]} Min`")
                    zc1, zc2 = st.columns(2)
                    if zc1.button("➕ 5 Min", key=f"p5_on_{doc_name}"):
                        st.session_state.zeit_online[doc_name] += 5
                        st.rerun()
                    if zc2.button("➖ 5 Min", key=f"m5_on_{doc_name}"):
                        if st.session_state.zeit_online[doc_name] > 5:
                            st.session_state.zeit_online[doc_name] -= 5
                            st.rerun()
                
                with col_o3:
                    if st.button("✔️ Bestätigen & Küche", key=f"prij_online_{doc_name}", type="primary", use_container_width=True):
                        bestellstatus_aktualisieren(doc_name, "In Zubereitung (Küche)", "Petr (Auto)", f["adresa"]["stringValue"], st.session_state.zeit_online[doc_name])
                        st.rerun()
                        
    if not online_gefunden:
        st.info("Keine neuen Online-Bestellungen.")
        
    st.write("---")
    st.subheader("✍️ Manuelle Bestelleingabe (Telefon / Tresen)")
    
    if "rest_korb" not in st.session_state:
        st.session_state.rest_korb = {artikel: 0 for artikel in menue}
        
    col_kassa_1, col_kassa_2 = st.columns([2, 1])
    with col_kassa_1:
        rendering_menue_grid("rest_korb")
                    
    with col_kassa_2:
        r_artikel = []
        r_summe = 0.0
        for artikel, anzahl in st.session_state.rest_korb.items():
            if anzahl > 0:
                r_artikel.append(f"{anzahl}x {artikel}")
                r_summe += menue[artikel]["preis"] * anzahl
                st.text(f"• {anzahl}x {artikel} = {(menue[artikel]['preis'] * anzahl):.2f} €")
                
        st.write("---")
        st.metric("Gesamtsumme", f"{r_summe:.2f} €")
        r_name = st.text_input("Kundenname", "Telefonischer Kunde", key="r_name")
        r_tel = st.text_input("Telefonnummer (Kunde)", "+43 ", key="r_tel")
        r_adresse = st.text_input("Lieferadresse", "Ennser Straße 5, Steyr", key="r_adr")
        r_zahlung = st.selectbox("Zahlungsart", ["Barzahlung", "Online-Karte"], key="r_zahl")
        
        # Ovládání času pro manuální objednávku
        st.markdown(f"⏱️ **Zubereitungszeit pro Küche:** `{st.session_state.zeit_manuell} Min`")
        mc1, mc2 = st.columns(2)
        if mc1.button("➕ 5 Min", key="p5_man"):
            st.session_state.zeit_manuell += 5
            st.rerun()
        if mc2.button("➖ 5 Min", key="m5_man"):
            if st.session_state.zeit_manuell > 5:
                st.session_state.zeit_manuell -= 5
                st.rerun()
                
        if st.button("📥 DIREKT IN DIE KÜCHE SENDEN", type="primary", use_container_width=True):
            if r_artikel == []:
                st.error("Warenkorb leer!")
            else:
                neue_bestellung = {
                    "obsah": ", ".join(r_artikel),
                    "cena": f"{r_summe:.2f}",
                    "platba": r_zahlung,
                    "adresa": f"{r_adresse} | Kunde: {r_name} | Tel: {r_tel}",
                    "stav": "In Zubereitung (Küche)",
                    "kuryr": "Petr (Auto)",
                    "cas": datetime.now().strftime("%H:%M:%S"),
                    "dysko": "0.00",
                    "cas_pripravy": str(st.session_state.zeit_manuell)
                }
                bestellung_speichern(neue_bestellung)
                st.session_state.rest_korb = {artikel: 0 for artikel in menue}
                st.session_state.zeit_manuell = 10
                st.success("Erfolgreich in die Küche gesendet!")
                st.rerun()

    st.write("---")
    if st.button("🗑️ Gesamte Cloud-Historie löschen"):
        alle_bestellungen_loeschen()
        st.rerun()

# ====== 3. KÜCHE MONITOR ======
elif rolle == "👨‍🍳 3. Küche Monitor":
    st.header("👨‍🍳 Küche Monitor (Zubereitung)")
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
                    st.text(f"⏱️ Angenommen um: {f['cas']['stringValue']} | Kassa: {f['platba']['stringValue']}")
                    st.text(f"📍 Infos: {f['adresa']['stringValue']}")
                with col_k2:
                    if st.button(f"✅ FERTIG / VERPACKT", key=f"hotovo_kuch_{doc_name}", type="primary", use_container_width=True):
                        # Při kliknutí na FERTIG uchováme dynamický čas i adresu pro kurýra
                        c_prip = f.get("cas_pripravy", {}).get("stringValue", "10")
                        bestellstatus_aktualisieren(doc_name, "Ready for Pick-up", "Petr (Auto)", f["adresa"]["stringValue"], c_prip)
                        st.success("Als FERTIG markiert!")
                        time.sleep(0.5)
                        st.rerun()
            st.write("")
            
    if not offene_kueche:
        st.info("Aktuell keine Bestellungen in der Küche. Gute Arbeit! ✨")

# ====== 4. FAHRER-ANSICHT ======
elif rolle == "🚗 4. Fahrer-Ansicht (Mobil & Finanzen)":
    st.header("Kurier-App (Unterwegs)")
    fahrer_name = "Petr (Auto)"
    
    if "bargeld_eur" not in st.session_state:
        st.session_state.bargeld_eur = 0.0
        st.session_state.provision_eur = 0.0
        st.session_state.trinkgeld_eur = 0.0

    st.subheader("📊 Meine Finanzübersicht")
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Meine Provision (Fix 4€/Fahrt)", f"{st.session_state.provision_eur:.2f} €")
    with c2: st.metric("Erhaltenes Trinkgeld (Dýško)", f"{st.session_state.trinkgeld_eur:.2f} €")
    with c3: st.metric("Eingenommenes Bargeld (Limit 200€)", f"{st.session_state.bargeld_eur:.2f} / 200.00 €")
    st.write("---")
    
    if st.session_state.bargeld_eur >= 200.0:
        st.error("🛑 BARGELDLIMIT ERREICHT! Du hast mehr als 200€ in bar. Es werden KEINE weiteren Bestellungen empfangen!")
        st.warning("⚠️ Fahre bitte sofort zur Hauptstation (Volt and value), um das Geld abzurechnen.")
        if st.button("💰 Geld in der Hauptstation (Volt and value) abgegeben (Reset Cash)", type="primary", use_container_width=True):
            st.session_state.bargeld_eur = 0.0
            st.success("Geld erfolgreich abgerechnet!")
            time.sleep(1)
            st.rerun()
    else:
        st.subheader("Aktuelle Aufträge in der Pipeline")
        docs = bestellungen_laden()
        aktive_auftraege = [d for d in docs if d["fields"]["kuryr"]["stringValue"] == fahrer_name 
                            and d["fields"]["stav"]["stringValue"] in ["In Zubereitung (Küche)", "Ready for Pick-up", "Auf dem Weg zum Kunden"]]
        
        if not aktive_auftraege:
            st.info("Kein aktiver Auftrag. Warte auf die Kassa...")
        else:
            for d in aktive_auftraege:
                f = d["fields"]
                status = f["stav"]["stringValue"]
                doc_name = d["name"]
                dysko_val = f.get("dysko", {}).get("stringValue", "0.00")
                minuten_pripravy = f.get("cas_pripravy", {}).get("stringValue", "10")
                
                if status == "Ready for Pick-up":
                    border_color = "#28a745"
                    header_text = "🚨 DER KOCH WAR SCHNELLER! DAS ESSEN IST FERTIG!"
                elif status == "Auf dem Weg zum Kunden":
                    border_color = "#007bff"
                    header_text = "🚚 AUF DEM WEG ZUM KUNDEN (ADRESSE OFFEN)"
                else:
                    border_color = "#ffc107"
                    header_text = "⏳ IN ZUBEREITUNG (KÜCHE KOCHT NOCH)"

                with st.container(border=True):
                    st.markdown(f"<h3 style='color:{border_color}; margin-top:0;'>{header_text}</h3>", unsafe_allow_html=True)
                    st.markdown(f"**📍 Abholen bei:** {RESTAURANT_NAME}")
                    st.write(f"🍱 **Inhalt:** {f['obsah']['stringValue']}")
                    st.write(f"💶 **Zu kassieren:** {f['cena']['stringValue']} € ({f['platba']['stringValue']})")
                    st.write(f"💰 **Trinkgeld:** {dysko_val} €")
                    
                    if status == "In Zubereitung (Küche)":
                        st.markdown(f"<div style='padding:10px; background-color:#FFF3CD; border-radius:5px;'><b>⏱️ Eingestellte Zubereitungszeit: cca. {minuten_pripravy} Minuten.</b> Du kannst entsprechend hinfahren.</div>", unsafe_allow_html=True)
                        if st.button("🔄 Aktualisieren", key=f"refresh_{doc_name}"): st.rerun()
                    elif status == "Ready for Pick-up":
                        st.markdown("<b style='color:#28a745;'>Das Essen wartet verpackt an der Theke!</b>", unsafe_allow_html=True)
                        if st.button("👍 Abholung an der Theke bestätigen", key=f"pick_{doc_name}", type="primary", use_container_width=True):
                            bestellstatus_aktualisieren(doc_name, "Auf dem Weg zum Kunden", fahrer_name, f["adresa"]["stringValue"], minuten_pripravy)
                            st.rerun()
                    elif status == "Auf dem Weg zum Kunden":
                        st.success("🔓 LIEFERADRESSE FREIGESCHALTET:")
                        st.markdown(f"➡️ **Wohin du fährst:** `{f['adresa']['stringValue']}`")
                        if st.button("✅ Geliefert & Kassiert (Auftrag abschließen)", key=f"deliver_{doc_name}", type="primary", use_container_width=True):
                            st.session_state.provision_eur += 4.00
                            st.session_state.trinkgeld_eur += float(dysko_val)
                            if f["platba"]["stringValue"] == "Barzahlung":
                                st.session_state.bargeld_eur += float(f["cena"]["stringValue"])
                            bestellstatus_aktualisieren(doc_name, "Geliefert", fahrer_name, f["adresa"]["stringValue"], minuten_pripravy)
                            st.success("Erfolgreich abgeschlossen!")
                            time.sleep(0.5)
                            st.rerun()
