import streamlit as st
import requests
import json
import time
from datetime import datetime

PROJECT_ID = "volt-a-value" 
FIRESTORE_URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents"

st.set_page_config(page_title="Kuryr & Restaurace MVP", layout="wide")

def uložit_objednávku(data):
    url = f"{FIRESTORE_URL}/objednavky"
    payload = {"fields": {k: {"stringValue": str(v)} for k, v in data.items()}}
    requests.post(url, json=payload)

def získej_objednávky():
    url = f"{FIRESTORE_URL}/objednavky"
    res = requests.get(url)
    if res.status_code == 200 and "documents" in res.json():
        return res.json()["documents"]
    return []

def aktualizovat_stav_objednavky(doc_name, novy_stav, kuryr_jmeno=""):
    url = f"https://firestore.googleapis.com/v1/{doc_name}?updateMask.fieldPaths=stav&updateMask.fieldPaths=kuryr"
    payload = {"fields": {"stav": {"stringValue": novy_stav}, "kuryr": {"stringValue": kuryr_jmeno}}}
    requests.patch(url, json=payload)

def smazat_vsechny_objednavky():
    docs = získej_objednávky()
    for d in docs:
        requests.delete(f"https://firestore.googleapis.com/v1/{d['name']}")

st.title("🚚 Kurýrní Systém s Jídelním Lístkem")
role = st.sidebar.radio("Zvol si rozhraní:", ["🏬 Rozhraní pro Restauraci", "🚗 Rozhraní pro Řidiče (Mobil)"])

if role == "🏬 Rozhraní pro Restauraci":
    st.header("Administrace Restaurace – Nová objednávka")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🍔 Jídelní lístek")
        menu = {"Oklahoma Burger": 10.90, "Pommes": 4.00, "Curly Fries": 4.00, "Pepsi": 3.00, "Fanta Dose": 3.00}
        if "kosik" not in st.session_state:
            st.session_state.kosik = {item: 0 for item in menu}
            
        for jidlo, cena in menu.items():
            cc1, cc2, cc3 = st.columns([2, 1, 1])
            with cc1:
                st.write(f"**{jidlo}** ({cena:.2f} €)")
            with cc2:
                if st.button(f"➕ Pridat", key=f"add_{jidlo}"):
                    st.session_state.kosik[jidlo] += 1
            with cc3:
                if st.session_state.kosik[jidlo] > 0:
                    st.write(f"v košíku: **{st.session_state.kosik[jidlo]}x**")
                    if st.button(f"❌", key=f"remove_{jidlo}"):
                        st.session_state.kosik[jidlo] = 0

    with col2:
        st.subheader("🛒 Shrnutí a odeslání kurýrovi")
        polozky_v_kosiku = []
        celkova_cena = 0.0
        for jidlo, pocet in st.session_state.kosik.items():
            if pocet > 0:
                cena_za_polozku = menu[jidlo] * pocet
                polozky_v_kosiku.append(f"{pocet}x {jidlo}")
                celkova_cena += cena_za_polozku
                st.text(f"• {pocet}x {jidlo} = {cena_za_generovana:.2f} €")
                
        st.write("---")
        st.metric("Celková cena k úhradě", f"{celkova_cena:.2f} €")
        adresa = st.text_input("Adresa doručení", "Hlavní ulice 12, Město")
        platba = st.selectbox("Typ platby zákazníka", ["Karta online", "Hotovost"])
        
        if polozky_v_kosiku == []:
            st.info("Košík je prázdný. Kliknutím na jídla vlevo sestav objednávku.")
        else:
            if st.button("🚀 ODESLAT NEJBLIŽŠÍMU KURÝROVI", type="primary", use_container_width=True):
                nejblizsi_kuryr = "Petr (Auto)"
                nova_obj = {
                    "obsah": ", ".join(polozky_v_kosiku),
                    "cena": f"{celkova_cena:.2f}",
                    "platba": platba,
                    "adresa": adresa,
                    "stav": "Čeká na potvrzení",
                    "kuryr": nejblizsi_kuryr,
                    "cas": datetime.now().strftime("%H:%M:%S")
                }
                uložit_objednávku(nova_obj)
                st.session_state.kosik = {item: 0 for item in menu}
                st.success(f"Odesláno! Kurýrovi {nejblizsi_kuryr} právě pípla objednávka.")
                st.rerun()
                
        st.write("---")
        if st.button("🗑️ Vyčistit historii objednávek v cloudu"):
            smazat_vsechny_objednavky()
            st.rerun()

elif role == "🚗 Rozhraní pro Řidiče (Mobil)":
    st.header("Aplikace pro kurýra v terénu")
    jmeno_kuryra = "Petr (Auto)"
    st.info(f"Přihlášen jako kurýr: **{jmeno_kuryra}**")
    
    if "hotovost_eur" not in st.session_state:
        st.session_state.hotovost_eur = 0.0
        st.session_state.odmena_eur = 0.0

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Moje dnešní odměna (fix)", f"{st.session_state.odmena_eur:.2f} €")
    with c2:
        st.metric("Vybraná hotovost (Limit 200€)", f"{st.session_state.hotovost_eur:.2f} / 200.00 €")
    
    if st.session_state.hotovost_eur >= 200:
        st.error("🛑 Dosáhl jsi limitu hotovosti! Musíš jet odevzdat peníze do restaurace.")

    st.write("---")
    st.subheader("Aktuální přidělená zakázka z restaurace")
    
    docs = získej_objednávky()
    moje_zakazka_nalezena = False
    
    for d in docs:
        f = d["fields"]
        if f["kuryr"]["stringValue"] == jmeno_kuryra and f["stav"]["stringValue"] != "Doručeno":
            moje_zakazka_nalezena = True
            doc_name = d["name"]
            
            st.warning(f"🔔 NOVÁ OBJEDNÁVKA PŘIDĚLENA SYSTÉMEM (Čas: {f['cas']['stringValue']})")
            st.write(f"🍱 **Co vezeš:** {f['obsah']['stringValue']}")
            st.write(f"📍 **Kam to vezeš:** {f['adresa']['stringValue']}")
            st.write(f"💶 **Částka k inkasování:** {f['cena']['stringValue']} € ({f['platba']['stringValue']})")
            st.write(f"Aktuální stav: `{f['stav']['stringValue']}`")
            
            if f["stav"]["stringValue"] == "Čeká na potvrzení":
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("👍 Přijmout a jet do restaurace", use_container_width=True):
                        aktualizovat_stav_objednavky(doc_name, "Vyzvednuto / Na cestě k zákazníkovi", jmeno_kuryra)
                        st.rerun()
                with col_b:
                    if st.button("👎 Odmítnout", use_container_width=True):
                        aktualizovat_stav_objednavky(doc_name, "Čeká na potvrzení", "Záložní kurýr (Honza)")
                        st.rerun()
                        
            elif f["stav"]["stringValue"] == "Vyzvednuto / Na cestě k zákazníkovi":
                if st.button("✅ Doručeno zákazníkovi (Uzavřít)", type="primary", use_container_width=True):
                    aktualizovat_stav_objednavky(doc_name, "Doručeno", jmeno_kuryra)
                    st.session_state.odmena_eur += 4.00
                    if f["platba"]["stringValue"] == "Hotovost":
                        st.session_state.hotovost_eur += float(f["cena"]["stringValue"])
                    st.success("Hotovo! Peníze byly přičteny do tvého přehledu.")
                    st.rerun()
            break
            
    if not moje_zakazka_nalezena:
        st.info("Žádná nová zakázka. Čekej, až restaurace klikne na odeslání objednávky...")
