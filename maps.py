import pandas as pd
import folium

# --- Configurações Iniciais ---
# 1. Nome do seu arquivo Excel
nome_arquivo_excel = 'especies_coordenadas.xlsx'

# 2. Defina o nome exato das colunas de Latitude, Longitude e Identificação (no seu Excel)
COLUNA_LATITUDE = 'Latitude'
COLUNA_LONGITUDE = 'Longitude'
COLUNA_ESPECIE = 'Nome da Espécie'

# 3. Nome do arquivo HTML de saída
nome_arquivo_mapa_html = 'mapa_especies.html'

try:
    # --- Passo 1: Leitura dos Dados do Excel com Pandas ---
    df = pd.read_excel(nome_arquivo_excel)

    # 4. Limpeza e Verificação de Colunas
    # Garante que as colunas de coordenadas sejam tratadas como números
    df[COLUNA_LATITUDE] = pd.to_numeric(df[COLUNA_LATITUDE], errors='coerce')
    df[COLUNA_LONGITUDE] = pd.to_numeric(df[COLUNA_LONGITUDE], errors='coerce')

    # Remove linhas onde a latitude ou longitude não são válidas (NaN)
    df = df.dropna(subset=[COLUNA_LATITUDE, COLUNA_LONGITUDE])

    if df.empty:
        print("Erro: Nenhuma coordenada válida encontrada após a limpeza dos dados.")
        exit()

    # --- Passo 2: Criação do Mapa Base com Folium ---

    # Calcula o ponto central do mapa com base na média das coordenadas
    lat_central = df[COLUNA_LATITUDE].mean()
    lon_central = df[COLUNA_LONGITUDE].mean()

    # Cria o mapa. O zoom inicial (ex: 4) pode ser ajustado.
    # Você pode alterar 'tiles' para 'Stamen Terrain', 'CartoDB positron', etc.
    m = folium.Map(location=[lat_central, lon_central], zoom_start=4, tiles='OpenStreetMap')

    # --- Passo 3: Iteração e Adição dos Marcadores (Pins) ---

    print(f"Plotando {len(df)} ocorrências no mapa...")

    for index, linha in df.iterrows():
        lat = linha[COLUNA_LATITUDE]
        lon = linha[COLUNA_LONGITUDE]
        especie = linha[COLUNA_ESPECIE]

        # Conteúdo que aparecerá no pop-up do marcador
        popup_html = f"""
        <b>Espécie:</b> {especie}<br>
        Lat: {lat:.4f}, Lon: {lon:.4f}
        """

        # Adiciona o marcador ao mapa
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=especie  # Texto que aparece ao passar o mouse
        ).add_to(m)

    # --- Passo 4: Salvar o Mapa ---
    m.save(nome_arquivo_mapa_html)

    print(f"\nSucesso! O mapa interativo foi salvo em: {nome_arquivo_mapa_html}")
    print(f"Abra o arquivo '{nome_arquivo_mapa_html}' no seu navegador para visualizar.")

except FileNotFoundError:
    print(f"Erro: O arquivo '{nome_arquivo_excel}' não foi encontrado.")
except KeyError as e:
    print(f"Erro: A coluna {e} não foi encontrada no seu Excel.")
    print(f"Verifique se as variáveis COLUNA_LATITUDE, COLUNA_LONGITUDE e COLUNA_ESPECIE estão corretas.")
except Exception as e:
    print(f"Ocorreu um erro: {e}")