from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
import re
import os
import edge_tts
import uuid
import json
import traceback
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq

# Carregar variáveis de ambiente
load_dotenv()

# Definir diretório base do backend (onde main.py está localizado)
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
print(f"📂 Diretório do backend: {BACKEND_DIR}")

app = FastAPI()

# Ler chave do arquivo .env
GROQ_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_KEY:
    raise ValueError("A chave GROQ_API_KEY não foi encontrada no arquivo .env")

# Inicializar cliente Groq para Whisper (STT)
groq_client = Groq(api_key=GROQ_KEY)

# Configuração CORS (Permite acesso do Frontend local)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURAÇÃO RAG & IA ---
# Usando Groq para LLM (Geração Rápida) e Hugging Face para Embeddings (Online)
MODEL_NAME = "llama-3.3-70b-versatile"  # Modelo atualizado Groq
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"  # Modelo multilíngue profissional

print(f"🔄 Inicializando IA com Groq ({MODEL_NAME})...")

# 1. Carregar Manual Completo
MANUAL_FILE = "manual_cuidador.txt"

print(f"📚 Carregando manual completo: {MANUAL_FILE}")

# Cache do FAISS para evitar recalcular embeddings toda vez
CACHE_NAME = "manual_cuidador"
FAISS_CACHE_DIR = os.path.join(BACKEND_DIR, ".faiss_cache", CACHE_NAME)

embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL,
    model_kwargs={'device': 'cpu'},  # CPU é suficiente para embeddings
    encode_kwargs={'normalize_embeddings': True}  # Melhora qualidade
)
vectorstore = None

# Tentar carregar do cache
if os.path.exists(FAISS_CACHE_DIR):
    try:
        print("⚡ Carregando FAISS do cache (rápido)...")
        vectorstore = FAISS.load_local(FAISS_CACHE_DIR, embeddings, allow_dangerous_deserialization=True)
        print("✅ Cache carregado com sucesso!")
    except Exception as e:
        print(f"⚠️ Erro ao carregar cache: {e}. Recriando...")
        vectorstore = None

# Se não tem cache, criar novo
if vectorstore is None:
    print("🔄 Criando novo FAISS (pode demorar alguns segundos)...")
    loader = TextLoader(MANUAL_FILE)
    documents = loader.load()
    text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_documents(documents)
    
    # Criar Vector Store (FAISS)
    vectorstore = FAISS.from_documents(chunks, embeddings)
    
    # Salvar no cache para próxima vez
    try:
        os.makedirs(FAISS_CACHE_DIR, exist_ok=True)
        vectorstore.save_local(FAISS_CACHE_DIR)
        print("💾 Cache salvo para próxima inicialização!")
    except Exception as e:
        print(f"⚠️ Erro ao salvar cache: {e}")

retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# 3. Setup LLM e Prompt
llm = ChatGroq(model=MODEL_NAME, temperature=0.3, api_key=GROQ_KEY)

# Função para carregar histórico recente da conversa
def get_recent_history(limit=5):
    """Carrega as últimas N interações do histórico"""
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
            # Retornar apenas as últimas N interações
            recent = history[-limit:] if len(history) > limit else history
            return recent
    except Exception as e:
        print(f"⚠️ Erro ao carregar histórico: {e}")
    return []

# Prompt Otimizado com Histórico e Conhecimento Geral
template = """Você é um assistente especialista em cuidados com demência.

DIRETRIZES PRINCIPAIS:
1. SEJA SEMPRE DIRETO: Evite frases como "Entendo sua preocupação" ou "não há informações no contexto fornecido". Vá direto ao ponto com informações úteis.
2. USE CONHECIMENTO GERAL: Se o contexto abaixo não tiver a resposta completa, use seu conhecimento geral sobre cuidados geriátricos e demência para ajudar. NUNCA diga que não sabe - sempre forneça uma resposta útil.
3. MANTENHA CONTEXTO: Considere o histórico da conversa abaixo para evitar repetições e criar respostas adequadas ao que já foi discutido.
4. FORMATO: Use listas e tópicos sempre que possível para facilitar a leitura.
5. IMPORTANTE: NÃO inclua cabeçalhos como "Resposta Direta:", "Dicas:", "Informações:" ou similares. Responda diretamente, sem rótulos ou títulos.

Histórico da Conversa (últimas interações):
{history}

Contexto da Base de Conhecimento:
{context}

Pergunta Atual do Usuário: {question}

Responda diretamente, sem cabeçalhos ou rótulos:"""
prompt = ChatPromptTemplate.from_template(template)

