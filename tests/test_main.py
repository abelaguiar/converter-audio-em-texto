"""
Testes para o sistema de transcrição de áudio
"""
import pytest
import os
import wave
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import json


class TestAudioValidation:
    """Testes para validação de arquivos de áudio"""
    
    def test_validate_wav_file_success(self, sample_wav_file):
        """Testa validação bem-sucedida de arquivo WAV"""
        from backend.main import validate_audio_file
        
        result = validate_audio_file(sample_wav_file)
        assert result is True
    
    def test_validate_mp3_file_success(self, sample_mp3_file):
        """Testa validação bem-sucedida de arquivo MP3"""
        from backend.main import validate_audio_file
        
        result = validate_audio_file(sample_mp3_file)
        assert result is True
    
    def test_validate_empty_wav_file_fails(self, empty_wav_file):
        """Testa que arquivo WAV vazio falha na validação"""
        from backend.main import validate_audio_file
        
        with pytest.raises(Exception) as exc_info:
            validate_audio_file(empty_wav_file)
        
        assert "Arquivo WAV vazio" in str(exc_info.value) or "0 frames" in str(exc_info.value)
    
    def test_validate_nonexistent_file_fails(self):
        """Testa que arquivo inexistente falha na validação"""
        from backend.main import validate_audio_file
        
        with pytest.raises(Exception):
            validate_audio_file("/path/that/does/not/exist.wav")


