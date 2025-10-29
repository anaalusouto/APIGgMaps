import pandas as pd
import folium
from folium.plugins import MarkerCluster
import sys

# --- CONFIGURAÇÕES DO USUÁRIO ---
# 1. O nome do seu arquivo Excel (certifique-se de que está na mesma pasta do script)
NOME_ARQUIVO_EXCEL = 'base/BASEDEDADOSNOVA.xlsx'

COLUNA_COORDENADAS_COMBINADAS = 'COORDENADAS'

# 3. Nome da coluna que contém a espécie/título (para o pop-up no mapa)
COLUNA_ESPECIE = 'NOME'

# 4. Nome do arquivo HTML que será gerado:
NOME_ARQUIVO_MAPA_HTML = 'mapa_coordenadas_locais.html'

# --- INÍCIO DO PROCESSO ---

# Nomes temporários que usaremos internamente para as colunas separadas
LATITUDE_FINAL = 'LAT_PLOTAR'
LONGITUDE_FINAL = 'LON_PLOTAR'


def parse_coordenadas_estranhas(coord_str):
    """Separa e insere o ponto decimal em coordenadas no formato '-XXXXXXX-YYYYYYYY'"""
    if not isinstance(coord_str, str) or coord_str.count('-') < 2:
        return None, None

    try:
        # A Longitude começa APÓS o segundo hífen.
        # Ex: '-1503333-48446667' -> Lat: -1503333, Lon: -48446667

        primeiro_hifen = coord_str.find('-', 1)  # Encontra o primeiro hífen após o sinal de negativo inicial

        lat_bruto = coord_str[:primeiro_hifen]
        lon_bruto = coord_str[primeiro_hifen:]

        # Inserir ponto decimal (Assumindo que Lat tem 2 dígitos inteiros e Lon tem 3)
        # Assumimos que o ponto decimal deve ser colocado após os dois primeiros dígitos (ex: -15.03333)

        # A: Para Latitude (ex: -1503333) -> -15.03333
        if len(lat_bruto) > 2 and lat_bruto.startswith('-'):
            lat = float(lat_bruto[:3] + '.' + lat_bruto[3:])
        else:
            return None, None

        # B: Para Longitude (ex: -48446667) -> -48.446667
        if len(lon_bruto) > 3 and lon_bruto.startswith('-'):
            lon = float(lon_bruto[:4] + '.' + lon_bruto[4:])
        else:
            return None, None

        return lat, lon

    except ValueError:
        return None, None
    except Exception:
        return None, None


try:
    # 1. Leitura dos Dados do Excel com Pandas
    print(f"Lendo dados do arquivo: {NOME_ARQUIVO_EXCEL}...")
    df = pd.read_excel(NOME_ARQUIVO_EXCEL)

    # 2. SEPARAÇÃO E LIMPEZA DE DADOS (USANDO A NOVA FUNÇÃO)
    print(f"Processando a coluna '{COLUNA_COORDENADAS_COMBINADAS}' para Lat/Lon...")

    # 2a. Trata linhas onde a coluna está vazia
    df = df.dropna(subset=[COLUNA_COORDENADAS_COMBINADAS])

    # 2b. Aplica a função de parsing a cada linha e cria as colunas temporárias
    # O .str.replace(',', '.') é um passo de segurança, caso haja vírgulas.
    resultados = df[COLUNA_COORDENADAS_COMBINADAS].astype(str).str.replace(',', '.').apply(parse_coordenadas_estranhas)

    # Atribui os resultados separados
    df[LATITUDE_FINAL] = resultados.apply(lambda x: x[0])
    df[LONGITUDE_FINAL] = resultados.apply(lambda x: x[1])

    # 2c. Remove linhas onde a conversão falhou (retornou None)
    df = df.dropna(subset=[LATITUDE_FINAL, LONGITUDE_FINAL])

    if df.empty:
        print(
            "ERRO: Nenhuma coordenada válida pôde ser extraída e formatada. Verifique se o formato é exatamente '-XXXXXXX-YYYYYYYY'.")
        sys.exit()

    # 3. Determinação do Centro do Mapa
    lat_central = df[LATITUDE_FINAL].mean()
    lon_central = df[LONGITUDE_FINAL].mean()

    # 4. Criação do Mapa Base com Folium
    print(f"Criando mapa centrado em: Lat={lat_central:.4f}, Lon={lon_central:.4f}")
    m = folium.Map(location=[lat_central, lon_central], zoom_start=8, tiles='OpenStreetMap')

    marker_cluster = MarkerCluster().add_to(m)

    # 5. Iteração e Adição dos Marcadores
    print(f"Plotando {len(df)} coordenadas no mapa...")

    for index, linha in df.iterrows():
        lat = linha[LATITUDE_FINAL]
        lon = linha[LONGITUDE_FINAL]
        especie = linha.get(COLUNA_ESPECIE, 'Espécie Não Informada')

        popup_html = f"""
        <b>Espécie:</b> {especie}<br>
        Lat: {lat:.6f}, Lon: {lon:.6f}
        """

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=especie
        ).add_to(marker_cluster)

    # 6. Salvar o Mapa
    m.save(NOME_ARQUIVO_MAPA_HTML)

    print("\n--- SUCESSO ---")
    print(f"O mapa interativo foi salvo em: {NOME_ARQUIVO_MAPA_HTML}")
    print("Abra este arquivo no seu navegador para visualizar.")

except FileNotFoundError:
    print(f"ERRO: O arquivo '{BASEDEDADOSNOVA}' não foi encontrado. Verifique o caminho.")
except KeyError:
    print(
        f"ERRO: A coluna '{COORDENADAS}' ou '{NOME}' não foi encontrada. Verifique se o nome está EXATAMENTE igual (incluindo espaços e maiúsculas/minúsculas) na sua planilha e na configuração do código.")
except Exception as e:
    print(f"Ocorreu um erro inesperado: {e}")