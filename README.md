# 🎙️ Transcriptor de Áudio - Sistema Completo de Transcrição

Um sistema robusto de transcrição de áudio offline em tempo real, utilizando **Whisper (OpenAI)** com suporte otimizado para português brasileiro. Interface moderna, processamento em background e downloads automáticos de transcrições.

## ✨ Características Principais

- ✅ **Transcrição Offline** - Não requer conexão com internet após inicialização
- ✅ **Suporte a Português** - Otimizado especificamente para português brasileiro
- ✅ **Múltiplos Formatos** - MP3, WAV, FLAC, M4A, OGG, WMA, AAC, etc.
- ✅ **Conversão Automática** - FFmpeg converte qualquer áudio para 16kHz mono PCM
- ✅ **Barra de Progresso Real** - Acompanhe cada etapa do processamento
- ✅ **Downloads Automáticos** - Gera arquivo .txt formatado com metadados
- ✅ **Limpeza Automática** - Remove arquivos após processamento (sucesso ou erro)
- ✅ **Interface Web Moderna** - UI responsiva com drag-drop de arquivos
- ✅ **API RESTful** - Backend robusto com FastAPI
- ✅ **100% Docker** - Deploy fácil com Docker Compose
- ✅ **Validação em Tempo Real** - Verifica arquivo antes/depois da conversão

## 📋 Requisitos

- Docker >= 20.10
- Docker Compose >= 1.29
- **Mínimo 4GB de RAM** (5-6GB recomendado para arquivos grandes)
- **Mínimo 2GB de espaço em disco** (1GB para modelo + uploads)
- Conexão com internet (apenas para primeira inicialização)

## 🚀 Início Rápido

### 1. Navegar para o diretório

```bash
cd /home/abel-aguiar/projects/work/converter
```

### 2. Iniciar os containers

```bash
docker compose up -d
```

### 3. Aguardar carregamento

```bash
docker logs audio-transcriber -f
# Aguarde a mensagem: "✓ Whisper pronto para usar!"
```

Pressione `Ctrl+C` para sair dos logs.

### 4. Acessar a interface

Abra no navegador: **http://localhost:8082**

## 📖 Como Usar

### Interface Web

#### 1️⃣ Upload de Arquivo

```
┌─────────────────────────────────┐
│   🎙️ Transcriptor de Áudio      │
│                                 │
│  ┌─────────────────────────────┐│
│  │ 📁 Clique ou arraste aqui  ││
│  │                             ││
│  │  Formatos: MP3, WAV, FLAC  ││
│  │  Tamanho máx: Testado até  ││
│  │  90MB                       ││
│  └─────────────────────────────┘│
└─────────────────────────────────┘
```

**Opções:**
- Clique no botão "Selecionar Arquivo"
- Ou arraste um arquivo para a caixa

#### 2️⃣ Acompanhar Progresso

A barra de progresso mostra:
- **0-20%** - Metadados + Validação
- **20-50%** - Conversão com FFmpeg (MP3 → WAV)
- **50-90%** - Transcrição com Whisper
- **90-100%** - Finalizando

#### 3️⃣ Visualizar Resultados

Após conclusão, você verá:

**📊 Metadados:**
- Arquivo
- Título / Artista
- Duração
- Formato original
- Tamanho

**📝 Transcrição:**
- Texto completo transcrito
- 100% copiável

**💾 Opções de Download:**
- `📋 Copiar Texto` - Copia para área de transferência
- `📄 Baixar Arquivo` - Download arquivo .txt com metadados

**🔄 Ações:**
- `🔄 Novo Arquivo` - Volta para upload

### Exemplos de Uso

#### Via Terminal (cURL)

```bash
# Fazer upload
curl -X POST -F "file=@audio.mp3" \
  http://localhost:8000/transcribe

# Verificar progresso
curl http://localhost:8000/progress | jq

# Fazer download do arquivo
curl http://localhost:8000/download/audio_transcricao.txt \
  -o minha_transcricao.txt
```

#### Verificar Saúde da API

```bash
curl http://localhost:8000/health | jq
```

Resposta esperada:
```json
{
  "status": "healthy",
  "model": "Whisper (Offline)",
  "ready": true
}
```

## 🏗️ Arquitetura

```
┌────────────────────────────────────────┐
│         FRONTEND (Nginx Port 8082)     │
│  - Interface web responsiva            │
│  - Upload drag-drop                    │
│  - Real-time progress polling          │
│  - Visualização de resultados          │
└──────────────────┬─────────────────────┘
                   │ HTTP REST API
                   ▼
┌────────────────────────────────────────┐
│    BACKEND (FastAPI Port 8000)         │
│  - Recepção de arquivos                │
│  - Conversão via FFmpeg                │
│  - Transcrição com Whisper             │
│  - Geração de arquivo .txt             │
│  - Limpeza automática de arquivos      │
└──────────────────┬─────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
   ┌─────────────┐    ┌──────────────┐
   │  FFmpeg     │    │   Whisper    │
   │  (Conversão)│    │ (Transcrição)│
   │ MP3→WAV     │    │    PT-BR     │
   │ 16kHz Mono  │    │  139MB Model │
   └─────────────┘    └──────────────┘
```