# Criar chain que inclui histórico
def format_history(x):
    """Formata o histórico recente para o prompt"""
    recent_history = get_recent_history(limit=5)
    
    if recent_history:
        history_lines = []
        for entry in recent_history:
            history_lines.append(f"Usuário: {entry.get('user', '')}")
            history_lines.append(f"Assistente: {entry.get('assistant', '')}")
        return "\n".join(history_lines)
    return "Nenhuma conversa anterior."

# Chain com histórico
chain = (
    {
        "context": retriever,
        "history": RunnableLambda(format_history),
        "question": RunnablePassthrough()
    }
    | prompt
    | llm
    | StrOutputParser()
)

# --- GUARDRAILS (REGRAS RÍGIDAS) ---
FORBIDDEN_TERMS = [
    r"medica[cç][aã]o", r"rem[eé]dio", r"dose", r"posologia", 
    r"sangue", r"desmai", r"emerg[eê]ncia", r"samu", r"hospital"
]

def check_guardrails(text: str) -> bool:
    for pattern in FORBIDDEN_TERMS:
        if re.search(pattern, text, re.IGNORECASE):
            return False
    return True

def clean_text_for_tts(text: str) -> str:
    """Remove caracteres de markdown para leitura fluida"""
    text = re.sub(r'[*#\-]', '', text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def clean_response_text(text: str) -> str:
    """Remove cabeçalhos indesejados das respostas do LLM"""
    # Remover linhas que começam com "Resposta Direta:", "Dicas:", "Informações:", etc.
    lines = text.split('\n')
    cleaned_lines = []
    skip_next_empty = False
    
    for line in lines:
        line_stripped = line.strip()
        # Verificar se é um cabeçalho indesejado
        if re.match(r'^(Resposta Direta|Dicas|Informações|Orientações|Solução|Resposta):\s*$', line_stripped, re.IGNORECASE):
            skip_next_empty = True
            continue
        
        # Pular linha vazia após cabeçalho removido
        if skip_next_empty and line_stripped == '':
            skip_next_empty = False
            continue
        
        skip_next_empty = False
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines).strip()

# --- LOGS (HISTÓRICO) ---
LOG_FILE = "historico_conversas.json"

def log_conversation(user_msg, assistant_msg, is_safe):
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": user_msg,
        "assistant": assistant_msg,
        "safe": is_safe
    }
    
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        else:
            history = []
            
        history.append(entry)
        
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Erro ao salvar log: {e}")

# --- FUNÇÕES DE ÁUDIO ---
async def text_to_speech(text: str, gender: str = "female") -> str:
    """Gera áudio neural a partir do texto usando Edge-TTS"""
    clean_text = clean_text_for_tts(text)
    
    if gender == "male":
        voice = "pt-BR-AntonioNeural"
    else:
        voice = "pt-BR-FranciscaNeural"
        
    communicate = edge_tts.Communicate(clean_text, voice)
    filename = f"temp_{uuid.uuid4()}.mp3"
    # Salvar no diretório do backend
    filepath = os.path.join(BACKEND_DIR, filename)
    await communicate.save(filepath)
    
    # Aguardar um pouco e verificar se o arquivo foi salvo corretamente
    import asyncio
    await asyncio.sleep(0.1)  # Pequeno delay para garantir que o arquivo está escrito
    
    if not os.path.exists(filepath):
        raise Exception(f"Arquivo não foi salvo corretamente: {filepath}")
    
    file_size = os.path.getsize(filepath)
    print(f"💾 Arquivo salvo: {filename}")
    print(f"📁 Caminho completo: {filepath}")
    print(f"📊 Tamanho do arquivo: {file_size} bytes")
    print(f"✅ Arquivo existe após salvar: {os.path.exists(filepath)}")
    
    if file_size == 0:
        raise Exception(f"Arquivo está vazio: {filepath}")
    
    return filename  # Retornar apenas o nome do arquivo para a URL

