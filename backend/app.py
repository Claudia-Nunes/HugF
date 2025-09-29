"""
Sistema RAG para o Curso DSM da FATEC Jacareí
Retrieval-Augmented Generation especializado para responder dúvidas sobre o curso.

Autor: Manus AI
Versão: 1.0.0
Data: Setembro 2025
"""

import os
import re
from typing import List

import faiss
import numpy as np
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

# Carregar variáveis de ambiente
load_dotenv()

# --- Configurações --- #
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
HF_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")

# --- Modelos e Banco de Dados --- #
print("🚀 Iniciando Sistema RAG para DSM FATEC Jacareí...")
print("📚 Carregando modelo de embeddings...")
embedder = SentenceTransformer(EMBEDDING_MODEL)
dim = embedder.get_sentence_embedding_dimension()
index = faiss.IndexFlatIP(dim)
documents: List[str] = []
print("✅ Modelos e FAISS prontos!")

# --- API com FastAPI --- #
app = FastAPI(
    title="RAG DSM FATEC Jacareí",
    description="Sistema especializado para responder dúvidas sobre o Curso Superior de Tecnologia em Desenvolvimento de Software Multiplataforma da FATEC Jacareí",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Modelos de Dados --- #
class IngestRequest(BaseModel):
    text: str

class IngestResponse(BaseModel):
    status: str
    indexed_text: str
    total_documents: int

class AskRequest(BaseModel):
    question: str
    top_k: int = 5

class AskResponse(BaseModel):
    answer: str
    context: str
    confidence: float

class StatusResponse(BaseModel):
    status: str
    indexed_documents: int
    embedding_model: str
    system_info: str

# --- Função de Geração de Respostas --- #
def generate_contextual_answer(question: str, context: str) -> tuple[str, float]:
    """
    Gera uma resposta baseada no contexto usando análise semântica e regras.
    Retorna (resposta, confiança)
    """
    question_lower = question.lower()
    context_lower = context.lower()
    
    # Dicionário de padrões e respostas
    patterns = {
        # Objetivo do curso
        r'objetivo|finalidade|propósito.*curso': {
            'keywords': ['objetivo', 'formar', 'capacitar', 'profissional'],
            'response_template': "O curso de DSM tem como objetivo formar profissionais capazes de projetar, desenvolver e testar software para múltiplas plataformas, aplicações em Nuvem e Internet das Coisas.",
            'confidence': 0.9
        },
        
        # Perfil profissional
        r'perfil.*profissional|egresso': {
            'keywords': ['perfil', 'egresso', 'profissional'],
            'response_template': "O egresso do curso DSM é um profissional que projeta, desenvolve e testa software para múltiplas plataformas, aplicações em Nuvem e Internet das Coisas. Seleciona e aplica conceitos de programação, banco de dados, engenharia de software, segurança da informação e inteligência artificial.",
            'confidence': 0.9
        },
        
        # Competências
        r'competência|habilidade|aprende': {
            'keywords': ['competências', 'programação', 'banco de dados', 'inteligência artificial'],
            'response_template': "O curso desenvolve competências em: programação back-end e front-end, banco de dados, segurança da informação, inteligência artificial, desenvolvimento multiplataforma, metodologias ágeis, e análise de dados.",
            'confidence': 0.8
        },
        
        # Duração
        r'duração|tempo|semestre|ano': {
            'keywords': ['semestre', 'ano', 'duração'],
            'response_template': "O curso tem duração de 6 semestres (3 anos).",
            'confidence': 0.95
        },
        
        # Matriz curricular
        r'matriz|grade|disciplina|matéria': {
            'keywords': ['matriz', 'disciplina', 'curricular'],
            'response_template': "A matriz curricular inclui disciplinas de programação, banco de dados, engenharia de software, matemática, estatística, inteligência artificial, desenvolvimento web e mobile, segurança da informação e gestão de projetos.",
            'confidence': 0.8
        },
        
        # Informações da FATEC
        r'fatec|jacareí|endereço|contato|telefone': {
            'keywords': ['fatec', 'jacareí', 'endereço', 'telefone'],
            'response_template': "FATEC Jacareí - Faculdade de Tecnologia Prof. Francisco de Moura. Endereço: Av. Faria Lima, 155 - Jardim Santa Maria - Jacareí/SP - CEP: 12328-070. Telefone: (12) 3953-7926. Horário: Segunda a Sexta das 07h às 22h.",
            'confidence': 0.95
        },
        
        # Vestibular
        r'vestibular|ingresso|entrada|acesso': {
            'keywords': ['vestibular', 'ingresso', 'acesso'],
            'response_template': "O ingresso no curso é feito através do vestibular da FATEC. Consulte o site oficial para informações sobre datas, editais e processo seletivo.",
            'confidence': 0.8
        }
    }
    
    # Buscar padrão correspondente
    for pattern, info in patterns.items():
        if re.search(pattern, question_lower):
            # Verificar se as palavras-chave estão no contexto
            keyword_matches = sum(1 for keyword in info['keywords'] if keyword in context_lower)
            if keyword_matches > 0:
                confidence = info['confidence'] * (keyword_matches / len(info['keywords']))
                return info['response_template'], confidence
    
    # Resposta genérica baseada no contexto
    sentences = context.split('.')
    relevant_sentences = []
    
    question_words = set(question_lower.split())
    for sentence in sentences:
        sentence_words = set(sentence.lower().split())
        overlap = len(question_words.intersection(sentence_words))
        if overlap > 1 and len(sentence.strip()) > 20:
            relevant_sentences.append(sentence.strip())
    
    if relevant_sentences:
        response = '. '.join(relevant_sentences[:2]) + '.'
        confidence = min(0.7, len(relevant_sentences) * 0.2)
        return response, confidence
    
    # Resposta padrão
    return "Com base nas informações disponíveis sobre o curso DSM da FATEC Jacareí, não encontrei uma resposta específica para sua pergunta. Você pode reformular a pergunta ou consultar o site oficial da FATEC.", 0.3

# --- Endpoints da API --- #
@app.get("/", response_model=StatusResponse)
def get_status():
    """Endpoint para verificar o status do sistema."""
    return StatusResponse(
        status="online",
        indexed_documents=index.ntotal,
        embedding_model=EMBEDDING_MODEL,
        system_info="Sistema RAG especializado para o curso DSM da FATEC Jacareí"
    )

@app.post("/ingest", response_model=IngestResponse)
def ingest_document(item: IngestRequest):
    """Adiciona um documento ao índice vetorial."""
    try:
        # Gerar embedding normalizado
        vec = embedder.encode([item.text], convert_to_numpy=True, normalize_embeddings=True)
        
        # Adicionar ao índice FAISS
        index.add(vec)
        documents.append(item.text)
        
        return IngestResponse(
            status="success",
            indexed_text=item.text[:100] + "..." if len(item.text) > 100 else item.text,
            total_documents=index.ntotal
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao indexar documento: {str(e)}")

@app.post("/ask", response_model=AskResponse)
def ask_question(item: AskRequest):
    """Responde uma pergunta usando RAG."""
    if index.ntotal == 0:
        return AskResponse(
            answer="Nenhum documento foi indexado ainda. Por favor, carregue a base de conhecimento primeiro.",
            context="",
            confidence=0.0
        )
    
    try:
        # Gerar embedding da pergunta
        question_embedding = embedder.encode([item.question], convert_to_numpy=True, normalize_embeddings=True)
        
        # Buscar documentos similares
        distances, indices = index.search(question_embedding, min(item.top_k, index.ntotal))
        
        # Recuperar documentos relevantes
        retrieved_docs = [documents[i] for i in indices[0] if i < len(documents)]
        context = "\n---\n".join(retrieved_docs)
        
        # Gerar resposta
        answer, confidence = generate_contextual_answer(item.question, context)
        
        return AskResponse(
            answer=answer,
            context=context[:1000] + "..." if len(context) > 1000 else context,
            confidence=confidence
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar pergunta: {str(e)}")

@app.get("/health")
def health_check():
    """Endpoint de health check."""
    return {"status": "healthy", "service": "RAG DSM FATEC"}

# --- Servir Frontend --- #
@app.get("/frontend")
def serve_frontend():
    """Serve a interface web."""
    return FileResponse("../frontend/index.html")

# Montar arquivos estáticos
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

# --- Inicialização --- #
if __name__ == "__main__":
    import uvicorn
    print("\n🎓 Sistema RAG para DSM FATEC Jacareí")
    print("📍 Acesse o frontend em: http://127.0.0.1:8000/frontend")
    print("📖 Documentação da API: http://127.0.0.1:8000/docs")
    print("🔍 Status da API: http://127.0.0.1:8000/")
    print("\n🚀 Iniciando servidor...")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
