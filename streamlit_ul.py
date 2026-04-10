import requests
import pandas as pd
from io import StringIO
import json
import streamlit as st
import plotly.express as px

STATISTIKAAMETI_API_URL = "https://andmed.stat.ee/api/v1/et/stat/RV032"
GEOJSON_FILE = "maakonnad.geojson"  # pane siia täpselt see failinimi, mis GitHubis olemas on

JSON_PAYLOAD_STR = """{
  "query": [
    {
      "code": "Aasta",
      "selection": {
        "filter": "item",
        "values": [
          "2014","2015","2016","2017","2018",
          "2019","2020","2021","2022","2023"
        ]
      }
    },
    {
      "code": "Maakond",
      "selection": {
        "filter": "item",
        "values": [
          "39","44","49","51","57",
          "59","65","67","70","74",
          "78","82","84","86","37"
        ]
      }
    },
    {
      "code": "Sugu",
      "selection": {
        "filter": "item",
        "values": ["2", "3"]
      }
    }
  ],
  "response": {
    "format": "csv"
  }
}"""


@st.cache_data
def import_data() -> pd.DataFrame:
    headers = {"Content-Type": "application/json"}
    parsed_payload = json.loads(JSON_PAYLOAD_STR)

    response = requests.post(
        STATISTIKAAMETI_API_URL,
        json=parsed_payload,
        headers=headers,
        timeout=30
    )
    response.raise_for_status()

    text = response.content.decode("utf-8-sig")
    df = pd.read_csv(StringIO(text))

    df["Loomulik iive"] = df["Mehed Loomulik iive"] + df["Naised Loomulik iive"]
    return df


@st.cache_data
def import_geojson() -> dict:
    with open(GEOJSON_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_data_for_year(df: pd.DataFrame, year: int) -> pd.DataFrame:
    year_df = df[df["Aasta"] == year].copy()
    return year_df


def plot_map(df: pd.DataFrame, geojson_data: dict, year: int):
    fig = px.choropleth(
        df,
        geojson=geojson_data,
        locations="Maakond",
        featureidkey="properties.MNIMI",
        color="Loomulik iive",
        hover_name="Maakond",
        hover_data={
            "Aasta": True,
            "Mehed Loomulik iive": True,
            "Naised Loomulik iive": True,
            "Loomulik iive": True
        },
        title=f"Loomulik iive maakonniti aastal {year}"
    )

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r": 0, "t": 60, "l": 0, "b": 0})

    return fig


def main():
    st.set_page_config(page_title="Loomulik iive maakonniti", layout="wide")

    st.title("Loomulik iive maakonniti")
    st.write("Vali aasta ja vaata, kuidas loomulik iive maakondade lõikes muutub.")

    df = import_data()
    geojson_data = import_geojson()

    years = sorted(df["Aasta"].unique())
    selected_year = st.sidebar.selectbox("Vali aasta", years, index=len(years) - 1)

    year_data = get_data_for_year(df, selected_year)
    fig = plot_map(year_data, geojson_data, selected_year)
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Näita andmeid"):
        st.dataframe(
            year_data[["Maakond", "Aasta", "Mehed Loomulik iive", "Naised Loomulik iive", "Loomulik iive"]]
            .sort_values("Maakond")
            .reset_index(drop=True),
            use_container_width=True
        )


if __name__ == "__main__":
    main()