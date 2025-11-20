# Agente Cuidador (POC)

Prova de Conceito (POC) de um **Assistente Inteligente Híbrido** para apoiar cuidadores familiares de pessoas com demência.

A solução combina **RAG (Retrieval-Augmented Generation)** para protocolos médicos seguros, **Guardrails** para bloqueio de riscos e **LLM (Groq/Llama 3.3)** para empatia e contextualização.

---

## 🚀 Arquitetura Híbrida

1.  **Interface (Frontend):**
    *   Simulação de App Mobile (HTML/CSS/JS).
    *   Chat estilo WhatsApp com suporte a **Input de Voz** e **Resposta em Áudio (TTS)**.
    *   Input de texto auto-expansível e modo Dark/Light adaptativo.

2.  **Cérebro (Backend Python/FastAPI):**
    *   **RAG (Vector Search):** Consulta manual técnico validado (FAISS + Ollama Embeddings).
    *   **Guardrails (Segurança):** Regex para bloquear perguntas sobre medicação/emergência.
    *   **LLM (Groq):** Gera respostas naturais usando o modelo `llama-3.3-70b` (Ultra-rápido).

---

## 🛠️ Como Rodar

### 1. Pré-requisitos
*   Python 3.10+
*   [Ollama](https://ollama.com/) instalado localmente (para gerar embeddings).
*   Modelo de embedding: `ollama pull llama3`

### 2. Backend (API)
No terminal, entre na pasta `poc-agente/backend`:

```bash
# Instalar dependências
pip install -r requirements.txt

# Iniciar servidor
uvicorn main:app --reload
```
*Aguarde a mensagem: "Application startup complete".*

### 3. Frontend (App)
Abra o arquivo `poc-agente/frontend/index.html` diretamente no seu navegador (Chrome/Edge recomendados para suporte a voz).

---

## 🧪 Testes Sugeridos

| Tipo | Pergunta Exemplo | Resultado Esperado |
| :--- | :--- | :--- |
| **RAG (Protocolo)** | "Como dar banho no leito?" | Instruções técnicas baseadas no manual oficial. |
| **Segurança (Guardrail)** | "Qual a dose de Rivotril?" | ⚠️ Bloqueio imediato com alerta vermelho. |
| **Empatia (LLM Geral)** | "Me sinto culpada por estar cansada..." | Resposta acolhedora e psicológica (fora do manual). |

---

## 🔒 Privacidade e Segurança
*   O agente **não** inventa protocolos médicos (prioriza o manual).
*   Perguntas críticas (remédios, sangue, desmaio) são bloqueadas por regra rígida (código), não por IA.
