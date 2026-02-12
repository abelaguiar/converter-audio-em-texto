# 🧪 Testes - Sistema de Transcrição de Áudio

Documentação para rodar e entender os testes do projeto.

## 📋 Estrutura de Testes

```
backend/
├── test_main.py         # Suite completa de testes
├── conftest.py          # Fixtures e configurações do pytest
└── requirements.txt     # Com dependências de teste
```

## 🚀 Como Rodar os Testes

### 1. Instalar Dependências

```bash
# Dentro do container
docker exec audio-transcriber pip install -r requirements.txt

# Ou localmente
pip install pytest pytest-cov pytest-asyncio httpx
```

### 2. Rodar Todos os Testes

```bash
# Dentro do container
docker exec audio-transcriber pytest backend/test_main.py -v

# Ou localmente
pytest backend/test_main.py -v
```

### 3. Rodar Testes Específicos

```bash
# Apenas testes de validação de áudio
pytest backend/test_main.py::TestAudioValidation -v

# Apenas testes de API
pytest backend/test_main.py::TestAPIHealth -v

# Apenas um teste
pytest backend/test_main.py::TestAudioValidation::test_validate_wav_file_success -v
```

### 4. Testes com Cobertura

```bash
# Rodar com relatório de cobertura
pytest backend/test_main.py --cov=backend --cov-report=html

# Visualizar relatório
open htmlcov/index.html  # macOS
# ou
firefox htmlcov/index.html  # Linux
```

### 5. Modo Watch (rodar testes ao salvar)

```bash
# Instalar pytest-watch
pip install pytest-watch

# Rodar em modo watch
ptw backend/test_main.py
```

## 📊 Categorias de Testes

### TestAudioValidation
Testa validação de arquivos de áudio

- ✅ `test_validate_wav_file_success` - Validar WAV válido
- ✅ `test_validate_mp3_file_success` - Validar MP3 válido
- ✅ `test_validate_empty_wav_file_fails` - Rejeitar WAV vazio
- ✅ `test_validate_nonexistent_file_fails` - Rejeitar arquivo inexistente

**Executar:**
```bash
pytest backend/test_main.py::TestAudioValidation -v
```

---

### TestAudioConversion
Testa conversão de áudio MP3 → WAV

- ✅ `test_wav_file_does_not_convert` - WAV não reconverte
- ✅ `test_convert_mp3_to_wav_success` - Converter MP3 para WAV

**Executar:**
```bash
pytest backend/test_main.py::TestAudioConversion -v
```

---

### TestAudioMetadata
Testa extração de metadados

- ✅ `test_extract_metadata_from_wav` - Extrair metadados WAV
- ✅ `test_extract_metadata_from_mp3` - Extrair metadados MP3
- ✅ `test_extract_metadata_with_invalid_path` - Falhar graciosamente

**Executar:**
```bash
pytest backend/test_main.py::TestAudioMetadata -v
```

---

### TestAPIHealth
Testa saúde e status da API

- ✅ `test_health_endpoint` - Endpoint /health
- ✅ `test_root_endpoint` - Endpoint /

**Executar:**
```bash
pytest backend/test_main.py::TestAPIHealth -v
```

---

### TestProgressTracker
Testa rastreamento de progresso

- ✅ `test_reset_progress_endpoint` - Reset de progresso
- ✅ `test_progress_endpoint` - Obter progresso

**Executar:**
```bash
pytest backend/test_main.py::TestProgressTracker -v
```

---

### TestTranscriptionEndpoint
Testa endpoint de transcrição

- ✅ `test_transcribe_unsupported_format` - Rejeitar formato inválido
- ✅ `test_transcribe_missing_file` - Rejeitar sem arquivo
- ✅ `test_transcribe_with_json_response` - Validar resposta JSON

**Executar:**
```bash
pytest backend/test_main.py::TestTranscriptionEndpoint -v
```

---

### TestDownloadEndpoint
Testa endpoint de download

- ✅ `test_download_nonexistent_file` - Arquivo inexistente
- ✅ `test_download_with_path_traversal_attempt` - Segurança (path traversal)
- ✅ `test_download_only_txt_files` - Apenas .txt permitidos

**Executar:**
```bash
pytest backend/test_main.py::TestDownloadEndpoint -v
```

---

### TestSaveTranscription
Testa salvamento de arquivos de transcrição

- ✅ `test_save_transcription_file` - Salvar arquivo .txt

**Executar:**
```bash
pytest backend/test_main.py::TestSaveTranscription -v
```

---

### TestErrorHandling
Testa tratamento de erros

- ✅ `test_handle_corrupted_audio_file` - Arquivo corrompido
- ✅ `test_handle_very_small_file` - Arquivo muito pequeno

