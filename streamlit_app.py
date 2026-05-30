import streamlit as st
import requests
import json
import time
from datetime import datetime

# ====== FIREBASE SETTINGS ======
PROJECT_ID = "volt-a-value" 
FIRESTORE_URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents"

st.set_page_config(page_title="Lieferdienst Management System", layout="wide")

# ====== DATABASE FUNCTIONS ======
def naechste_bestellnummer_holen():
    url = f"{FIRESTORE_URL}/objednavky"
    res = requests.get(url)
    max_nr = 0
    if res.status_code == 200 and "documents" in res.json():
        for d in res.json()["documents"]:
            f = d.get("fields", {})
            if "cislo_objednavky" in f:
                try:
                    nr = int(f["cislo_objednavky"]["stringValue"])
                    if nr > max_nr:
                        max_nr = nr
                except:
                    pass
    naechste = max_nr + 1
    if naechste > 9999:
        naechste = 1
    return naechste

def bestellung_speichern(daten):
    url = f"{FIRESTORE_URL}/objednavky"
    daten["cislo_objednavky"] = str(naechste_bestellnummer_holen())
    payload = {"fields": {k: {"stringValue": str(v)} for k, v in daten.items()}}
    requests.post(url, json=payload)

def bestellungen_laden():
    url = f"{FIRESTORE_URL}/objednavky"
    res = requests.get(url)
    if res.status_code == 200 and "documents" in res.json():
        return res.json()["documents"]
    return []

def bestellstatus_aktualisieren(doc_name, neuer_status, fahrer_name="", lieferdetails="", zubereitungszeit="10"):
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
rolle = st.sidebar.radio("Bereich auswählen:", [
    "🏠 1. Kunden-Ansicht (Bestellung von zu Hause)", 
    "🏬 2. Kassa / Eingabe (Theke)",
    "👨‍🍳 3. Küche Monitor", 
    "🚗 4. Fahrer-Ansicht (Mobil & Finanzen)"
])

# ====== REÁLNÉ GASTRO FOTKY PRO KACHLÍKY (Přímé URL odkazy) ======
url_burger = "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=500&auto=format&fit=crop&q=60"
url_chicken = "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=500&auto=format&fit=crop&q=60"
url_wrap = "https://images.unsplash.com/photo-1626700051175-6518c4793f4f?w=500&auto=format&fit=crop&q=60"
url_kebab = "https://images.unsplash.com/photo-1628258475456-0224b1e4225a?w=500&auto=format&fit=crop&q=60"
url_pizza = "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=500&auto=format&fit=crop&q=60"
url_schnitzel = "https://images.unsplash.com/photo-1599921841143-819065a55cc6?w=500&auto=format&fit=crop&q=60"

# ====== MULTI-RESTAURANT MENUE STRUCTURE ======
restaurants_menue = {
    "Smash Brothers": {
        "Cheese Burger": {"preis": 9.00, "icon": "🍔", "kat": "Smash Burger", "extras": True, "bild": url_burger},
        "Chili Cheese Burger": {"preis": 10.00, "icon": "🌶️", "kat": "Smash Burger", "extras": True, "bild": url_burger},
        "Double Trouble Burger": {"preis": 12.90, "icon": "🔥", "kat": "Smash Burger", "extras": True, "bild": url_burger},
        "Oklahoma Double Burger": {"preis": 12.90, "icon": "🧅", "kat": "Smash Burger", "extras": True, "bild": url_burger},
        "Double Beast Burger": {"preis": 12.90, "icon": "👹", "kat": "Smash Burger", "extras": True, "bild": url_burger},
        "Smash 'n' Egg": {"preis": 12.50, "icon": "🍳", "kat": "Smash Burger", "extras": True, "bild": url_burger},
        "OG SMASH": {"preis": 10.00, "icon": "👑", "kat": "Smash Burger", "extras": True, "bild": url_burger},
        "Classic Chicken Burger": {"preis": 10.00, "icon": "🍗", "kat": "Smash Burger", "extras": True, "bild": url_chicken},
        "Spicy Chicken Burger": {"preis": 10.00, "icon": "💥", "kat": "Smash Burger", "extras": True, "bild": url_chicken},
        "Green Dream Burger": {"preis": 10.00, "icon": "🌱", "kat": "Smash Burger", "extras": True, "bild": url_burger},
        "Vegan Leaf Burger": {"preis": 10.00, "icon": "🍃", "kat": "Smash Burger", "extras": True, "bild": url_burger},
        "Chicken Wrap": {"preis": 9.90, "icon": "🌯", "kat": "Wraps", "extras": False, "bild": url_wrap},
        "Beef Wrap": {"preis": 9.90, "icon": "🥩", "kat": "Wraps", "extras": False, "bild": url_wrap},
        "Green Wrap": {"preis": 9.90, "icon": "🥗", "kat": "Wraps", "extras": False, "bild": url_wrap}
    },
    "King Food": {
        "Kebab Oriental": {"preis": 6.50, "icon": "🥙", "kat": "Kebab", "extras": False, "bild": url_kebab},
        "Kebab Spezial": {"preis": 7.20, "icon": "🌯", "kat": "Kebab", "extras": False, "bild": url_wrap},
        "Pizza Margherita": {"preis": 8.50, "icon": "🍕", "kat": "Pizza", "extras": False, "bild": url_pizza},
        "Pizza Salami": {"preis": 9.50, "icon": "🍕", "kat": "Pizza", "extras": False, "bild": url_pizza},
        "Pizza Cardinale": {"preis": 9.90, "icon": "🍕", "kat": "Pizza", "extras": False, "bild": url_pizza},
        "Pizza Tonno": {"preis": 10.20, "icon": "🍕", "kat": "Pizza", "extras": False, "bild": url_pizza},
        "Pizza Quattro Formaggi": {"preis": 10.90, "icon": "🍕", "kat": "Pizza", "extras": False, "bild": url_pizza},
        "Wiener Schnitzel (vom Schwein)": {"preis": 11.50, "icon": "🥩", "kat": "Schnitzel", "extras": False, "bild": url_schnitzel}
    }
}

