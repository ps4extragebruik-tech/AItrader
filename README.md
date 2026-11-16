# AItrader — Pro Market Terminal

Professioneel, mobielvriendelijk Streamlit-dashboard met **echte publieke exchange-marktdata**, interactieve candlestick-grafieken, EMA/RSI, nieuws via RSS en optionele OpenAI-nieuwssamenvatting.

## Veiligheidsstatus

- **Geen echte orderuitvoering**. Alle orderknoppen zijn uitgeschakeld.
- **Geen bankkoppeling**, geen bankwachtwoorden of financiële claims.
- **Geen fictief portfolio of fictieve rendementen**.
- Nieuws via RSS is **niet** milliseconde-snel.
- Een winstgevende AI kan niet gegarandeerd worden.

## Starten

1. Installeer: `pip install -r requirements.txt`
2. Stel de serveromgevingsvariabele `APP_PASSWORD` in met een sterk, uniek wachtwoord.
3. Start: `streamlit run app.py --server.address 0.0.0.0 --server.port 8501`
4. Voor Render: build `pip install -r requirements.txt`, start `streamlit run app.py --server.address 0.0.0.0 --server.port $PORT --server.headless true`.
5. Optioneel: `OPENAI_API_KEY` en `OPENAI_MODEL` als serveromgevingvariabelen. Geen sleutels in GitHub of in de browser zetten.

## Wat nog nodig is voor echt geld

Een afzonderlijke, veilig geïsoleerde trading backend met exchange OAuth/API-permissies, uitvoerbare en geteste risicolimieten, auditlogs, order-reconciliatie, robuuste foutafhandeling, persistente database, fail-closed kill switch, backtests, paper tests en handmatige activering. Gebruik geen gratis slapende webserver voor autonome 24/7 handel.
