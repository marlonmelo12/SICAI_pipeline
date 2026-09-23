#!/usr/bin/env bash
# scripts/init_garage.sh
# Inicializa o layout de nós e cria os buckets da arquitetura SICAI no Garage S3

set -e

echo "==> Aguardando Garage S3 inicializar..."
until docker exec sicai-garage garage status > /dev/null 2>&1; do
    sleep 2
done

echo "==> Identificando ID do Nó do Garage..."
NODE_ID=$(docker exec sicai-garage garage status | grep -E "^[a-f0-9]{64}" | awk '{print $1}' | head -n 1)

if [ -z "$NODE_ID" ]; then
    echo "ERRO: Não foi possível obter o Node ID do Garage."
    exit 1
fi

echo "==> Configurando Layout do Nó ($NODE_ID)..."
docker exec sicai-garage garage layout assign -z dc1 -c 10G "$NODE_ID" || true
docker exec sicai-garage garage layout apply --version 1 || true

echo "==> Criando Chaves de Acesso S3..."
docker exec sicai-garage garage key create sicai-key || true

echo "==> Criando Buckets do Lakehouse Forense..."
docker exec sicai-garage garage bucket create sicai-bronze || true
docker exec sicai-garage garage bucket create sicai-lakehouse || true

echo "==> Concedendo Permissões de Leitura/Escrita..."
docker exec sicai-garage garage bucket allow sicai-bronze --read --write --key sicai-key || true
docker exec sicai-garage garage bucket allow sicai-lakehouse --read --write --key sicai-key || true

echo "==> [SUCESSO] Garage S3 inicializado e buckets 'sicai-bronze' e 'sicai-lakehouse' prontos!"
