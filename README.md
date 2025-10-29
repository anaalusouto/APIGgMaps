# 🌴 GBIF Species Distribution Mapper: Combu Island Focus

## Project Description

This project provides a specialized Python solution for dynamically mapping the occurrence of biological species, with a particular focus on the **Ilha do Combu (Pará, Brazil)**, by leveraging the **Global Biodiversity Information Facility (GBIF) API**.

It allows users to input a list of species names (via an Excel file) and automatically retrieves global occurrence data, applying strict geographic filters to isolate records found within the predetermined bounding box of the Ilha do Combu. The final output is an interactive, Leaflet-based HTML map, providing researchers and conservationists a clear visualization of biodiversity data in this critical region.

### Key Features

  * **Targeted Geographic Filtering (Ilha do Combu):** Includes a predefined WKT (Well-Known Text) polygon filter to restrict GBIF occurrence results specifically to the Ilha do Combu region.
  * **GBIF Data Retrieval:** Seamlessly integrates with the GBIF API using the `pygbif` library to fetch global occurrence records.
  * **Input Flexibility:** Reads scientific names directly from a standard Excel file (`.xlsx`).
  * **Country-Level Filtering:** Allows for an initial filter by **Country Code** (defaulted to 'BR' for Brazil) before applying the local geofence.
  * **Interactive Visualization:** Generates a fully interactive map using the `Folium` library, featuring **Marker Clustering** for efficient display of data points within the island.

## Technologies Used

  * **Python 3.x**
  * **Pandas:** For reading the input Excel file and data handling.
  * **pygbif:** The official Python client for querying the GBIF API.
  * **Folium:** For generating the interactive, Leaflet-based HTML map.

## Installation and Setup

### 1\. Prerequisites

Ensure you have Python 3.x installed.

### 2\. Install Dependencies

Install the required Python packages using `pip`:

```bash
pip install pandas openpyxl pygbif folium
```

## How to Run the Project

### 1\. Prepare Input Data

Create an Excel file (e.g., `species_list.xlsx`) with a column containing the scientific names of the species found in or near the Ilha do Combu (e.g., *Theobroma cacao*, *Euterpe oleracea*).

| Scientific Name (Example) |
| :---------------------- |
| *Theobroma cacao* |
| *Euterpe oleracea* |

### 2\. Configure the Script

Open the Python script (e.g., `gbif_mapper.py`) and adjust the **USER CONFIGURATION** section. **To activate the Combu filter, set the corresponding variable to `True`:**

| Variable | Description | Value for Combu Focus |
| :--- | :--- | :--- |
| `NOME_ARQUIVO_EXCEL` | Path to your input Excel file. | `'species_list.xlsx'` |
| `COLUNA_ESPECIE` | The exact column header containing the species names. | `'Scientific Name'` |
| `PAIS_FILTRO` | ISO 2-letter country code (recommended: 'BR'). | `'BR'` |
| `FILTRAR_ILHA_COMBU` | **Activates the WKT polygon filter for Ilha do Combu.** | `True` |

### 3\. Execution

Run the script from your terminal or PyCharm:

```bash
python gbif_mapper.py
```

## Results and Visualization

Upon successful execution, the script will generate an HTML file in the project directory:

```
mapa_gbif_especies.html
```

To view the map:

1.  Navigate to the project folder.
2.  **Double-click** on `mapa_gbif_especies.html`.

The interactive map will open in your default web browser, centered on the Ilha do Combu, displaying only the occurrence points (if any) that the GBIF has recorded within that defined geographical area.
