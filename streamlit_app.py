import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

st.title("Datavisualisointi")
st.divider()

st.header("Tarkastele analyysiä Helsingin ja Espoon kaupunkipyörien käytöstä")

st.write("Tämä sovellus käsittelee kaupunkipyöräasemien Origin-Destination (OD) -dataa, joka pitää sisällään tiedot yksittäisten matkojen lähtö- ja päätösasemista, lähtö- ja päätösajoista, pituuksista sekä kestoista. Oletusaineistona näytetään Huhtikuun 2021 dataa, jonka analyysit löytyvät alta.")
         
st.markdown('''
**Saatavilla oleva aineistopaketti Huhtikuu-Lokakuu 2021(csv) on ladattavissa alla olevasta linkistä.**  
[Aineistopaketti 2021 (zip)](https://dev.hsl.fi/citybikes/od-trips-2021/od-trips-2021.zip)
''')

st.markdown('''
**Aineistojen lähdesivu.**  
[Helsinki Region Infoshare](https://hri.fi/data/fi/dataset/helsingin-ja-espoon-kaupunkipyorilla-ajatut-matkat)
''')
            
st.markdown('''
**Datan omistaa City Bike Finland ja se on lisensoitu seuraavasti:**  
[Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/)
''')

# Oletusdatan nouto
DATA_URL = "https://dev.hsl.fi/citybikes/od-trips-2021/2021-04.csv"

@st.cache_data
def load_data(url):
    df = pd.read_csv(url)
    return df

# Käyttäjän vaihtoehto
uploaded_file = st.file_uploader("Lataa CSV-tiedosto tai käytä valmista aineistoa. Raahaa ja pudota tiedosto (Drag and drop) tai lataa tiedosto koneeltasi (Browse files).", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("Käytetään ladattua tiedostoa!")
else:
    df = load_data(DATA_URL)
    st.info("Käytetään oletusaineistoa (Huhtikuu 2021).")

# Varmistetaan, että data on ladattu
if df is not None and not df.empty:
    # Muunnetaan lähtöaika datetime-muotoon
    df["Departure"] = pd.to_datetime(df["Departure"], errors="coerce", dayfirst=True)

    # Aikavälisuodatus
    with st.sidebar:
        st.subheader("Valitse aikaväli")
        start_date = st.date_input("Aloituspäivämäärä", datetime.date(2021, 4, 1))
        end_date = st.date_input("Lopetuspäivämäärä", datetime.date(2021, 4, 30))

        # Lähtö- ja paluuaseman suodatus
        st.subheader("Suodata aseman mukaan")
        unique_stations = sorted(set(df["Departure station name"].dropna().unique()) | set(df["Return station name"].dropna().unique()))
        selected_departure = st.selectbox("Valitse lähtöasema", ["Kaikki"] + unique_stations)
        selected_return = st.selectbox("Valitse paluuasema", ["Kaikki"] + unique_stations)

    df = df[(df["Departure"].dt.date >= start_date) & (df["Departure"].dt.date <= end_date)]

    if selected_departure != "Kaikki":
        df = df[df["Departure station name"] == selected_departure]

    if selected_return != "Kaikki":
        df = df[df["Return station name"] == selected_return]

    if df.empty:
        st.warning("Valitulla suodatuksella ei ole dataa! Kokeile toista valintaa.")
    else:
        st.write("**Ensimmäiset rivit datasta**")

        # Näytetään data suomenkielisillä sarakeotsikoilla
        suomennokset = {
            "Departure": "Lähtöaika",
            "Return": "Paluu",
            "Departure station id": "Lähtöaseman tunnus",
            "Departure station name": "Lähtöasema",
            "Return station id": "Paluuaseman tunnus",
            "Return station name": "Paluuasema",
            "Covered distance (m)": "Matkan pituus (m)",
            "Duration (sec.)": "Kesto (s)"
        }

        df_naytto = df[list(suomennokset.keys())].rename(columns=suomennokset)
        st.write(df_naytto.head())

        required_columns = {"Departure", "Departure station name", "Return station name", "Covered distance (m)", "Duration (sec.)"}
        if required_columns.issubset(df.columns):
            df["Hour"] = df["Departure"].dt.hour
            df["Weekday"] = df["Departure"].dt.day_name()

            # Viikonpäivien suomennos
            viikonpaivat = {
                "Monday": "Maanantai",
                "Tuesday": "Tiistai",
                "Wednesday": "Keskiviikko",
                "Thursday": "Torstai",
                "Friday": "Perjantai",
                "Saturday": "Lauantai",
                "Sunday": "Sunnuntai"
            }
            df["Weekday"] = df["Weekday"].map(viikonpaivat)

            # Aseman määrän säätö
            st.write("**Säädä näytettävien asemien määrää alla näkyvissä infograafeissa**")
            station_count = st.slider("Näytettävien asemien määrä (10–50)", min_value=10, max_value=50, value=10)

            top_departures = df["Departure station name"].value_counts().nlargest(station_count)
            top_returns = df["Return station name"].value_counts().nlargest(station_count)

            df_departures = pd.DataFrame({"Station": top_departures.index, "Trips": top_departures.values})
            df_returns = pd.DataFrame({"Station": top_returns.index, "Trips": top_returns.values})

            fig_departures = px.bar(df_departures, x="Station", y="Trips", title="Suosituimmat lähtöasemat", text_auto=True, labels={"Station": "Asema", "Trips": "Matkat"})
            fig_returns = px.bar(df_returns, x="Station", y="Trips", title="Suosituimmat palautusasemat", text_auto=True, labels={"Station": "Asema", "Trips": "Matkat"})

            st.plotly_chart(fig_departures)
            st.plotly_chart(fig_returns)

            avg_distance = df.groupby("Departure station name")["Covered distance (m)"].mean().nlargest(station_count)
            df_avg_distance = pd.DataFrame({"Station": avg_distance.index, "Avg Distance (m)": avg_distance.values})

            fig_avg_distance = px.bar(df_avg_distance, x="Station", y="Avg Distance (m)", 
                                      title="Keskimääräinen matkan pituus per lähtöasema", text_auto=True, labels={"Station": "Asema", "Avg Distance (m)": "Keskimääräinen matkan pituus"})

            st.plotly_chart(fig_avg_distance)

            hourly_counts = df["Hour"].value_counts().sort_index()
            fig_hourly = px.line(x=hourly_counts.index, y=hourly_counts.values, labels={"x": "Tunti", "y": "Matkojen määrä"},
                                 title="Matkustamisen määrä tunneittain")
            st.plotly_chart(fig_hourly)

            weekday_counts = df["Weekday"].value_counts()
            fig_weekday = px.bar(x=weekday_counts.index, y=weekday_counts.values, labels={"x": "Viikonpäivä", "y": "Matkojen määrä"},
                                 title="Matkustamisen määrä viikonpäivittäin")
            st.plotly_chart(fig_weekday)
        else:
            st.error("CSV-tiedostosta puuttuu tarvittavia sarakkeita!")
else:
    st.error("Dataa ei voitu ladata. Tarkista tiedosto tai URL!")


