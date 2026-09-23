# scripts/init_garage.ps1
# Inicializa o layout de nós e cria os buckets da arquitetura SICAI no Garage S3 via PowerShell

Write-Host "==> Aguardando Garage S3 inicializar..." -ForegroundColor Cyan
do {
    Start-Sleep -Seconds 2
    $status = docker exec sicai-garage garage status 2>$null
} while (-not $status)

Write-Host "==> Obtendo ID do Nó do Garage..." -ForegroundColor Cyan
$nodeIdLine = ($status | Select-String -Pattern '^[a-f0-9]{64}').Line
$nodeId = ($nodeIdLine -split '\s+')[0]

if (-not $nodeId) {
    Write-Error "Não foi possível obter o Node ID do Garage."
    exit 1
}

Write-Host "==> Configurando Layout do Nó ($nodeId)..." -ForegroundColor Cyan
docker exec sicai-garage garage layout assign -z dc1 -c 10G $nodeId
docker exec sicai-garage garage layout apply --version 1

Write-Host "==> Criando Chaves de Acesso S3..." -ForegroundColor Cyan
docker exec sicai-garage garage key create sicai-key

Write-Host "==> Criando Buckets do Lakehouse Forense..." -ForegroundColor Cyan
docker exec sicai-garage garage bucket create sicai-bronze
docker exec sicai-garage garage bucket create sicai-lakehouse

Write-Host "==> Concedendo Permissões de Leitura/Escrita..." -ForegroundColor Cyan
docker exec sicai-garage garage bucket allow sicai-bronze --read --write --key sicai-key
docker exec sicai-garage garage bucket allow sicai-lakehouse --read --write --key sicai-key

Write-Host "==> [SUCESSO] Garage S3 inicializado e buckets 'sicai-bronze' e 'sicai-lakehouse' prontos!" -ForegroundColor Green