## 📁 Estrutura do Projeto

```
converter/
├── backend/
│   ├── main.py              # API FastAPI + lógica de processamento (465 linhas)
│   ├── requirements.txt      # Dependências Python
│   └── download_model.py     # Script para baixar modelo Whisper
├── frontend/
│   └── index.html            # Interface web (671 linhas, responsiva)
├── uploads/                  # Diretório de arquivos temporários (auto-limpável)
├── Dockerfile               # Imagem Python 3.11 + FFmpeg + Sistema
├── docker-compose.yml       # Orquestração: Frontend (Nginx) + Backend (FastAPI)
├── nginx.conf              # Configuração do servidor web
└── README.md               # Este arquivo
```

## 🔧 Endpoints da API

### POST `/transcribe`
Faz upload e inicia transcrição em background

**Request:**
```bash
curl -X POST -F "file=@audio.mp3" http://localhost:8000/transcribe
```

**Response:**
```json
{
  "status": "processing",
  "message": "Arquivo enviado e processamento iniciado. Verifique /progress para atualizações."
}
```

---

### GET `/progress`
Retorna progresso atual

**Response (durante processamento):**
```json
{
  "percent": 45,
  "status": "processing",
  "error": null,
  "result": null
}
```

**Response (concluído):**
```json
{
  "percent": 100,
  "status": "completed",
  "error": null,
  "result": {
    "status": "success",
    "transcription": "Olá, bem vindo ao transcriptor de áudio...",
    "metadata": {
      "filename": "audio.mp3",
      "duration": "1m 23s",
      "format": "MP3"
    },
    "download_file": "audio_transcricao.txt"
  }
}
```

---

### GET `/download/{filename}`
Baixa arquivo de transcrição

**Exemplo:**
```bash
curl http://localhost:8000/download/audio_transcricao.txt -o audio.txt
```

**Arquivo gerado (.txt):**
```
TRANSCRIÇÃO DE ÁUDIO
==================================================

Arquivo: audio.mp3
Data: 12/02/2026 16:30:45
Modelo: Whisper (Offline)
Idioma: Português (Brasil)

==================================================

TRANSCRIÇÃO:

Olá, bem vindo ao transcriptor de áudio...

==================================================
```

---

### POST `/reset-progress`
Reseta o rastreador para novo upload

```bash
curl -X POST http://localhost:8000/reset-progress
```

---

### GET `/health`
Status da API

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "model": "Whisper (Offline)",
  "ready": true
}
```

## ⚙️ Configuração

### Variáveis de Ambiente

No `docker-compose.yml`:
```yaml
environment:
  - PYTHONUNBUFFERED=1  # Output sem buffer
```

### Limites

| Parâmetro | Valor | Local |
|-----------|-------|-------|
| Timeout máximo | 40 minutos | `main.py` |
| Taxa de amostra | 16kHz | `main.py` (conversão FFmpeg) |
| Canais áudio | Mono | `main.py` (conversão FFmpeg) |
| Formatos aceitos | MP3, WAV, FLAC, M4A, OGG, WMA, AAC | `main.py` |
| Upload máximo | 500MB | `nginx.conf` (`client_max_body_size`) |

### Modificar Limites

**Aumentar timeout (em main.py):**
```python
timeout = 3600  # 1 hora em segundos
```

**Aumentar limite de upload (em nginx.conf):**
```nginx
client_max_body_size 1000M;  # Para 1GB
```

## 📊 Performance

### Tempos Típicos de Processamento

| Duração Áudio | Tempo Estimado | Recurso CPU |
|--------------|----------------|-----------|
| 30 segundos | 30-60 segundos | 1-2 cores |
| 1 minuto | 1-2 minutos | 2-3 cores |
| 5 minutos | 5-10 minutos | 3-4 cores |
| 10 minutos | 10-15 minutos | 4 cores |
| 30 minutos | 20-40 minutos | 4 cores |
| 1 hora | 45-90 minutos | 4 cores |
| 90 minutos | 60-120 minutos | 4 cores |

*Tempos variam conforme CPU disponível e qualidade do áudio*

### Requisitos de Memória

- **Idle**: ~500MB
- **Durante processamento**: 3-5GB (pico)
- **Modelo Whisper em RAM**: ~1.5GB

## 🐳 Docker Compose

### Containers Disponíveis

```yaml
audio-transcriber:
  - Porta: 8000 (API)
  - Serviço: FastAPI + Whisper + FFmpeg
  - Status: docker logs audio-transcriber

audio-transcriber-web:
  - Porta: 8082 (Frontend)
  - Serviço: Nginx
  - Status: docker logs audio-transcriber-web
