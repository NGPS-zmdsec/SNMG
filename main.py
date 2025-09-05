import os
import threading
import time
from pathlib import Path
from datetime import datetime
import requests
from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Sat Norte de Minas Gerais")

# ---------------- Configuração de Diretórios ----------------
# A linha abaixo usa um caminho absoluto para evitar erros de diretório na Render
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
FRONTEND_DIR = BASE_DIR / "frontend"
DATA_DIR.mkdir(exist_ok=True)

# ---------------- Constantes de Localização ----------------
# BBOX para a região de Norte de Minas Gerais
LON_MIN, LAT_MIN = -46.5, -17.5
LON_MAX, LAT_MAX = -42.0, -14.0

# ---------------- Funções de Download de Imagens ----------------
def get_gibs_image():
    """
    Tenta baixar a imagem mais recente do satélite VIIRS da NASA GIBS.
    """
    print("🚀 Iniciando o download da imagem da NASA GIBS...")
    try:
        # Pega a data de hoje para buscar a imagem mais recente
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        
        # URL da API da NASA GIBS com os parâmetros corretos
        gibs_url = (
            f"https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?SERVICE=WMS"
            f"&REQUEST=GetMap&VERSION=1.3.0&LAYERS=VIIRS_SNPP_CorrectedReflectance_TrueColor"
            f"&STYLES=&FORMAT=image/jpeg&TRANSPARENT=FALSE&HEIGHT=800&WIDTH=800"
            f"&CRS=EPSG:4326&BBOX={LON_MIN},{LAT_MIN},{LON_MAX},{LAT_MAX}"
            f"&TIME={date_str}"
        )
        
        response = requests.get(gibs_url)

        if response.status_code == 200:
            image_path = DATA_DIR / "satellite_image.jpg"
            with open(image_path, "wb") as f:
                f.write(response.content)
            print("✅ Download da imagem do satélite concluído.")
            return True
        else:
            print(f"❌ Erro ao baixar a imagem da NASA GIBS: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro na requisição ao GIBS: {e}")
        return False

# ---------------- Atualização Periódica ----------------
def atualizar_periodicamente():
    """
    Tarefa que roda em segundo plano para baixar a imagem a cada 4 horas.
    """
    while True:
        get_gibs_image()
        time.sleep(4 * 3600)  # 4 horas em segundos

@app.on_event("startup")
def startup_event():
    """
    Função que inicia a tarefa de atualização quando o servidor é iniciado.
    """
    thread = threading.Thread(target=atualizar_periodicamente, daemon=True)
    thread.start()

# ---------------- Endpoints da API ----------------
@app.get("/api")
def root():
    return {"message": "Bem-vindo ao Sat Norte de Minas Gerais 🚀"}

@app.get("/api/image.jpg")
def get_image():
    """
    Endpoint que serve a imagem de satélite baixada.
    """
    image_path = DATA_DIR / "satellite_image.jpg"
    if image_path.exists():
        with open(image_path, "rb") as f:
            content = f.read()
        return Response(content=content, media_type="image/jpeg")
    else:
        return {"error": "Imagem não encontrada."}

# ---------------- Frontend (Página Web) ----------------
# A forma mais robusta de montar a pasta estática
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

# ---------------- Execução do Servidor ----------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 0)) or 8000
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
