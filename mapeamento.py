import pandas as pd
import folium
from folium.plugins import MarkerCluster
from pygbif import occurrences as occ
from pygbif import species
import time

NOME_ARQUIVO_EXCEL = 'base/BASEDEDADOS.xlsx'
COLUNA_ESPECIE = 'ESPECIE'
PAIS_FILTRO = 'BR'
ILHA_COMBU_WKT = 'POLYGON((-48.52 -1.47, -48.45 -1.47, -48.45 -1.42, -48.52 -1.42, -48.52 -1.47))'
FILTRAR_ILHA_COMBU = False
MAX_PONTOS_POR_ESPECIE = 500


def obter_ocorrencias_gbif(nome_cientifico, country_code=None, geometry_wkt=None, limit=MAX_PONTOS_POR_ESPECIE):
    """Busca ocorrências no GBIF, convertendo o nome científico em taxonKey."""
    print(f"Buscando {nome_cientifico}...")

    try:
        busca_nome = species.name_backbone(name=nome_cientifico)
        if not busca_nome or busca_nome.get('status') != 'ACCEPTED':
            print(f"  -> Nome '{nome_cientifico}' não aceito ou não encontrado no GBIF. Pulando.")
            return []
        taxon_key = busca_nome['usageKey']
    except Exception as e:
        print(f"  -> Erro ao buscar TaxonKey para {nome_cientifico}: {e}")
        return []

    filtros = {
        'taxonKey': taxon_key,
        'hasCoordinate': True,
        'hasGeospatialIssue': False,
        'limit': limit
    }
    if country_code:
        filtros['country'] = country_code
    if geometry_wkt and FILTRAR_ILHA_COMBU:
        filtros['geometry'] = geometry_wkt

    dados = []
    offset = 0
    total_records = 0

    while True:
        try:
            filtros['offset'] = offset

            resultado = occ.search(**filtros)

            if not resultado['results']:
                break

            total_records = resultado.get('count', total_records)

            for rec in resultado['results']:
                if rec.get('decimalLatitude') and rec.get('decimalLongitude'):
                    dados.append({
                        'scientificName': nome_cientifico,
                        'latitude': rec['decimalLatitude'],
                        'longitude': rec['decimalLongitude']
                    })

            offset += len(resultado['results'])

            if offset >= limit or offset >= total_records:
                break

            time.sleep(0.5)

        except Exception as e:
            print(f"  -> Erro ao buscar ocorrências para {nome_cientifico}: {e}")
            break

    print(f"  -> Total de {len(dados)} ocorrências válidas encontradas.")
    return dados


def main():
    try:
        df_excel = pd.read_excel(NOME_ARQUIVO_EXCEL)
        nomes_cientificos = df_excel[COLUNA_ESPECIE].unique()
        print(f"Lidas {len(nomes_cientificos)} espécies únicas do Excel.")
    except Exception as e:
        print(f"Erro ao ler o Excel: {e}")
        return

    todos_os_dados_gbif = []
    for nome in nomes_cientificos:
        if pd.notna(nome) and nome:
            ocorrencias = obter_ocorrencias_gbif(
                nome,
                country_code=PAIS_FILTRO,
                geometry_wkt=ILHA_COMBU_WKT
            )
            todos_os_dados_gbif.extend(ocorrencias)

    if not todos_os_dados_gbif:
        print("\nNenhuma ocorrência encontrada no GBIF com os filtros especificados.")
        return

    df_gbif = pd.DataFrame(todos_os_dados_gbif)
    print(f"\nTotal de {len(df_gbif)} ocorrências de todas as espécies (filtradas por País/Área).")


    if FILTRAR_ILHA_COMBU:
        map_center = [-1.445, -48.485]
        zoom = 12
    elif PAIS_FILTRO == 'BR':
        map_center = [-15.0, -48.0]
        zoom = 4
    else:
        map_center = [0, 0]
        zoom = 2

    m = folium.Map(location=map_center, zoom_start=zoom, tiles='CartoDB positron')

    marker_cluster = MarkerCluster().add_to(m)

    for index, row in df_gbif.iterrows():
        lat = row['latitude']
        lon = row['longitude']
        nome = row['scientificName']

        popup_html = f"<b>GBIF</b><br>Espécie: {nome}"

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=200),
            tooltip=nome
        ).add_to(marker_cluster)

    nome_mapa_saida = 'mapa_gbif_especies.html'
    m.save(nome_mapa_saida)

    print(f"\nMapa interativo gerado com sucesso!")
    print(f"Filtros aplicados: País={PAIS_FILTRO}, Ilha do Combu={FILTRAR_ILHA_COMBU}")
    print(f"Abra o arquivo '{nome_mapa_saida}' no seu navegador.")


if __name__ == "__main__":
    main()