import requests
import pandas as pd
from io import StringIO
import json
import geopandas as gpd
import matplotlib.pyplot as plt
import streamlit as st

STATISTIKAAMETI_API_URL = "https://andmed.stat.ee/api/v1/et/stat/RV032"
GEOJSON_FILE = "maakonnad.geojson"   # või .json, täpselt nagu fail repos

JSON_PAYLOAD_STR = """{
  "query": [
    {
      "code": "Aasta",
      "selection": {
        "filter": "item",
        "values": ["2014","2015","2016","2017","2018","2019","2020","2021","2022","2023"]
      }
    },
    {
      "code": "Maakond",
      "selection": {
        "filter": "item",
        "values": ["39","44","49","51","57","59","65","67","70","74","78","82","84","86","37"]
      }
    },
    {
      "code": "Sugu",
      "selection": {
        "filter": "item",
        "values": ["2","3"]
      }
    }
  ],
  "response": {
    "format": "csv"
  }
}"""


@st.cache_data
def import_data():
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
def import_geojson():
    return gpd.read_file(GEOJSON_FILE)


def get_data_for_year(df, year):
    return df[df["Aasta"] == year].copy()


def prepare_data():
    df = import_data()
    gdf = import_geojson()
    merged = gdf.merge(df, left_on="MNIMI", right_on="Maakond")
    return merged


def plot_map(df, year):
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))

    df.plot(
        column="Loomulik iive",
        ax=ax,
        legend=True,
        cmap="viridis",
        legend_kwds={"label": "Loomulik iive"},
        edgecolor="white",
        linewidth=0.8
    )

    ax.set_title(f"Loomulik iive maakonniti aastal {year}", fontsize=18, pad=16)
    ax.axis("off")
    plt.tight_layout()
    return fig


def main():
    st.set_page_config(page_title="Loomulik iive maakonniti", layout="wide")

    st.title("Loomulik iive maakonniti")
    st.write("Vali aasta ja vaata, kuidas loomulik iive maakondade lõikes muutub.")

    merged_data = prepare_data()

    years = sorted(merged_data["Aasta"].unique())
    selected_year = st.sidebar.selectbox("Vali aasta", years, index=len(years) - 1)

    year_data = get_data_for_year(merged_data, selected_year)
    fig = plot_map(year_data, selected_year)
    st.pyplot(fig)

    with st.expander("Näita andmeid"):
        st.dataframe(
            year_data[["Maakond", "Aasta", "Mehed Loomulik iive", "Naised Loomulik iive", "Loomulik iive"]]
            .sort_values("Maakond")
            .reset_index(drop=True),
            use_container_width=True
        )


if __name__ == "__main__":
    main()
