#!/bin/bash

# Script de inicialização do Sistema RAG DSM FATEC Jacareí
# Autor: Manus AI
# Versão: 1.0.0

echo "🎓 Sistema RAG para o Curso DSM da FATEC Jacareí"
echo "=================================================="

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Por favor, instale Python 3.8+"
    exit 1
fi

echo "✅ Python encontrado: $(python3 --version)"

# Navegar para o diretório backend
cd backend

# Verificar se requirements.txt existe
if [ ! -f "requirements.txt" ]; then
    echo "❌ Arquivo requirements.txt não encontrado"
    exit 1
fi

# Instalar dependências
echo "📦 Instalando dependências..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Erro ao instalar dependências"
    exit 1
fi

echo "✅ Dependências instaladas com sucesso"

# Verificar se os arquivos de dados existem
echo "📄 Verificando arquivos de dados..."
if [ ! -f "../data/projeto_pedagogico_dsm.txt" ]; then
    echo "⚠️  Arquivo projeto_pedagogico_dsm.txt não encontrado"
fi

if [ ! -f "../data/ementa_dsm.txt" ]; then
    echo "⚠️  Arquivo ementa_dsm.txt não encontrado"
fi

if [ ! -f "../data/site_fatec_jacarei.txt" ]; then
    echo "⚠️  Arquivo site_fatec_jacarei.txt não encontrado"
fi

# Iniciar o servidor
echo "🚀 Iniciando servidor RAG..."
echo "📍 Interface Web: http://127.0.0.1:8000/frontend"
echo "📖 API Docs: http://127.0.0.1:8000/docs"
echo ""
echo "💡 Para carregar a base de conhecimento, execute em outro terminal:"
echo "   cd backend && python ingest_knowledge_base.py"
echo ""
echo "🛑 Para parar o servidor, pressione Ctrl+C"
echo ""

python app.py
