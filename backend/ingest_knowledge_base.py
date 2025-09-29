
"""
Script para carregar a base de conhecimento do curso DSM da FATEC Jacareí.
Processa e indexa os documentos oficiais no sistema RAG.

Autor: Manus AI
Versão: 1.0.0
"""

import requests
import re
import os

API_URL = "http://127.0.0.1:8000/ingest"

def chunk_text(text, max_chunk_size=512, min_chunk_size=100):
    """
    Divide o texto em chunks inteligentes baseados em parágrafos e seções.
    """
    # Limpar texto
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Dividir por seções principais
    sections = re.split(r'\n\s*\n|\.\s*\n', text)
    chunks = []
    
    current_chunk = ""
    for section in sections:
        section = section.strip()
        if len(section) < min_chunk_size:
            continue
            
        # Se adicionar esta seção não exceder o limite, adicione
        if len(current_chunk + section) <= max_chunk_size:
            current_chunk += section + "\n"
        else:
            # Salvar chunk atual se não estiver vazio
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = section + "\n"
    
    # Adicionar último chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks

def ingest_file(file_path, description=""):
    """
    Processa e ingere um arquivo na base de conhecimento.
    """
    print(f"\n📄 Processando: {description}")
    print(f"   Arquivo: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        chunks = chunk_text(content)
        print(f"   📊 {len(chunks)} chunks gerados")
        
        success_count = 0
        for i, chunk in enumerate(chunks):
            try:
                response = requests.post(API_URL, json={"text": chunk}, timeout=10)
                if response.status_code == 200:
                    success_count += 1
                    print(f"   ✅ Chunk {i+1}/{len(chunks)} indexado", end='\r')
                else:
                    print(f"\n   ❌ Erro no chunk {i+1}: {response.text}")
            except requests.exceptions.RequestException as e:
                print(f"\n   ❌ Erro de conexão no chunk {i+1}: {e}")
        
        print(f"\n   ✅ {success_count}/{len(chunks)} chunks indexados com sucesso")
        return success_count
        
    except FileNotFoundError:
        print(f"   ❌ Arquivo não encontrado: {file_path}")
        return 0
    except Exception as e:
        print(f"   ❌ Erro ao processar arquivo: {e}")
        return 0

def check_api_status():
    """
    Verifica se a API está online e funcionando.
    """
    try:
        response = requests.get("http://127.0.0.1:8000/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API online - {data.get('indexed_documents', 0)} documentos já indexados")
            return True
        else:
            print("❌ API respondeu com erro")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Não foi possível conectar à API")
        print("   Certifique-se de que o servidor está rodando: python app.py")
        return False
    except Exception as e:
        print(f"❌ Erro ao verificar API: {e}")
        return False

if __name__ == "__main__":
    print("🎓 Sistema RAG - Carregamento da Base de Conhecimento DSM")
    print("=" * 60)
    
    # Verificar se a API está online
    if not check_api_status():
        print("\n💡 Para iniciar a API, execute:")
        print("   cd backend && python app.py")
        exit(1)
    
    # Definir arquivos para ingestão
    data_dir = "../data"
    files_to_ingest = [
        {
            "path": os.path.join(data_dir, "projeto_pedagogico_dsm.txt"),
            "description": "Projeto Pedagógico do Curso DSM"
        },
        {
            "path": os.path.join(data_dir, "ementa_dsm.txt"),
            "description": "Ementa das Disciplinas do Curso DSM"
        },
        {
            "path": os.path.join(data_dir, "site_fatec_jacarei.txt"),
            "description": "Informações do Site Oficial FATEC Jacareí"
        }
    ]
    
    total_chunks = 0
    successful_files = 0
    
    print(f"\n📚 Iniciando ingestão de {len(files_to_ingest)} arquivos...")
    
    for file_info in files_to_ingest:
        chunks_added = ingest_file(file_info["path"], file_info["description"])
        total_chunks += chunks_added
        if chunks_added > 0:
            successful_files += 1
    
    print("\n" + "=" * 60)
    print("📊 RESUMO DA INGESTÃO")
    print(f"✅ Arquivos processados: {successful_files}/{len(files_to_ingest)}")
    print(f"📄 Total de chunks indexados: {total_chunks}")
    
    if total_chunks > 0:
        print("\n🎉 Base de conhecimento carregada com sucesso!")
        print("💬 Agora você pode fazer perguntas sobre o curso DSM da FATEC Jacareí")
        print("\n🌐 Acesse a interface web em: http://127.0.0.1:8000/frontend")
    else:
        print("\n⚠️  Nenhum documento foi indexado. Verifique os arquivos e tente novamente.")
    
    print("=" * 60)

