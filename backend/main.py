import os
import sys
import json
import wave
import whisper
import subprocess
from pydub import AudioSegment
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil
from datetime import datetime
import time
import threading

# Configuração
# Use /tmp/uploads em ambiente de teste, /app/uploads em produção
if "pytest" in sys.modules or os.getenv("TESTING") == "1":
    UPLOAD_DIR = "/tmp/uploads"
else:
    UPLOAD_DIR = "/app/uploads"
    
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Rastreador de progresso
progress_tracker = {
    'current_percent': 0,
    'status': 'waiting',
    'result': None,
    'error': None,
    'lock': threading.Lock()
}

# Criar app FastAPI
app = FastAPI(title="Audio Transcription API")

# CORS middleware para aceitar requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar Whisper
print("Carregando modelo Whisper (offline)...")
try:
    # Usar modelo 'base' que suporta português e é mais rápido que 'small'
    whisper_model = whisper.load_model("base")
    print("✓ Whisper pronto para usar! (modelo: base)")
except Exception as e:
    print(f"⚠ Aviso ao carregar Whisper: {e}")
    whisper_model = None

def validate_audio_file(file_path):
    """Valida se o arquivo de áudio é válido"""
    try:
        if file_path.endswith('.wav'):
            with wave.open(file_path, 'rb') as wf:
                frames = wf.getnframes()
                print(f"Validação WAV - Frames: {frames}, Channels: {wf.getnchannels()}, Frame rate: {wf.getframerate()}")
                if frames == 0:
                    raise Exception(f"Arquivo WAV vazio (0 frames)")
                return True
        else:
            audio = AudioSegment.from_file(file_path)
            duration_ms = len(audio)
            print(f"Validação {Path(file_path).suffix} - Duração: {duration_ms}ms, Channels: {audio.channels}, Frame rate: {audio.frame_rate}")
            if duration_ms == 0:
                raise Exception(f"Arquivo vazio (0 ms)")
            return True
    except Exception as e:
        print(f"✗ Erro ao validar arquivo: {e}")
        raise

