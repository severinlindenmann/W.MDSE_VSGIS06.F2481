import streamlit as st
from data import sharedmobility


st.set_page_config(
    page_title="Stadt Luzern | Nextbike",
    page_icon="👋",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://severin.io",
        "Report a bug": "https://severin.io",
        "About": "Analytics Tool Nextbike, erstellt von Severin Lindenmann",
    },
)

title_alignment ="""
<style>
h4 {
  text-align: center
}
</style>
"""

st.markdown(title_alignment, unsafe_allow_html=True)


st.markdown("""
# Analyse von Nextbike Daten in der Stadt Luzern
## im Studiengang B.Sc. Mobility, Data Science and Economics der Hochschule Luzern
#### by Severin Lindenmann, Mai 2024
            """)

st.info("Die Analyse wurde mit öffentlich Zugänglichen Daten durchgeführt. Die Quellen dafür sind unten aufgeführt.")

df = sharedmobility()
st.dataframe(df)

st.markdown("""
### Quellen
- [Nextbike](https://www.nextbike.de/de/)
- [Open Data Luzern](https://data.stadt-luzern.ch/)
- [Open Weather](https://open-meteo.com/)
- [Veloverkehr](https://www.veloverkehr.ch/)
- [Google Maps](https://cloud.google.com/maps-platform)
""")