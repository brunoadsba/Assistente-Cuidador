# Erros Conhecidos e Pendências (POC Agente Cuidador)

## 1. Funcionalidade de Áudio 🔮 ADIADO PARA FUTURO
- **Descrição:** A funcionalidade completa de áudio (input e output) será implementada em uma versão futura.
- **Status:** 🔮 **ADIADO PARA FUTURO** - Removida temporariamente para simplificar o deploy inicial.
- **Motivo:** Foco no deploy da versão básica (texto apenas) no Render e Netlify.
- **Inclui:**
  - Input de áudio (gravação e transcrição)
  - Output de áudio (TTS com Edge-TTS)
  - Players de áudio estilo WhatsApp
- **Quando:** Será implementado após o deploy bem-sucedido da versão básica.

## 2. Segurança de API Key ✅ RESOLVIDO
- **Descrição:** A chave da Groq estava hardcoded no `main.py`.
- **Status:** ✅ **RESOLVIDO** - Chave movida para `.env` e código atualizado para ler via `os.getenv("GROQ_API_KEY")`.
- **Data de Resolução:** Hoje
- **Observação:** Garantir que `.env` esteja no `.gitignore` antes de fazer commit.

## 3. Deploy em Produção 🚀 EM ANDAMENTO
- **Backend (Render.com):** Configuração em andamento
- **Frontend (Netlify):** Configuração em andamento
- **Status:** Preparando arquivos de configuração e removendo dependências de áudio.