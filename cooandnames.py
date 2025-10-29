import pandas as pd
import folium
from folium.plugins import MarkerCluster
from pygbif import species as gbif_species
from pygbif import occurrences as gbif_occ
import sys

# --- CONFIGURAÇÕES DO USUÁRIO ---
# Caminho para o seu arquivo Excel
NOME_ARQUIVO_EXCEL = 'base/BASEDEDADOSNOVA.xlsx'
# Nome da coluna com as coordenadas combinadas (Ex: COORDENADAS)
COLUNA_COORDENADAS_COMBINADAS = 'COORDENADAS'
# *** AJUSTE ESTE NOME para a sua coluna de nome científico ***
COLUNA_ESPECIE = 'NOME'
NOME_ARQUIVO_MAPA_HTML = 'mapa_validacao_gbif_brasil.html'
# revisar

# --- CONSTANTES INTERNAS ---
LATITUDE_FINAL = 'LAT_PLOTAR'
LONGITUDE_FINAL = 'LON_PLOTAR'
COLUNA_STATUS_GBIF = 'GBIF_STATUS'
COLUNA_KEY_GBIF_CONST = 'GBIF_KEY'  # Renomeei a constante para evitar conflito
PAIS_FILTRO_GBIF = 'BR'  # FILTRO PARA O BRASIL


# --- FUNÇÕES DE PROCESSAMENTO (MANTIDAS) ---

def parse_coordenadas_estranhas(coord_str):
    """
    Separa e corrige o formato de coordenada '-XXXXXXX-YYYYYYYY' para Lat/Lon numérico.
    """
    if not isinstance(coord_str, str) or coord_str.count('-') < 2:
        return None, None

    try:
        primeiro_hifen = coord_str.find('-', 1)
        lat_bruto = coord_str[:primeiro_hifen]
        lon_bruto = coord_str[primeiro_hifen:]

        # A: Para Latitude (ex: -1503333 -> -15.03333)
        if len(lat_bruto) > 2 and lat_bruto.startswith('-'):
            lat = float(lat_bruto[:3] + '.' + lat_bruto[3:])
        else:
            return None, None

        # B: Para Longitude (ex: -48446667 -> -48.446667)
        if len(lon_bruto) > 3 and lon_bruto.startswith('-'):
            lon = float(lon_bruto[:4] + '.' + lon_bruto[4:])
        else:
            return None, None

        return lat, lon

    except Exception:
        return None, None


def validar_especie_gbif(nome_cientifico, country_code):
    """Busca a chave taxonômica e verifica a existência de ocorrências no GBIF no país especificado."""

    try:
        res = gbif_species.name_backbone(name=nome_cientifico)
        if not res or res.get('status') != 'ACCEPTED' or 'usageKey' not in res:
            return "NOT FOUND", None, 0

        taxon_key = res['usageKey']

        occ_count = gbif_occ.search(taxonKey=taxon_key, country=country_code, limit=0)
        num_ocorrencias = occ_count.get('count', 0)

        if num_ocorrencias > 0:
            return f"VALIDADO ({country_code} > 0)", taxon_key, num_ocorrencias
        else:
            return f"VALIDADO ({country_code} 0)", taxon_key, num_ocorrencias

    except Exception as e:
        return f"API ERROR: {e}", None, 0


