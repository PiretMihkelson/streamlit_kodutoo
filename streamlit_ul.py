import requests
import pandas as pd
from io import StringIO
import json
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection

STATISTIKAAMETI_API_URL = "https://andmed.stat.ee/api/v1/et/stat/RV032"
GEOJSON_FILE = "maakonnad.json"   # kui fail on .geojson, muuda see vastavalt

JSON_PAYLOAD_STR = """{
  "query": [
    {
      "code": "Aasta",
      "selection": {
        "filter": "item",
        "values": [
          "2014",
          "2015",
          "2016",
          "2017",
          "2018",
          "2019",
          "2020",
          "2021",
          "2022",
          "2023"
        ]
      }
    },
    {
      "code": "Maakond",
      "selection": {
        "filter": "item",
        "values": [
          "39",
          "44",
          "49",
          "51",
          "57",
          "59",
          "65",
          "67",
          "70",
          "74",
          "78",
          "82",
          "84",
          "86",
          "37"
        ]
      }
    },
    {
      "code": "Sugu",
      "selection": {
        "filter": "item",
        "values": [
          "2",
          "3"
        ]
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
    return df[df["Aasta"] == year].copy()


def extract_polygons(geometry):
    polygons = []

    if geometry["type"] == "Polygon":
        for ring in geometry["coordinates"]:
            polygons.append(ring)

    elif geometry["type"] == "MultiPolygon":
        for polygon in geometry["coordinates"]:
            for ring in polygon:
                polygons.append(ring)

    return polygons


def plot_map(year_data: pd.DataFrame, geojson_data: dict, year: int):
    value_map = dict(zip(year_data["Maakond"], year_data["Loomulik iive"]))

    patches = []
    patch_values = []

    for feature in geojson_data["features"]:
        maakond_nimi = feature["properties"]["MNIMI"]
        value = value_map.get(maakond_nimi)

        if value is None:
            continue

        polygons = extract_polygons(feature["geometry"])

        for coords in polygons:
            patches.append(Polygon(coords, closed=True))
            patch_values.append(value)

    fig, ax = plt.subplots(figsize=(12, 8))

    collection = PatchCollection(
        patches,
        cmap="viridis",
        edgecolor="none",
        linewidth=0.3
    )
    collection.set_array(pd.Series(patch_values).to_numpy())

    ax.add_collection(collection)
    ax.autoscale_view()
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(f"Loomulik iive maakonniti aastal {year}", fontsize=16, pad=12)

    cbar = fig.colorbar(collection, ax=ax, shrink=0.82, pad=0.02)
    cbar.set_label("Loomulik iive")

    plt.tight_layout()
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
    st.pyplot(fig)

    with st.expander("Näita andmeid"):
        st.dataframe(
            year_data[
                ["Maakond", "Aasta", "Mehed Loomulik iive", "Naised Loomulik iive", "Loomulik iive"]
            ]
            .sort_values("Maakond")
            .reset_index(drop=True),
            use_container_width=True
        )


if __name__ == "__main__":
    main()