def convert_audio_to_wav(file_path):
    """Converte áudio para WAV usando FFmpeg (mais confiável que pydub)"""
    if file_path.endswith('.wav'):
        validate_audio_file(file_path)
        return file_path
    
    try:
        print(f"Convertendo {file_path} para WAV com FFmpeg...")
        original_size = os.path.getsize(file_path) / 1024 / 1024
        print(f"Arquivo original: {original_size:.2f} MB")
        
        wav_path = file_path.replace(Path(file_path).suffix, '.wav')
        
        # Use FFmpeg command to convert to WAV with specific parameters
        # -acodec pcm_s16le = PCM 16-bit little-endian (padrão do Whisper)
        # -ar 16000 = 16kHz sample rate
        # -ac 1 = 1 channel (mono)
        cmd = [
            'ffmpeg',
            '-i', file_path,
            '-acodec', 'pcm_s16le',
            '-ar', '16000',
            '-ac', '1',
            '-y',  # Sobrescrever arquivo se existir
            wav_path
        ]
        
        print(f"Executando: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode != 0:
            error_msg = result.stderr[-500:] if result.stderr else "Erro desconhecido"
            raise Exception(f"FFmpeg falhou: {error_msg}")
        
        # Validar arquivo WAV criado
        if not os.path.exists(wav_path):
            raise Exception(f"Arquivo WAV não foi criado: {wav_path}")
        
        wav_size = os.path.getsize(wav_path) / 1024 / 1024
        print(f"Arquivo WAV criado: {wav_size:.2f} MB")
        
        if wav_size < 0.1:  # Menos de 100KB é suspeito
            raise Exception(f"Arquivo WAV muito pequeno ({wav_size:.2f} MB) - conversão pode ter falhado")
        
        validate_audio_file(wav_path)
        
        # Remover arquivo original
        try:
            os.remove(file_path)
            print(f"✓ Arquivo original removido: {file_path}")
        except Exception as e:
            print(f"⚠ Aviso ao remover arquivo original: {e}")
        
        return wav_path
        
    except subprocess.TimeoutExpired:
        raise Exception("Timeout na conversão FFmpeg (arquivo muito grande)")
    except Exception as e:
        print(f"✗ Erro ao converter áudio com FFmpeg: {e}")
        import traceback
        traceback.print_exc()
        raise Exception(f"Falha na conversão de áudio: {str(e)}")

def extract_audio_metadata(file_path):
    """Extrai metadados do arquivo de áudio"""
    try:
        from mutagen.wave import WAVE
        from mutagen.mp3 import MP3
        from mutagen.flac import FLAC
        
        metadata = {
            "title": "N/A",
            "artist": "N/A",
            "duration": "N/A",
            "format": Path(file_path).suffix[1:].upper()
        }
        
        try:
            # Tentar MP3
            if file_path.endswith('.mp3'):
                audio = MP3(file_path)
                if audio.tags:
                    metadata["title"] = str(audio.tags.get('TIT2', 'N/A'))
                    metadata["artist"] = str(audio.tags.get('TPE1', 'N/A'))
                metadata["duration"] = str(int(audio.info.length)) + " segundos"
        except:
            pass
        
        try:
            # Tentar WAV
            if file_path.endswith('.wav'):
                audio = WAVE(file_path)
                info = audio.info
                metadata["duration"] = str(int(info.length)) + " segundos"
        except:
            pass
        
        return metadata
    except Exception as e:
        print(f"Erro ao extrair metadados: {e}")
        return {
            "title": "N/A",
            "artist": "N/A",
            "duration": "N/A",
            "format": Path(file_path).suffix[1:].upper() if file_path else "N/A"
        }

@app.get("/")
async def root():
    return {"message": "Audio Transcription API - Sistema de Transcrição de Áudio"}

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    """
    Endpoint para transcrição de áudio
    
    Aceita arquivos de áudio em formatos: MP3, WAV, FLAC, M4A, OGG
    Retorna: Transcrição em texto, metadados do áudio, timestamp
    """
    try:
        # Validar tipo de arquivo
        allowed_extensions = {'.mp3', '.wav', '.flac', '.m4a', '.ogg', '.wma', '.aac'}
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in allowed_extensions:
            return JSONResponse(
                status_code=400,
                content={"error": f"Formato não suportado. Use: {', '.join(allowed_extensions)}"}
            )
        
        # Salvar arquivo temporário
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"Arquivo recebido: {file.filename}")
        
        # Iniciar thread background
        def process_audio_background():
            file_path_to_cleanup = file_path
            wav_path_to_cleanup = None
            
            try:
                # Extrair metadados (antes de converter)
                metadata = extract_audio_metadata(file_path)
                print(f"Metadados extraídos: {metadata}")
                
                with progress_tracker['lock']:
                    progress_tracker['status'] = 'converting'
                    progress_tracker['current_percent'] = 5
                
                # Converter para WAV se necessário
                print(f"Arquivo original: {file_path} ({os.path.getsize(file_path)/1024/1024:.2f} MB)")
                wav_path = convert_audio_to_wav(file_path)
                wav_path_to_cleanup = wav_path
                print(f"Arquivo WAV convertido: {wav_path} ({os.path.getsize(wav_path)/1024/1024:.2f} MB)")
                
                with progress_tracker['lock']:
                    progress_tracker['status'] = 'processing'
                    progress_tracker['current_percent'] = 10
                
                # Transcrever áudio localmente com Whisper
                print("Iniciando transcrição com Whisper (offline)...")
                transcription_text = transcribe_audio_with_whisper(wav_path)
                print("Transcrição completa!")
                
                # Salvar arquivo de transcrição
                txt_file_path = save_transcription_file(transcription_text, file.filename)
                txt_filename = os.path.basename(txt_file_path) if txt_file_path else None
                
                # Preparar resultado
                result = {
                    "status": "success",
                    "transcription": transcription_text,
                    "metadata": {
                        "filename": file.filename,
                        "title": metadata.get("title", "N/A"),
                        "artist": metadata.get("artist", "N/A"),
                        "duration": metadata.get("duration", "N/A"),
                        "format": metadata.get("format", "N/A")
                    },
                    "timestamp": datetime.now().isoformat(),
                    "model": "Whisper (Offline)",
                    "language": "Portuguese (Brazil)",
                    "download_file": txt_filename
                }
                
                # Armazenar resultado e marcar como completo
                with progress_tracker['lock']:
                    progress_tracker['result'] = result
                    progress_tracker['status'] = 'completed'
                    progress_tracker['current_percent'] = 100
                    progress_tracker['error'] = None
                
                print("✓ Resultado pronto para envio")
                
            except Exception as e:
                print(f"✗ Erro no processamento background: {str(e)}")
                import traceback
                traceback.print_exc()
                
                with progress_tracker['lock']:
                    progress_tracker['status'] = 'error'
                    progress_tracker['error'] = str(e)
                    progress_tracker['current_percent'] = 0
                    progress_tracker['result'] = None
            
            finally:
                # Sempre limpar arquivos de áudio, mesmo em caso de erro
                cleanup_count = 0
                
                # Remover arquivo original
                if file_path_to_cleanup and os.path.exists(file_path_to_cleanup):
                    try:
                        os.remove(file_path_to_cleanup)
                        print(f"✓ Arquivo removido: {file_path_to_cleanup}")
                        cleanup_count += 1
                    except Exception as e:
                        print(f"⚠ Erro ao remover {file_path_to_cleanup}: {e}")
                
                # Remover arquivo WAV
                if wav_path_to_cleanup and os.path.exists(wav_path_to_cleanup):
                    try:
                        os.remove(wav_path_to_cleanup)
                        print(f"✓ Arquivo removido: {wav_path_to_cleanup}")
                        cleanup_count += 1
                    except Exception as e:
                        print(f"⚠ Erro ao remover {wav_path_to_cleanup}: {e}")
                
                print(f"✓ Limpeza concluída: {cleanup_count} arquivo(s) removido(s)")
        
        # Iniciar thread background
        thread = threading.Thread(target=process_audio_background, daemon=True)
        thread.start()
        
        # Retornar imediatamente com status processing
        return JSONResponse(
            status_code=202,
            content={
                "status": "processing",
                "message": "Arquivo enviado e processamento iniciado. Verifique /progress para atualizações."
            }
        )
        
    except Exception as e:
        print(f"Erro ao receber arquivo: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Erro ao processar arquivo: {str(e)}"}
        )

    except Exception as e:
        print(f"Erro durante transcrição: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Erro ao processar áudio: {str(e)}"}
        )