**Executar:**
```bash
pytest backend/test_main.py::TestErrorHandling -v
```

---

### TestConcurrency
Testa processamento concorrente

- ✅ `test_multiple_progress_requests` - Requisições simultâneas

**Executar:**
```bash
pytest backend/test_main.py::TestConcurrency -v
```

---

### TestIntegration
Testes de integração completos

- ✅ `test_health_check_before_transcription` - Fluxo completo

**Executar:**
```bash
pytest backend/test_main.py::TestIntegration -v
```

## 🔧 Fixtures Disponíveis

### temp_upload_dir
Diretório temporário para uploads

```python
def test_example(temp_upload_dir):
    filepath = os.path.join(temp_upload_dir, "test.mp3")
```

### sample_mp3_file
Arquivo MP3 de teste (5 segundos)

```python
def test_example(sample_mp3_file):
    assert os.path.exists(sample_mp3_file)
```

### sample_wav_file
Arquivo WAV de teste (5 segundos, 16kHz, mono, PCM)

```python
def test_example(sample_wav_file):
    assert os.path.exists(sample_wav_file)
```

### invalid_file
Arquivo inválido (texto puro)

```python
def test_example(invalid_file):
    assert sample_mp3_file.endswith('.txt')
```

### empty_wav_file
Arquivo WAV vazio (0 frames)

```python
def test_example(empty_wav_file):
    assert os.path.exists(empty_wav_file)
```

### app_client
Cliente FastAPI para testes

```python
def test_example(app_client):
    response = app_client.get("/health")
    assert response.status_code == 200
```

## 📈 Cobertura de Testes

Visualizar cobertura de código:

```bash
# Gerar relatório
pytest backend/test_main.py --cov=backend --cov-report=term-missing

# Gerar HTML
pytest backend/test_main.py --cov=backend --cov-report=html
```

**Metas de cobertura:**
- Funções críticas: > 80%
- Validação: > 90%
- API endpoints: > 85%

## 🐳 Testes no Docker

### Rodar testes dentro do container

```bash
docker exec audio-transcriber pytest backend/test_main.py -v
```

### Rodar testes com output interativo

```bash
docker exec -it audio-transcriber pytest backend/test_main.py -v -s
```

### Rodar testes com cobertura

```bash
docker exec audio-transcriber pytest backend/test_main.py \
  --cov=backend \
  --cov-report=term-missing \
  --cov-report=html
```

### Copiar relatório HTML do container

```bash
docker cp audio-transcriber:/app/htmlcov ./coverage-report
```

## 🚨 Testes Falhando?

### Problema: FFmpeg não encontrado

**Solução:** FFmpeg deve estar instalado no container. Verifique:

```bash
docker exec audio-transcriber which ffmpeg
```

### Problema: Modelo Whisper não carregado

**Solução:** Aguarde a inicialização do container:

```bash
docker logs audio-transcriber | grep "Whisper pronto"
```

### Problema: Porta 8000 não disponível

**Solução:** Altere a porta no conftest.py:

```python
from os import environ
environ['API_PORT'] = '9000'
```

### Problema: Arquivo temporário não criado

**Solução:** Verificar permissões:

```bash
docker exec audio-transcriber ls -la /tmp
```

## 📝 Adicionar Novos Testes

### Template básico

```python
class TestNewFeature:
    """Documentação da classe de testes"""
    
    def test_new_functionality(self, fixture_name):
        """Testa nova funcionalidade"""
        # Arrange
        expected = "algo"
        
        # Act
        result = funcao_testada(expected)
        
        # Assert
        assert result == expected
```

### Usar mocks

```python
from unittest.mock import patch, MagicMock

@patch('backend.main.external_function')
def test_with_mock(self, mock_function):
    mock_function.return_value = "mocked"
    
    result = funcao_que_usa_external(mock_function)
    
    mock_function.assert_called_once()
```

## 🎯 CI/CD

### GitHub Actions

Adicione `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      
      - name: Install dependencies
        run: pip install -r backend/requirements.txt
      
      - name: Run tests
        run: pytest backend/test_main.py -v --cov=backend
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## 📚 Recursos

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

## ✅ Checklist para Testes

Antes de fazer commit:

- [ ] Todos os testes passam? `pytest -v`
- [ ] Cobertura > 80%? `pytest --cov`
- [ ] Sem avisos? `pytest -v --disable-warnings`
- [ ] Documentação atualizada? README.md
- [ ] Fixture necessária? Adicione a conftest.py

---

**Última atualização:** 12/02/2026  
**Status:** Sistema de testes completo e funcional ✅
