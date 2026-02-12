#!/usr/bin/env python3
"""
Script para baixar o modelo Vosk para português
Usado na inicialização do container
"""

import os
import urllib.request
import zipfile
import shutil

MODELS_DIR = "/app/models"
MODEL_NAME = "vosk-model-pt-br"
MODEL_PATH = os.path.join(MODELS_DIR, MODEL_NAME)

def download_model():
    """Baixa o modelo Vosk para português"""
    
    # Verificar se modelo já existe
    if os.path.exists(MODEL_PATH):
        print(f"✓ Modelo Vosk encontrado em {MODEL_PATH}")
        return True
    
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    # URLs para tentar
    urls = [
        "https://alphacephei.com/vosk/models/vosk-model-small-pt-br-0.3.zip",
        "https://github.com/alphacephei/vosk-models/releases/download/pt-br/vosk-model-small-pt-br-0.3.zip",
    ]
    
    zip_path = os.path.join(MODELS_DIR, "model.zip")
    
    for url in urls:
        try:
            print(f"Tentando baixar modelo de: {url}")
            urllib.request.urlretrieve(url, zip_path)
            
            # Verificar se o arquivo é um ZIP válido
            if zipfile.is_zipfile(zip_path):
                print("✓ Download concluído, extraindo...")
                
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(MODELS_DIR)
                
                # Encontrar a pasta extraída e renomear
                extracted_dirs = [d for d in os.listdir(MODELS_DIR) 
                                 if d.startswith('vosk-model') and d != MODEL_NAME]
                
                if extracted_dirs:
                    src = os.path.join(MODELS_DIR, extracted_dirs[0])
                    dst = MODEL_PATH
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.move(src, dst)
                    print(f"✓ Modelo Vosk instalado com sucesso em {MODEL_PATH}")
                else:
                    print("⚠ Arquivo ZIP extraído mas estrutura não encontrada")
                
                # Limpar arquivo ZIP
                try:
                    os.remove(zip_path)
                except:
                    pass
                
                return True
            else:
                os.remove(zip_path)
                print(f"✗ Arquivo baixado não é ZIP válido, tentando próxima URL...")
                continue
                
        except Exception as e:
            print(f"✗ Erro ao baixar de {url}: {e}")
            continue
    
    print("✗ Não foi possível baixar o modelo Vosk!")
    print("⚠ A aplicação tentará funcionar sem o modelo pré-carregado")
    return False

if __name__ == "__main__":
    download_model()