def save_transcription_file(transcription_text, audio_filename):
    """Salva a transcrição em um arquivo de texto"""
    try:
        # Criar nome do arquivo baseado no áudio original
        base_name = Path(audio_filename).stem
        txt_filename = f"{base_name}_transcricao.txt"
        txt_path = os.path.join(UPLOAD_DIR, txt_filename)
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"TRANSCRIÇÃO DE ÁUDIO\n")
            f.write(f"{'='*50}\n\n")
            f.write(f"Arquivo: {audio_filename}\n")
            f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"Modelo: Whisper (Offline)\n")
            f.write(f"Idioma: Português (Brasil)\n")
            f.write(f"\n{'='*50}\n\n")
            f.write(f"TRANSCRIÇÃO:\n\n")
            f.write(transcription_text)
            f.write(f"\n\n{'='*50}\n")
        
        print(f"✓ Arquivo de transcrição salvo: {txt_path}")
        return txt_path
    except Exception as e:
        print(f"⚠ Erro ao salvar arquivo de transcrição: {e}")
        return None

def transcribe_audio_with_whisper(wav_path):
    """Transcreve áudio usando Whisper (offline)"""
    
    try:
        print(f"Iniciando transcrição com Whisper (offline)...")
        print(f"Arquivo: {wav_path}")
        
        if not whisper_model:
            raise Exception("Modelo Whisper não foi carregado com sucesso!")
        
        print("Validando arquivo de áudio...")
        validate_audio_file(wav_path)
        
        with progress_tracker['lock']:
            progress_tracker['status'] = 'processing'
            progress_tracker['current_percent'] = 20
        
        print("Iniciando processamento com Whisper...")
        
        # O WAV já foi garantido correto pelo FFmpeg
        # Whisper pode processar o arquivo diretamente agora
        result = whisper_model.transcribe(
            wav_path,
            language='pt',
            verbose=False,
            fp16=False
        )
        
        print("✓ Transcrição concluída!")
        
        # Atualizar progresso durante os passos finais
        with progress_tracker['lock']:
            progress_tracker['current_percent'] = 90
        
        transcription_text = result.get('text', '').strip()
        
        if transcription_text:
            print(f"✓ Transcrição: '{transcription_text[:100]}...'")
        else:
            print("! Nenhuma transcrição gerada pelo Whisper")
            transcription_text = "[Áudio não contém fala reconhecível]"
        
        return transcription_text
        
    except Exception as e:
        print(f"✗ Erro na transcrição: {str(e)}")
        import traceback
        traceback.print_exc()
        with progress_tracker['lock']:
            progress_tracker['status'] = 'error'
            progress_tracker['current_percent'] = 0
        raise Exception(f"Erro ao transcrever áudio: {str(e)}")

@app.post("/reset-progress")
async def reset_progress():
    """Resetar o rastreador de progresso para uma nova transcrição"""
    with progress_tracker['lock']:
        progress_tracker['current_percent'] = 0
        progress_tracker['status'] = 'waiting'
        progress_tracker['result'] = None
        progress_tracker['error'] = None
    print("✓ Rastreador de progresso resetado")
    return {"status": "reset"}

@app.get("/progress")
async def get_progress():
    """Obter o progresso atual do processamento"""
    with progress_tracker['lock']:
        response = {
            "percent": progress_tracker['current_percent'],
            "status": progress_tracker['status'],
            "error": progress_tracker['error'],
            "result": None
        }
        
        # Se o resultado está pronto, incluí-lo na resposta
        if progress_tracker['status'] == 'completed' and progress_tracker['result']:
            response['result'] = progress_tracker['result']
            print(f"DEBUG: Retornando resultado - status: {progress_tracker['status']}, tem resultado: {progress_tracker['result'] is not None}")
    
    return response

@app.get("/download/{filename}")
async def download_transcription(filename: str):
    """Download do arquivo de transcrição"""
    try:
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        # Validar que o arquivo está no diretório de uploads (segurança)
        if not os.path.abspath(file_path).startswith(os.path.abspath(UPLOAD_DIR)):
            return JSONResponse(
                status_code=403,
                content={"error": "Acesso negado"}
            )
        
        if not os.path.exists(file_path):
            return JSONResponse(
                status_code=404,
                content={"error": "Arquivo não encontrado"}
            )
        
        from fastapi.responses import FileResponse
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='text/plain; charset=utf-8'
        )
    except Exception as e:
        print(f"Erro ao fazer download: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Erro ao fazer download: {str(e)}"}
        )

@app.get("/health")
async def health_check():
    """Verificar saúde da API"""
    return {
        "status": "healthy",
        "model": "Whisper (Offline)",
        "ready": whisper_model is not None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

