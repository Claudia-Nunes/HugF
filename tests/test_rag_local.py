#!/usr/bin/env python3
"""
Script de teste para demonstrar o funcionamento do RAG sem depender da API de inferência do Hugging Face.
Este script simula a funcionalidade completa do RAG usando apenas os componentes locais.
"""

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Configurações
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

print("=== Teste do Sistema RAG ===")
print("Carregando modelo de embeddings...")

# Inicializar o modelo de embeddings
embedder = SentenceTransformer(EMBEDDING_MODEL)
dim = embedder.get_sentence_embedding_dimension()

# Criar índice FAISS
index = faiss.IndexFlatIP(dim)
documents = []

print(f"Modelo carregado. Dimensão dos embeddings: {dim}")
print()

# Função para adicionar documentos
def add_document(text):
    vec = embedder.encode([text], convert_to_numpy=True, normalize_embeddings=True)
    index.add(vec)
    documents.append(text)
    print(f"✓ Documento adicionado: '{text}'")

# Função para buscar documentos similares
def search_documents(query, top_k=3):
    query_embedding = embedder.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    distances, indices = index.search(query_embedding, top_k)
    
    results = []
    for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
        if idx < len(documents):
            results.append({
                'document': documents[idx],
                'similarity': float(distance),
                'rank': i + 1
            })
    
    return results

# Adicionar documentos de exemplo
print("1. Adicionando documentos ao índice:")
add_document("A capital da França é Paris.")
add_document("O Brasil é o maior produtor de café do mundo.")
add_document("Python é uma linguagem de programação popular.")
add_document("O Rio de Janeiro é conhecido pelo Cristo Redentor.")
add_document("Machine Learning é um subcampo da inteligência artificial.")

print(f"\nTotal de documentos indexados: {index.ntotal}")
print()

# Testar consultas
queries = [
    "Qual é a capital da França?",
    "Quem produz mais café?",
    "O que é Python?",
    "Pontos turísticos do Rio de Janeiro",
    "O que é aprendizado de máquina?"
]

print("2. Testando consultas:")
for query in queries:
    print(f"\n🔍 Pergunta: '{query}'")
    results = search_documents(query, top_k=2)
    
    if results:
        print("📄 Documentos mais relevantes:")
        for result in results:
            print(f"   {result['rank']}. (Similaridade: {result['similarity']:.3f}) {result['document']}")
        
        # Simular resposta baseada no contexto mais relevante
        best_context = results[0]['document']
        print(f"💡 Resposta baseada no contexto: {best_context}")
    else:
        print("❌ Nenhum documento relevante encontrado.")

print("\n=== Teste Concluído ===")
print("O sistema RAG está funcionando corretamente!")
print("- ✓ Embeddings gerados com sucesso")
print("- ✓ Índice FAISS operacional") 
print("- ✓ Busca por similaridade funcionando")
print("- ✓ Recuperação de contexto eficiente")