async def speech_to_text(file_path: str) -> str:
    """Transcreve áudio usando Groq Whisper"""
    with open(file_path, "rb") as file:
        transcription = groq_client.audio.transcriptions.create(
            file=(file_path, file.read()),
            model="whisper-large-v3",
            language="pt"
        )
    return transcription.text

# --- API ---
class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_endpoint(
    message: str = Form(None)
):
    # 1. Validar Input (Apenas Texto - Áudio será implementado no futuro)
    if not message:
        raise HTTPException(status_code=400, detail="Envie uma mensagem de texto")
    
    user_msg = message

    print(f"📝 Input Usuário: {user_msg}")

    # 2. Validação de Segurança (Guardrails)
    print("🔒 Verificando Guardrails...")
    is_safe = check_guardrails(user_msg)
    final_response_text = ""

    if not is_safe:
        print("⚠️ Bloqueado por Guardrails")
        final_response_text = "⚠️ ALERTA DE SEGURANÇA: Não posso orientar sobre medicação ou emergências. Contate o médico imediatamente."
    else:
        # 3. RAG + Geração
        try:
            print("🧠 Chamando LLM (RAG)...")
            raw_response = chain.invoke(user_msg)
            # Limpar cabeçalhos indesejados da resposta
            final_response_text = clean_response_text(raw_response)
            print("✅ Resposta gerada com sucesso.")
        except Exception as e:
            error_msg = str(e)
            error_traceback = traceback.format_exc()
            print(f"❌ Erro na IA: {error_msg}")
            print(f"📋 Traceback completo:\n{error_traceback}")
            final_response_text = "Desculpe, tive um erro técnico ao processar sua solicitação."
            is_safe = False

    # Salvar Log
    log_conversation(user_msg, final_response_text, is_safe)

    # 4. Retornar Resposta (Apenas Texto - Áudio será implementado no futuro)
    response_data = {
        "text_response": final_response_text,
        "audio_url": None,  # Desabilitado temporariamente
        "is_safe": is_safe
    }
    
    print(f"📤 Resposta enviada (texto apenas)")
    return response_data

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    # Procurar o arquivo no diretório do backend
    path = os.path.join(BACKEND_DIR, filename)
    
    print(f"🔍 Buscando áudio: {filename}")
    print(f"📁 Diretório backend: {BACKEND_DIR}")
    print(f"📁 Caminho completo: {path}")
    print(f"✅ Arquivo existe: {os.path.exists(path)}")
    
    if os.path.exists(path):
        print(f"✅ Servindo arquivo: {path}")
        # Servir arquivo com headers CORS explícitos
        response = FileResponse(
            path, 
            media_type="audio/mpeg",
            filename=filename,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET",
                "Access-Control-Allow-Headers": "*",
            }
        )
        return response
    else:
        print(f"❌ Arquivo não encontrado: {path}")
        # Debug: listar arquivos MP3 no diretório backend
        if os.path.exists(BACKEND_DIR):
            mp3_files = [f for f in os.listdir(BACKEND_DIR) if f.endswith('.mp3')]
            print(f"📋 Arquivos MP3 no diretório backend ({BACKEND_DIR}): {mp3_files}")
        raise HTTPException(status_code=404, detail=f"Arquivo não encontrado: {filename}")

@app.get("/")
def read_root():
    return {"status": "online", "service": "Agente Cuidador POC"}

@app.get("/health")
def health_check():
    """Endpoint para verificar se o servidor está online"""
    return {
        "status": "online",
        "service": "Agente Cuidador POC",
        "timestamp": datetime.now().isoformat()
    }
