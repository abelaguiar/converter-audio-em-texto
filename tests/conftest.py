"""
Configuração de fixtures para os testes
"""
import pytest
import tempfile
import os
from pathlib import Path
from pydub import AudioSegment
import wave


@pytest.fixture
def temp_upload_dir():
    """Cria um diretório temporário para uploads"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_mp3_file(temp_upload_dir):
    """Cria um arquivo MP3 de teste com 5 segundos"""
    mp3_path = os.path.join(temp_upload_dir, "test_audio.mp3")
    
    # Gerar tom de 1kHz por 5 segundos
    audio = AudioSegment.silent(duration=5000)  # 5000ms = 5s
    # Adicionar conteúdo de áudio mínimo para ter datos válidos
    audio = audio.apply_gain(0)  # Aplicar ganho para ter dados
    
    audio.export(mp3_path, format="mp3")
    return mp3_path


@pytest.fixture
def sample_wav_file(temp_upload_dir):
    """Cria um arquivo WAV de teste com 5 segundos"""
    wav_path = os.path.join(temp_upload_dir, "test_audio.wav")
    
    # Criar arquivo WAV PCM 16-bit 16kHz mono de 5 segundos
    sample_rate = 16000
    duration_seconds = 5
    frames = sample_rate * duration_seconds
    
    with wave.open(wav_path, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        # Gerar dados de áudio (silêncio)
        silence = b'\x00\x00' * frames
        wav_file.writeframes(silence)
    
    return wav_path


@pytest.fixture
def invalid_file(temp_upload_dir):
    """Cria um arquivo inválido para teste"""
    invalid_path = os.path.join(temp_upload_dir, "invalid.txt")
    with open(invalid_path, 'w') as f:
        f.write("Este é um arquivo de texto, não áudio")
    return invalid_path


@pytest.fixture
def empty_wav_file(temp_upload_dir):
    """Cria um arquivo WAV vazio (0 frames)"""
    wav_path = os.path.join(temp_upload_dir, "empty.wav")
    
    with wave.open(wav_path, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        # Não escrever nenhum frame
    
    return wav_path


@pytest.fixture
def app_client():
    """Cliente FastAPI para testes"""
    from fastapi.testclient import TestClient
    from backend.main import app
    
    return TestClient(app)