extra_options = {
    "Extra Fleisch (+3.00 €)": 3.00,
    "Extra Gurken (+0.50 €)": 0.50,
    "Ketchup (+0.50 €)": 0.50,
    "Mayo (+0.50 €)": 0.50
}

def rendering_menue_grid(aktive_rest, session_key):
    aktuelle_speisekarte = restaurants_menue[aktive_rest]
    kategorien = list(set(info["kat"] for info in aktuelle_speisekarte.values()))
    
    for kat in sorted(kategorien):
        st.markdown(f"#### ++ {kat} ++")
        items = [item for item in aktuelle_speisekarte.items() if item[1]["kat"] == kat]
        for i in range(0, len(items), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(items):
                    artikel, info = items[i + j]
                    with cols[j]:
                        with st.container(border=True):
                            # Vykreslení fotky jídla navrchu kachlíku (pokud v menu existuje odkaz)
                            if "bild" in info:
                                st.image(info["bild"], use_container_width=True)
                                
                            st.markdown(f"**{info['icon']} {artikel}**")
                            st.markdown(f"Price: {info['preis']:.2f} €")
                            
                            selected_extras = []
                            extra_cost = 0.0
                            if info.get("extras", False):
                                with st.expander("✨ Zutaten / Extras"):
                                    for ex_name, ex_preis in extra_options.items():
                                        if st.checkbox(ex_name, key=f"{session_key}_{aktive_rest}_{artikel}_{ex_name}"):
                                            selected_extras.append(ex_name.split(" (")[0])
                                            extra_cost += ex_preis
                            
                            st.write("")
                            if st.button("➕ Hinzufügen", key=f"{session_key}_{aktive_rest}_btn_{artikel}", use_container_width=True):
                                název_polozky = artikel
                                if selected_extras:
                                    název_polozky += f" ({', '.join(selected_extras)})"
                                
                                final_preis = info["preis"] + extra_cost
                                st.session_state[f"{session_key}_liste"].append({"name": název_polozky, "preis": final_preis})
                                st.success("Hinzugefügt!")
                                time.sleep(0.2)
                                st.rerun()

if "kunden_korb_liste" not in st.session_state: st.session_state.kunden_korb_liste = []
if "rest_korb_liste" not in st.session_state: st.session_state.rest_korb_liste = []
if "gewaehltes_rest_kunde" not in st.session_state: st.session_state.gewaehltes_rest_kunde = None
if "gewaehltes_rest_kassa" not in st.session_state: st.session_state.gewaehltes_rest_kassa = "Smash Brothers"

# ====== 1. KUNDEN-ANSICHT ======
if rolle == "🏠 1. Kunden-Ansicht (Bestellung von zu Hause)":
    st.header("🚚 Online-Bestellung – Restaurant wählen")
    
    c_rest1, c_rest2 = st.columns(2)
    with c_rest1:
        if st.button("🍔 SMASH BROTHERS", use_container_width=True, type="primary" if st.session_state.gewaehltes_rest_kunde == "Smash Brothers" else "secondary"):
            st.session_state.gewaehltes_rest_kunde = "Smash Brothers"
            st.rerun()
    with c_rest2:
        if st.button("🥙 KING FOOD (Kebab & Pizza)", use_container_width=True, type="primary" if st.session_state.gewaehltes_rest_kunde == "King Food" else "secondary"):
            st.session_state.gewaehltes_rest_kunde = "King Food"
            st.rerun()
            
    st.write("---")
    
    if st.session_state.gewaehltes_rest_kunde is None:
        st.info("Bitte wählen Sie oben ein Restaurant aus, um die Speisekarte anzuzeigen.")
    else:
        st.subheader(f"Speisekarte von: {st.session_state.gewaehltes_rest_kunde}")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            rendering_menue_grid(st.session_state.gewaehltes_rest_kunde, "kunden_korb")

        with col2:
            st.subheader("📋 Meine Bestellung")
            gesamtsumme = 0.0
            artikel_strings = []
            
            if not st.session_state.kunden_korb_liste:
                st.info("Dein Warenkorb ist leer.")
            else:
                for idx, item in enumerate(st.session_state.kunden_korb_liste):
                    st.text(f"• {item['name']} = {item['preis']:.2f} €")
                    gesamtsumme += item["preis"]
                    artikel_strings.append(item["name"])
                    
                if st.button("🧹 Korb leeren", key="clear_kunden"):
                    st.session_state.kunden_korb_liste = []
                    st.rerun()
                    
            st.write("---")
            st.metric("Gesamtsumme", f"{gesamtsumme:.2f} €")
            k_trinkgeld = st.number_input("Trinkgeld für den Fahrer (€)", min_value=0.0, max_value=20.0, value=0.0, step=0.5, key="k_trinkgeld")
            k_name = st.text_input("Name", "Max Mustermann", key="k_name")
            k_telefon = st.text_input("Telefonnummer", "+43 660 1234567", key="k_tel")
            k_adresse = st.text_input("Lieferadresse", "Hauptstraße 12, Steyr", key="k_adr")
            k_zahlung = st.selectbox("Zahlungsart", ["Online-Karte", "Barzahlung"], key="k_zahl")
            
            if st.session_state.kunden_korb_liste:
                if st.button("🚀 BESTELLUNG ABSENDEN", type="primary", use_container_width=True):
                    neue_bestellung = {
                        "restaurant": st.session_state.gewaehltes_rest_kunde,
                        "obsah": ", ".join(artikel_strings),
                        "cena": f"{gesamtsumme:.2f}",
                        "platba": k_zahlung,
                        "adresa": f"{k_adresse} | Kunde: {k_name} | Tel: {k_telefon}",
                        "stav": "Wartet auf Bestätigung durch Kassa",
                        "kuryr": "Petr (Auto)",
                        "cas": datetime.now().strftime("%H:%M:%S"),
                        "dysko": f"{k_trinkgeld:.2f}",
                        "cas_pripravy": "10"
                    }
                    bestellung_speichern(neue_bestellung)
                    st.session_state.kunden_korb_liste = []
                    st.success("🎉 Abgesendet!")
                    st.rerun()

# ====== 2. KASSA / EINGABE ======
elif rolle == "🏬 2. Kassa / Eingabe (Theke)":
    st.header("🏬 Kassa & Auftragsannahme")
    docs = bestellungen_laden()
    
    if "zeit_online" not in st.session_state: st.session_state.zeit_online = {}
    if "zeit_manuell" not in st.session_state: st.session_state.zeit_manuell = 10

    st.subheader("🔔 Eingehende ONLINE-Bestellungen")
    online_gefunden = False
    for d in docs:
        f = d["fields"]
        status = f["stav"]["stringValue"]
        doc_name = d["name"]
        nr_obj = f.get("cislo_objednavky", {}).get("stringValue", "0")
        r_von = f.get("restaurant", {}).get("stringValue", "Smash Brothers")
        
        if status == "Wartet auf Bestätigung durch Kassa":
            online_gefunden = True
            if doc_name not in st.session_state.zeit_online: st.session_state.zeit_online[doc_name] = 10
                
            with st.container(border=True):
                col_o1, col_o2, col_o3 = st.columns([2, 1, 1])
                with col_o1:
                    st.markdown(f"### 📦 ORDER #{int(nr_obj):04d} ({r_von})")
                    st.markdown(f"**Inhalt:** {f['obsah']['stringValue']} ({f['cena']['stringValue']} €)")
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
                        
    if not online_gefunden: st.info("Keine neuen Online-Bestellungen.")
        
    st.write("---")
    st.subheader("✍️ Manuelle Bestelleingabe (Telefon / Tresen)")
    st.session_state.gewaehltes_rest_kassa = st.selectbox("Restaurant für die Eingabe:", ["Smash Brothers", "King Food"])
    
    col_kassa_1, col_kassa_2 = st.columns([2, 1])
    with col_kassa_1:
        rendering_menue_grid(st.session_state.gewaehltes_rest_kassa, "rest_korb")
                    
    with col_kassa_2:
        r_summe = 0.0
        r_artikel_strings = []
        if not st.session_state.rest_korb_liste:
            st.info("Kassa-Beleg leer.")
        else:
            for item in st.session_state.rest_korb_liste:
                st.text(f"• {item['name']} = {item['preis']:.2f} €")
                r_summe += item["preis"]
                r_artikel_strings.append(item["name"])
                
            if st.button("🧹 Beleg leeren", key="clear_rest"):
                st.session_state.rest_korb_liste = []
                st.rerun()
                
        st.write("---")
        st.metric("Gesamtsumme", f"{r_summe:.2f} €")
        r_name = st.text_input("Kundenname", "Telefonischer Kunde", key="r_name")
        r_tel = st.text_input("Telefonnummer (Kunde)", "+43 ", key="r_tel")
        r_adresse = st.text_input("Lieferadresse", "Ennser Straße 5, Steyr", key="r_adr")
        r_zahlung = st.selectbox("Zahlungsart", ["Barzahlung", "Online-Karte"], key="r_zahl")
        
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
            if not r_artikel_strings:
                st.error("Warenkorb leer!")
            else:
                neue_bestellung = {
                    "restaurant": st.session_state.gewaehltes_rest_kassa,
                    "obsah": ", ".join(r_artikel_strings),
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
                st.session_state.rest_korb_liste = []
                st.session_state.zeit_manuell = 10
                st.success("Erfolgreich in die Küche gesendet!")
                st.rerun()

    st.write("---")
    if st.button("🗑️ Gesamte Cloud-Historie löschen"): 
        alle_bestellungen_loeschen()
        st.rerun()

# ====== 3. KÜCHE MONITOR ======
elif rolle == "👨‍🍳 3. Küche Monitor":
    st.header("👨‍🍳 Monitor v kuchyni (Küche Monitor)")
    docs = bestellungen_laden()
    offene_kueche = False
    
    cols_kueche = st.columns(3)
    k_idx = 0
    
    for d in docs:
        f = d["fields"]
        status = f["stav"]["stringValue"]
        doc_name = d["name"]
        
        nr_obj = f.get("cislo_objednavky", {}).get("stringValue", "0")
        r_von = f.get("restaurant", {}).get("stringValue", "Smash Brothers")
        try:
            label_bon = f"BON #{int(nr_obj):04d}"
        except:
            label_bon = f"BON #{nr_obj}"
        
        if status == "In Zubereitung (Küche)":
            offene_kueche = True
            with cols_kueche[k_idx % 3]:
                with st.container(border=True):
                    st.markdown(
                        f'<div style="background-color: #ffffff; border: 2px solid #333333; padding: 15px; border-radius: 4px; font-family: monospace; color: #000000 !important;">'
                        f'<h3 style="text-align: center; color: #e91e63 !important; margin: 0;">{label_bon}</h3>'
                        f'<p style="text-align: center; color: #333333 !important; font-weight: bold; margin: 2px 0;">{r_von}</p>'
                        f'<p style="text-align: center; color: #555555 !important; margin: 5px 0;">Zeit: {f["cas"]["stringValue"]}</p>'
                        f'<hr style="border-top: 1px dashed #333333;">',
                        unsafe_allow_html=True
                    )
                    
                    items_list = f['obsah']['stringValue'].split(", ")
                    for item in items_list:
                        st.markdown(f"<p style='color: #000000 !important; font-size: 16px; font-weight: bold; margin: 4px 0;'>• {item}</p>", unsafe_allow_html=True)
                    
                    st.markdown(
                        f'<hr style="border-top: 1px dashed #333333;">'
                        f'<p style="color: #000000 !important; margin: 0;"><b>Kassa:</b> {f["platba"]["stringValue"]}</p>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                    st.write("")
                    
                    if st.button(f"✅ READY / HOTOVO ({label_bon})", key=f"hotovo_kuch_{doc_name}", type="primary", use_container_width=True):
                        c_prip = f.get("cas_pripravy", {}).get("stringValue", "10")
                        bestellstatus_aktualisieren(doc_name, "Ready for Pick-up", "Petr (Auto)", f["adresa"]["stringValue"], c_prip)
                        st.success(f"{label_bon} FERTIG!")
                        time.sleep(0.3)
                        st.rerun()
            k_idx += 1
            
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
    with c1: st.metric("Meine Provision", f"{st.session_state.provision_eur:.2f} €")
    with c2: st.metric("Erhaltenes Trinkgeld", f"{st.session_state.trinkgeld_eur:.2f} €")
    with c3: st.metric("Bargeld (Limit 200€)", f"{st.session_state.bargeld_eur:.2f} / 200.00 €")
    st.write("---")
    
    if st.session_state.bargeld_eur >= 200.0:
        st.error("🛑 BARGELDLIMIT ERREICHT! Du hast mehr als 200€ in bar.")
        st.warning("⚠️ Fahre bitte sofort zur Hauptstation (Volt and value), um das Geld abzurechnen.")
        if st.button("💰 Geld in der Hauptstation (Volt and value) odevzdáno", type="primary", use_container_width=True):
            st.session_state.bargeld_eur = 0.0
            st.success("Geld erfolgreich abgerechnet!")
            time.sleep(1)
            st.rerun()
    else:
        st.subheader("Aktuelle Aufträge in der Pipeline")
        docs = bestellungen_laden()
        aktive_auftraege = []
        for d in docs:
            try:
                if d["fields"]["kuryr"]["stringValue"] == fahrer_name and d["fields"]["stav"]["stringValue"] in ["In Zubereitung (Küche)", "Ready for Pick-up", "Auf dem Weg zum Kunden"]:
                    aktive_auftraege.append(d)
            except:
                pass
        
        if not aktive_auftraege:
            st.info("Kein aktiver Auftrag. Warte auf die Kassa...")
        else:
            for d in aktive_auftraege:
                f = d["fields"]
                status = f["stav"]["stringValue"]
                doc_name = d["name"]
                dysko_val = f.get("dysko", {}).get("stringValue", "0.00")
                minuten_pripravy = f.get("cas_pripravy", {}).get("stringValue", "10")
                nr_obj = f.get("cislo_objednavky", {}).get("stringValue", "0")
                r_von = f.get("restaurant", {}).get("stringValue", "Smash Brothers")
                
                try:
                    txt_nr = f"BON #{int(nr_obj):04d}"
                except:
                    txt_nr = f"BON #{nr_obj}"
                
                if status == "Ready for Pick-up":
                    st.success(f"🚨 DER KOCH WAR SCHNELLER! {txt_nr} ({r_von}) IST FERTIG!")
                elif status == "Auf dem Weg zum Kunden":
                    st.info(f"🚚 AUF DEM WEG ZUM KUNDEN ({txt_nr})")
                else:
                    st.warning(f"⏳ IN ZUBEREITUNG ({txt_nr} - {r_von})")

                with st.container(border=True):
                    st.markdown(f"**📍 Abholen bei:** `{r_von}`")
                    st.write(f"🍱 **Inhalt:** {f['obsah']['stringValue']}")
                    st.write(f"💶 **Zu kassieren:** {f['cena']['stringValue']} € ({f['platba']['stringValue']})")
                    st.write(f"💰 **Trinkgeld:** {dysko_val} €")
                    
                    if status == "In Zubereitung (Küche)":
                        st.write(f"⏱️ Ready in cca. {minuten_pripravy} Minuten.")
                        if st.button("🔄 Aktualisieren", key=f"refresh_{doc_name}"): st.rerun()
                    elif status == "Ready for Pick-up":
                        st.write("Das Essen wartet verpackt an der Theke!")
                        if st.button("👍 Abholung an der Theke bestätigen", key=f"pick_{doc_name}", type="primary", use_container_width=True):
                            bestellstatus_aktualisieren(doc_name, "Auf dem Weg zum Kunden", fahrer_name, f["adresa"]["stringValue"], minuten_pripravy)
                            st.rerun()
                    elif status == "Auf dem Weg zum Kunden":
                        st.write(f"➡️ **Wohin du fährst:** {f['adresa']['stringValue']}")
                        if st.button("✅ Geliefert & Kassiert", key=f"deliver_{doc_name}", type="primary", use_container_width=True):
                            st.session_state.provision_eur += 4.00
                            st.session_state.trinkgeld_eur += float(dysko_val)
                            if f["platba"]["stringValue"] == "Barzahlung":
                                st.session_state.bargeld_eur += float(f["cena"]["stringValue"])
                            bestellstatus_aktualisieren(doc_name, "Geliefert", fahrer_name, f["adresa"]["stringValue"], minuten_pripravy)
                            st.success("Erfolgreich abgeschlossen!")
                            time.sleep(0.5)
                            st.rerun()