```

### Comandos Úteis

**Iniciar:**
```bash
docker compose up -d
```

**Parar:**
```bash
docker compose down
```

**Reiniciar:**
```bash
docker compose restart
```

**Ver logs em tempo real:**
```bash
docker compose logs -f audio-transcriber
docker compose logs -f audio-transcriber-web
```

**Ver logs de uma data específica:**
```bash
docker compose logs --since 2026-02-12T10:00:00 audio-transcriber
```

**Limpar volumes (⚠️ Remove dados):**
```bash
docker compose down -v
```

**Reconstruir containers:**
```bash
docker compose up -d --build
```

## 🗑️ Limpeza Automática

O sistema remove automaticamente:
- ✅ Arquivo original após processamento (sucesso/erro)
- ✅ Arquivo WAV temporário conversão (sucesso/erro)
- ✅ Logs de operação mantidos

**Manual:** Para limpar uploads manualmente:
```bash
docker exec audio-transcriber rm -rf /app/uploads/*
```

**Verificar espaço:**
```bash
docker exec audio-transcriber du -sh /app/uploads/
```

## 🐛 Troubleshooting

### Container não inicia

**Verificar logs:**
```bash
docker compose logs audio-transcriber
```

**Solução:**
- Aguarde 10-15 segundos na primeira execução (modelo Whisper está carregando)
- Reinicie: `docker compose restart`
- Libere espaço em disco: ~2GB necessário

---

### Progresso travado em X%

**Causa:** Whisper está processando em background (isso é normal!)

**Solução:**
- Aguarde. Não feche a aba do navegador
- Para arquivos grandes, pode levar 30-90 minutos
- Verifique CPU: `docker stats`

---

### Erro "Connection refused"

**Causa:** Containers estão iniciando

**Solução:**
```bash
docker compose ps  # Verificar status
docker compose logs audio-transcriber  # Ver logs
docker compose up -d  # Reiniciar se necessário
```

---

### Arquivo muito grande (> 50MB)

**Causa:** Pode demorar bastante

**Solução:**
- Aumentar timeout em `main.py`
- Usar arquivo de áudio de qualidade menor
- Dividir áudio em partes menores

---

### Sem som / Transcrição vazia

**Causas possíveis:**
- Arquivo corrompido
- Áudio muito baixo
- Formato não suportado
- Idioma diferente de português

**Solução:**
```bash
# Testar com arquivo pequeno:
curl -X POST -F "file=@test.mp3" http://localhost:8000/transcribe
curl http://localhost:8000/progress | jq
```

---

### Erro FFmpeg

**Exemplo:** "ffmpeg: not found"

**Solução:**
```bash
docker compose down
docker compose up -d --build
```

## 📝 Arquivos de Log

**Logs da API:**
```bash
docker compose logs audio-transcriber > api.log
```

**Logs do Nginx:**
```bash
docker compose logs audio-transcriber-web > web.log
```

**Logs internos da conversão:**
Exibidos em tempo real via `/progress` endpoint

## 🔒 Segurança

- ✅ Arquivos validados por tipo MIME
- ✅ Nomes de arquivo sanitizados
- ✅ Uploads em diretório isolado (`/app/uploads`)
- ✅ Arquivos removidos automaticamente
- ✅ Sem persistência de dados sensíveis
- ⚠️ API sem autenticação (use em rede confiável ou adicione reverse proxy com autenticação)

## 📈 Melhorias Futuras

- [ ] Autenticação de usuários
- [ ] Histórico de transcrições
- [ ] Suporte a múltiplos idiomas com seleção
- [ ] Edição de transcrições na interface
- [ ] Timestamps de áudio na transcrição
- [ ] Exportação em PDF
- [ ] Busca em transcrições antigas
- [ ] Modelo Whisper "large" (maior precisão)
- [ ] API com rate limiting

## 🤝 Suporte

Se encontrar problemas:

1. **Verifique os logs:**
   ```bash
   docker compose logs audio-transcriber
   ```

2. **Teste a API:**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Tente com arquivo pequeno:**
   - Use arquivo < 5MB para testar

4. **Reinicie containers:**
   ```bash
   docker compose restart
   ```

5. **Libere memória:**
   ```bash
   docker system prune
   ```

## 📞 Informações Técnicas

- **Linguagem Backend:** Python 3.11
- **Framework Web:** FastAPI 0.104.1
- **Modelo IA:** Whisper (OpenAI) - Base
- **Conversão Áudio:** FFmpeg
- **Frontend:** HTML5 + CSS3 + JavaScript Vanilla
- **Servidor Web:** Nginx
- **Containerização:** Docker + Docker Compose

## 📄 Licença

MIT License - Veja LICENSE se disponível

## 🙏 Agradecimentos

- [OpenAI Whisper](https://github.com/openai/whisper) - Modelo de transcrição
- [FastAPI](https://fastapi.tiangolo.com/) - Framework web
- [FFmpeg](https://ffmpeg.org/) - Conversão de áudio
- [Nginx](https://nginx.org/) - Servidor web
- [Docker](https://www.docker.com/) - Containerização

---

**Versão:** 1.0.0 ✅ Produção  
**Última Atualização:** 12/02/2026  
**Status:** Sistema completo e funcional
