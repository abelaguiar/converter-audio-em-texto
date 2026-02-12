.PHONY: help test test-local test-docker test-cov test-watch test-unit test-api test-integration install install-test clean docker-build docker-up docker-down docker-logs

help:
	@echo "🎙️  Transcriptor de Áudio - Makefile"
	@echo ""
	@echo "Testes:"
	@echo "  make test              - Rodar todos os testes localmente"
	@echo "  make test-local        - Alias para 'make test'"
	@echo "  make test-docker       - Rodar testes dentro do container"
	@echo "  make test-cov          - Rodar testes com cobertura"
	@echo "  make test-watch        - Rodar testes em modo watch"
	@echo "  make test-unit         - Rodar apenas testes unitários"
	@echo "  make test-api          - Rodar apenas testes de API"
	@echo "  make test-integration  - Rodar apenas testes de integração"
	@echo ""
	@echo "Instalação:"
	@echo "  make install           - Instalar dependências localmente"
	@echo "  make install-test      - Instalar dependências de teste"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build      - Construir imagens Docker"
	@echo "  make docker-up         - Iniciar containers"
	@echo "  make docker-down       - Parar containers"
	@echo "  make docker-logs       - Ver logs dos containers"
	@echo ""
	@echo "Limpeza:"
	@echo "  make clean             - Remover arquivos temporários"
	@echo "  make clean-all         - Remover tudo (incluindo volumes Docker)"

# ==================
# TESTES LOCAIS
# ==================

test: install-test
	@echo "🧪 Rodando testes locais..."
	./.venv/bin/pytest tests/test_main.py -v

test-local: test

test-cov: install-test
	@echo "🧪 Rodando testes com cobertura..."
	./.venv/bin/pytest tests/test_main.py \
		--cov=backend \
		--cov-report=term-missing \
		--cov-report=html
	@echo "✅ Relatório gerado em: htmlcov/index.html"

test-watch: install-test
	@echo "🧪 Rodando testes em modo watch..."
	./.venv/bin/ptw tests/test_main.py

test-unit: install-test
	@echo "🧪 Rodando testes unitários..."
	./.venv/bin/pytest tests/test_main.py::TestAudioValidation -v
	./.venv/bin/pytest tests/test_main.py::TestAudioConversion -v
	./.venv/bin/pytest tests/test_main.py::TestAudioMetadata -v
	./.venv/bin/pytest tests/test_main.py::TestErrorHandling -v

test-api: install-test
	@echo "🧪 Rodando testes de API..."
	./.venv/bin/pytest tests/test_main.py::TestAPIHealth -v
	./.venv/bin/pytest tests/test_main.py::TestTranscriptionEndpoint -v
	./.venv/bin/pytest tests/test_main.py::TestDownloadEndpoint -v
	./.venv/bin/pytest tests/test_main.py::TestProgressTracker -v

test-integration: install-test
	@echo "🧪 Rodando testes de integração..."
	./.venv/bin/pytest tests/test_main.py::TestIntegration -v
	./.venv/bin/pytest tests/test_main.py::TestConcurrency -v

# ==================
# TESTES NO DOCKER
# ==================

test-docker:
	@echo "🧪 Rodando testes dentro do Docker..."
	docker exec audio-transcriber pytest tests/test_main.py -v

test-docker-cov:
	@echo "🧪 Rodando testes com cobertura no Docker..."
	docker exec audio-transcriber pytest tests/test_main.py \
		--cov=backend \
		--cov-report=term-missing \
		--cov-report=html

test-docker-watch:
	@echo "🧪 Rodando testes em modo watch no Docker..."
	docker exec -it audio-transcriber ptw tests/test_main.py

# ==================
# INSTALAÇÃO
# ==================

install: .venv
	@echo "📦 Instalando dependências..."
	./.venv/bin/python -m pip install -r backend/requirements.txt

.venv:
	@echo "🐍 Criando virtual environment..."
	python3 -m venv .venv

install-test: install
	@echo "📦 Instalando dependências de teste..."
	./.venv/bin/python -m pip install pytest pytest-cov pytest-asyncio httpx pytest-watch

install-docker:
	@echo "📦 Instalando dependências no Docker..."
	docker exec audio-transcriber python3 -m pip install -r /app/backend/requirements.txt

# ==================
# DOCKER
# ==================

docker-build:
	@echo "🐳 Construindo imagens Docker..."
	docker compose build

docker-up:
	@echo "🐳 Iniciando containers..."
	docker compose up -d
	@echo "✅ Containers iniciados"
	@echo "Frontend: http://localhost:8082"
	@echo "API: http://localhost:8000"

docker-down:
	@echo "🐳 Parando containers..."
	docker compose down

docker-logs:
	@echo "📋 Logs do backend..."
	docker logs -f audio-transcriber

docker-ps:
	@echo "🐳 Containers em execução..."
	docker compose ps

# ==================
# LIMPEZA
# ==================

clean:
	@echo "🧹 Limpando arquivos temporários..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	@echo "✅ Limpeza concluída"

clean-uploads:
	@echo "🧹 Limpando arquivos de upload..."
	docker exec audio-transcriber rm -rf /app/uploads/*
	@echo "✅ Uploads removidos"

clean-docker:
	@echo "🧹 Limpando containers e volumes..."
	docker compose down -v
	@echo "✅ Containers e volumes removidos"

clean-all: clean clean-docker
	@echo "✅ Limpeza completa concluída"

# ==================
# QUALIDADE DE CÓDIGO
# ==================

lint:
	@echo "🔍 Executando lint..."
	python3 -m pip install flake8
	flake8 backend/ --max-line-length=120

format:
	@echo "🔧 Formatando código..."
	python3 -m pip install black
	black backend/ --line-length=120

type-check:
	@echo "🔍 Type checking..."
	python3 -m pip install mypy
	mypy backend/ --ignore-missing-imports

# ==================
# DEV
# ==================

dev-setup: clean install-test
	@echo "✅ Ambiente de desenvolvimento configurado"

dev-test: test-cov
	@echo "✅ Testes de desenvolvimento completos"

# ==================
# CI/CD
# ==================

ci-test: install-test
	@echo "🔄 Rodando testes CI/CD..."
	./.venv/bin/pytest tests/test_main.py -v --cov=backend --cov-report=xml

ci-lint: install-test
	@echo "🔍 Executando lint CI/CD..."
	flake8 backend/ --max-line-length=120 --count --exit-zero

# ==================
# INFORMAÇÕES
# ==================

info:
	@echo "📊 Informações do projeto:"
	@echo "Python: $$(python --version)"
	@echo "Pytest: $$(pytest --version)"
	@echo "Docker: $$(docker --version)"
	@echo "Docker Compose: $$(docker compose version)"

env-info:
	@echo "🔧 Informações do ambiente:"
	@echo "Diretório atual: $$(pwd)"
	@echo "User: $$(whoami)"
	@echo "Espaço em disco: $$(df -h . | tail -1)"

# ==================
# DEFAULT
# ==================

.DEFAULT_GOAL := help