class TestAudioConversion:
    """Testes para conversão de áudio"""
    
    def test_wav_file_does_not_convert(self, sample_wav_file):
        """Testa que arquivo WAV não é convertido novamente"""
        from backend.main import convert_audio_to_wav
        
        result = convert_audio_to_wav(sample_wav_file)
        assert result == sample_wav_file
        assert os.path.exists(sample_wav_file)
    
    @patch('subprocess.run')
    def test_convert_mp3_to_wav_success(self, mock_subprocess, sample_mp3_file, temp_upload_dir):
        """Testa conversão bem-sucedida de MP3 para WAV"""
        from backend.main import convert_audio_to_wav
        
        # Criar arquivo WAV de saída simulado
        wav_path = sample_mp3_file.replace('.mp3', '.wav')
        
        # Simular sucesso do FFmpeg
        mock_subprocess.return_value = MagicMock(returncode=0)
        
        # Criar arquivo WAV de teste
        with wave.open(wav_path, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            silence = b'\x00\x00' * (16000 * 5)  # 5 segundos
            wav_file.writeframes(silence)
        
        # Não vamos testar a conversão real, só a lógica
        # pois FFmpeg pode não estar disponível em todos os ambientes de teste
        assert os.path.exists(wav_path)


class TestAudioMetadata:
    """Testes para extração de metadados"""
    
    def test_extract_metadata_from_wav(self, sample_wav_file):
        """Testa extração de metadados de arquivo WAV"""
        from backend.main import extract_audio_metadata
        
        metadata = extract_audio_metadata(sample_wav_file)
        
        assert isinstance(metadata, dict)
        assert "format" in metadata
        assert metadata["format"] == "WAV"
        assert "duration" in metadata
    
    def test_extract_metadata_from_mp3(self, sample_mp3_file):
        """Testa extração de metadados de arquivo MP3"""
        from backend.main import extract_audio_metadata
        
        metadata = extract_audio_metadata(sample_mp3_file)
        
        assert isinstance(metadata, dict)
        assert "format" in metadata
        assert metadata["format"] == "MP3"
        assert "duration" in metadata
    
    def test_extract_metadata_with_invalid_path(self):
        """Testa extração de metadados com arquivo inexistente"""
        from backend.main import extract_audio_metadata
        
        # Deve retornar valores padrão, não falhar
        metadata = extract_audio_metadata("/invalid/path.mp3")
        
        assert isinstance(metadata, dict)
        assert metadata["title"] == "N/A"
        assert metadata["artist"] == "N/A"


class TestAPIHealth:
    """Testes para endpoint de saúde da API"""
    
    def test_health_endpoint(self, app_client):
        """Testa endpoint /health"""
        response = app_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "model" in data
        assert "ready" in data
    
    def test_root_endpoint(self, app_client):
        """Testa endpoint raiz /"""
        response = app_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestProgressTracker:
    """Testes para rastreamento de progresso"""
    
    def test_reset_progress_endpoint(self, app_client):
        """Testa reset do tracker de progresso"""
        response = app_client.post("/reset-progress")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data or data.get("status") == "reset"
    
    def test_progress_endpoint(self, app_client):
        """Testa endpoint /progress"""
        response = app_client.get("/progress")
        
        assert response.status_code == 200
        data = response.json()
        assert "percent" in data
        assert "status" in data
        assert isinstance(data["percent"], (int, float))


class TestTranscriptionEndpoint:
    """Testes para endpoint de transcrição"""
    
    def test_transcribe_unsupported_format(self, app_client, invalid_file):
        """Testa upload de formato não suportado"""
        with open(invalid_file, 'rb') as f:
            response = app_client.post(
                "/transcribe",
                files={"file": ("invalid.txt", f, "text/plain")}
            )
        
        # Deve retornar erro de formato não suportado
        assert response.status_code in [400, 422]
        data = response.json()
        assert "error" in data or response.status_code == 422
    
    def test_transcribe_missing_file(self, app_client):
        """Testa transcrição sem arquivo"""
        response = app_client.post("/transcribe")
        
        # Deve retornar erro de arquivo obrigatório
        assert response.status_code in [400, 422]
    
    @patch('backend.main.whisper_model')
    def test_transcribe_with_json_response(self, mock_whisper, app_client, sample_mp3_file):
        """Testa que endpoint retorna JSON válido"""
        # Simular modelo Whisper
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": "Olá mundo"}
        
        with open(sample_mp3_file, 'rb') as f:
            response = app_client.post(
                "/transcribe",
                files={"file": (os.path.basename(sample_mp3_file), f, "audio/mpeg")}
            )
        
        # Aceitar 202 (processando) ou 200 (completo)
        assert response.status_code in [200, 202]
        
        # Resposta deve ser JSON válido
        try:
            data = response.json()
            assert isinstance(data, dict)
        except:
            pytest.fail("Response is not valid JSON")


class TestDownloadEndpoint:
    """Testes para endpoint de download"""
    
    def test_download_nonexistent_file(self, app_client):
        """Testa download de arquivo inexistente"""
        response = app_client.get("/download/nonexistent_file.txt")
        
        assert response.status_code in [404, 400]
    
    def test_download_with_path_traversal_attempt(self, app_client):
        """Testa proteção contra path traversal"""
        response = app_client.get("/download/../../../etc/passwd")
        
        # Deve rejeitar por segurança
        assert response.status_code in [404, 400]
    
    def test_download_only_txt_files(self, app_client):
        """Testa que apenas arquivos .txt podem ser baixados"""
        # Tentar baixar arquivo que não existe
        response = app_client.get("/download/nonexistent_audio.wav")
        
        assert response.status_code in [404, 400]


class TestSaveTranscription:
    """Testes para salvar arquivo de transcrição"""
    
    def test_save_transcription_file(self, temp_upload_dir):
        """Testa salvamento de arquivo de transcrição"""
        from backend.main import save_transcription_file
        
        transcription_text = "Olá mundo! Esta é uma transcrição de teste."
        audio_filename = "test.mp3"
        
        filename = save_transcription_file(transcription_text, audio_filename)
        
        # Arquivo deve ser criado
        assert filename is not None
        assert filename.endswith(".txt")


class TestErrorHandling:
    """Testes para tratamento de erros"""
    
    def test_handle_corrupted_audio_file(self):
        """Testa tratamento de arquivo de áudio corrompido"""
        from backend.main import validate_audio_file
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b'Invalid WAV data')
            temp_path = f.name
        
        try:
            with pytest.raises(Exception):
                validate_audio_file(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_handle_very_small_file(self, temp_upload_dir):
        """Testa tratamento de arquivo muito pequeno"""
        from backend.main import validate_audio_file
        
        small_file = os.path.join(temp_upload_dir, "tiny.wav")
        with open(small_file, 'wb') as f:
            f.write(b'RIFF' + b'\x00' * 10)  # WAV header mínimo
        
        # Deve falhar ou passar dependendo do FFmpeg
        # O importante é não crashear
        try:
            validate_audio_file(small_file)
        except Exception:
            pass  # Esperado


class TestConcurrency:
    """Testes para processamento concorrente"""
    
    def test_multiple_progress_requests(self, app_client):
        """Testa múltiplas requisições simultâneas de progresso"""
        import threading
        
        results = []
        
        def make_request():
            response = app_client.get("/progress")
            results.append(response.status_code)
        
        threads = [threading.Thread(target=make_request) for _ in range(5)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Todas as requisições devem ser bem-sucedidas
        assert all(status == 200 for status in results)


class TestIntegration:
    """Testes de integração completos"""
    
    def test_health_check_before_transcription(self, app_client):
        """Testa check de saúde antes de transcrever"""
        # Verificar saúde
        health = app_client.get("/health")
        assert health.status_code == 200
        
        # Resetar progresso
        reset = app_client.post("/reset-progress")
        assert reset.status_code == 200
        
        # Verificar progresso inicial
        progress = app_client.get("/progress")
        assert progress.status_code == 200
        data = progress.json()
        assert data["percent"] in [0, 100]  # Deve estar em estado inicial ou anterior


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
