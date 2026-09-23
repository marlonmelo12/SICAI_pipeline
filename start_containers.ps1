# start_containers.ps1
# Script de Inicialização da Plataforma SICAI em Containers (Docker Compose)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   SICAI - Inicializacao da Plataforma em Containers      " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Verifica se o Docker Desktop está em execução
Write-Host "==> Verificando status do Docker..." -ForegroundColor Yellow
docker info >$null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "O Docker nao esta em execucao. Por favor, inicie o Docker Desktop."
    exit 1
}

# 2. Inicializa os 8 microserviços
Write-Host "==> Subindo stack de servicos com Docker Compose..." -ForegroundColor Yellow
docker compose up -d --build

# 3. Aguarda inicialização básica
Write-Host "==> Aguardando servicos estabilizarem..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# 4. Baixa o modelo Qwen 2.5 7B no Ollama (com GPU)
Write-Host "==> Baixando modelo Qwen 2.5 7B Instruct no Ollama..." -ForegroundColor Yellow
docker exec -it sicai-ollama ollama pull qwen2.5:7b-instruct

# 5. Exibe os endpoints prontos para uso
Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "   Plataforma SICAI em Execucao com Sucesso!              " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host " - OpenSearch Dashboards (UI Forense): http://localhost:5601" -ForegroundColor White
Write-Host " - Apache Airflow (Orquestrador):       http://localhost:8080" -ForegroundColor White
Write-Host " - Garage S3 (Object Storage Lakehouse): http://localhost:3900" -ForegroundColor White
Write-Host " - Ollama Local LLM (com GPU CUDA):    http://localhost:11434" -ForegroundColor White
Write-Host " - PostgreSQL 16 (Catalogo de Metadados): localhost:5432" -ForegroundColor White
Write-Host " - Redpanda (Event Streaming Kafka):    localhost:9092" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Green
