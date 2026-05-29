# ====== 4. FAHRER-ANSICHT (OPTIMALIZOVÁNO PRO PENDL) ======
elif rolle == "🚗 4. Fahrer-Ansicht (Mobil)":
    st.header("🛵 Kurier-Einsatz")
    
    docs = bestellungen_laden()
    aktive_auftraege = [d for d in docs if d["fields"]["kuryr"]["stringValue"] == "Petr (Auto)" 
                        and d["fields"]["stav"]["stringValue"] in ["In Zubereitung (Küche)", "Ready for Pick-up", "Auf dem Weg zum Kunden"]]
    
    if not aktive_auftraege:
        st.info("Žádné aktivní objednávky. Relaxuj! ☕")
    else:
        for d in aktive_auftraege:
            f = d["fields"]
            status = f["stav"]["stringValue"]
            doc_name = d["name"]
            
            # Barevné rozlišení podle stavu pro rychlou orientaci
            if status == "Ready for Pick-up":
                border_color = "#28a745" # Zelená (Hotovo, běž pro to)
                header_text = "✅ HOTOVO - BĚŽ NA BAR"
            elif status == "Auf dem Weg zum Kunden":
                border_color = "#007bff" # Modrá (Jedeš k zákazníkovi)
                header_text = "🚚 NA CESTĚ"
            else:
                border_color = "#ffc107" # Žlutá (Vaří se)
                header_text = "⏳ VAŘÍ SE"

            with st.container(border=True):
                st.markdown(f"<h4 style='color:{border_color};'>{header_text}</h4>", unsafe_allow_html=True)
                st.write(f"**Obsah:** {f['obsah']['stringValue']}")
                st.write(f"**Adresa:** {f['adresa']['stringValue']}")
                
                if status == "Ready for Pick-up":
                    if st.button(f"🚀 VYZVEDNUTO (Objednávka {doc_name[-5:]})", key=f"vyz_{doc_name}", type="primary"):
                        bestellstatus_aktualisieren(doc_name, "Auf dem Weg zum Kunden", "Petr (Auto)", f["adresa"]["stringValue"])
                        st.rerun()
                elif status == "Auf dem Weg zum Kunden":
                    if st.button(f"✅ DORUČENO (Objednávka {doc_name[-5:]})", key=f"dor_{doc_name}", type="primary"):
                        bestellstatus_aktualisieren(doc_name, "Geliefert", "Petr (Auto)", f["adresa"]["stringValue"])
                        st.rerun()