try:
    # 1. Leitura e Parsing dos Dados Locais
    print(f"Lendo dados e parsing de '{COLUNA_COORDENADAS_COMBINADAS}'...")
    df = pd.read_excel(NOME_ARQUIVO_EXCEL)
    df = df.dropna(subset=[COLUNA_COORDENADAS_COMBINADAS])

    resultados_parsing = df[COLUNA_COORDENADAS_COMBINADAS].astype(str).str.replace(',', '.').apply(
        parse_coordenadas_estranhas)
    df[LATITUDE_FINAL] = resultados_parsing.apply(lambda x: x[0])
    df[LONGITUDE_FINAL] = resultados_parsing.apply(lambda x: x[1])
    df = df.dropna(subset=[LATITUDE_FINAL, LONGITUDE_FINAL, COLUNA_ESPECIE])

    if df.empty:
        print("ERRO: Nenhuma linha válida foi encontrada para processamento.")
        sys.exit()

    # 2. Validação GBIF para Espécies Únicas
    especies_unicas = df[[COLUNA_ESPECIE]].drop_duplicates()
    status_list = []

    print(f"\nIniciando validação de espécies no GBIF (Filtro: {PAIS_FILTRO_GBIF})...")

    for index, linha in especies_unicas.iterrows():
        nome = linha[COLUNA_ESPECIE]
        status, key, count = validar_especie_gbif(nome, PAIS_FILTRO_GBIF)

        # A LINHA CORRIGIDA ESTÁ AQUI: Usando a constante COLUNA_KEY_GBIF_CONST
        status_list.append({
            COLUNA_ESPECIE: nome,
            COLUNA_STATUS_GBIF: status,
            COLUNA_KEY_GBIF_CONST: key,
            'GBIF_OCORRENCIAS_BR': count
        })
        print(f" -> {nome}: {status} ({count} ocorrências no BR)")

    df_status = pd.DataFrame(status_list)
    df = df.merge(df_status, on=COLUNA_ESPECIE, how='left')

    # 3. Geração do Mapa Interativo
    print("\nGerando mapa interativo...")
    lat_central = df[LATITUDE_FINAL].mean()
    lon_central = df[LONGITUDE_FINAL].mean()
    m = folium.Map(location=[-15.0, -48.0], zoom_start=4, tiles='OpenStreetMap')

    marker_cluster = MarkerCluster().add_to(m)

    cores = {
        f"VALIDADO ({PAIS_FILTRO_GBIF} > 0)": "green",
        f"VALIDADO ({PAIS_FILTRO_GBIF} 0)": "orange",
        "NOT FOUND": "red",
        "API ERROR": "gray"
    }

    for index, linha in df.iterrows():
        lat = linha[LATITUDE_FINAL]
        lon = linha[LONGITUDE_FINAL]
        especie = linha[COLUNA_ESPECIE]
        status = linha[COLUNA_STATUS_GBIF]

        # Lógica para determinar a cor correta
        if status.startswith("VALIDADO") and status.endswith(" > 0)"):
            cor_icone = cores[f"VALIDADO ({PAIS_FILTRO_GBIF} > 0)"]
        elif status.startswith("VALIDADO") and status.endswith(" 0)"):
            cor_icone = cores[f"VALIDADO ({PAIS_FILTRO_GBIF} 0)"]
        elif status.startswith("NOT FOUND"):
            cor_icone = cores["NOT FOUND"]
        else:
            cor_icone = cores.get(status, 'gray')  # 'gray' para API ERROR

        popup_html = f"""
        <b>Espécie Local:</b> {especie}<br>
        <b>Status GBIF (BR):</b> <span style="color:{cor_icone};">{status}</span><br>
        Lat: {lat:.6f}, Lon: {lon:.6f}
        """

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(color=cor_icone, icon='leaf', prefix='fa')
        ).add_to(marker_cluster)

    m.save(NOME_ARQUIVO_MAPA_HTML)

    print("\n--- SUCESSO ---")
    print(f"O mapa interativo foi salvo em: {NOME_ARQUIVO_MAPA_HTML}")

    # 4. Saída da Tabela de Status
    print("\nSTATUS DAS ESPÉCIES NO GBIF (FILTRADAS POR BRASIL):")
    # Usa a constante COLUNA_KEY_GBIF_CONST para imprimir o resultado
    print(df_status[[COLUNA_ESPECIE, COLUNA_STATUS_GBIF, COLUNA_KEY_GBIF_CONST, 'GBIF_OCORRENCIAS_BR']].to_string(
        index=False))


except Exception as e:
    # Captura outros erros, incluindo KeyError se o nome da coluna estiver errado
    print(f"Ocorreu um erro no processo principal: {e}")