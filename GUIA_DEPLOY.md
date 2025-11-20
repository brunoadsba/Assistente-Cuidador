# 🚀 Guia de Deploy: POC Agente Cuidador

Este guia detalha o processo completo para fazer deploy da POC no **Render** (backend) e **Netlify** (frontend).

---

## 📋 Pré-requisitos

- Conta no [Render.com](https://render.com) (gratuita)
- Conta no [Netlify](https://netlify.com) (gratuita)
- Repositório Git (GitHub, GitLab ou Bitbucket)
- Chave API da Groq

---

## 🔧 Passo 1: Preparar o Repositório

### 1.1. Verificar arquivos importantes

Certifique-se de que estes arquivos estão no repositório:

```
poc-agente/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── manual_cuidador.txt
│   ├── render.yaml
│   └── .env (NÃO commitar - apenas local)
├── frontend/
│   ├── index.html
│   ├── _redirects
│   └── netlify.toml
└── .gitignore
```

### 1.2. Commit e Push

```bash
cd poc-agente
git add .
git commit -m "Preparar para deploy: remover funcionalidade de áudio temporariamente"
git push origin main  # ou sua branch principal
```

---

## 🖥️ Passo 2: Deploy do Backend no Render

### 2.1. Criar novo serviço Web

1. Acesse [Render Dashboard](https://dashboard.render.com)
2. Clique em **"New +"** → **"Web Service"**
3. Conecte seu repositório Git
4. Selecione o repositório `diario-cuidador` (ou o nome do seu repo)

### 2.2. Configurar o serviço

**Configurações básicas:**
- **Name:** `agente-cuidador-backend`
- **Region:** Escolha a mais próxima (ex: `Oregon (US West)`)
- **Branch:** `main` (ou sua branch principal)
- **Root Directory:** `poc-agente/backend`
- **Runtime:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

**Variáveis de Ambiente:**
- Clique em **"Environment Variables"**
- Adicione:
  - **Key:** `GROQ_API_KEY`
  - **Value:** Sua chave da Groq (cole aqui)

### 2.3. Deploy

1. Clique em **"Create Web Service"**
2. Aguarde o build (pode demorar 2-5 minutos)
3. Quando concluir, você verá uma URL como: `https://agente-cuidador-backend-xxxx.onrender.com`

### 2.4. Testar o backend

Abra no navegador:
- `https://seu-backend.onrender.com/health` → Deve retornar `{"status": "online", ...}`
- `https://seu-backend.onrender.com/` → Deve retornar `{"status": "online", "service": "Agente Cuidador POC"}`

**⚠️ IMPORTANTE:** Anote a URL do seu backend Render! Você precisará dela no próximo passo.

---

## 🌐 Passo 3: Deploy do Frontend no Netlify

### 3.1. Atualizar URL do backend no frontend

Antes de fazer deploy, atualize a URL do backend no arquivo `frontend/index.html`:

```javascript
// Linha ~307 (aproximadamente)
const BACKEND_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://seu-backend-render.onrender.com'; // ← SUBSTITUA pela URL real do Render
```

**Substitua `seu-backend-render.onrender.com` pela URL real do seu backend no Render.**

### 3.2. Commit a mudança

```bash
git add frontend/index.html
git commit -m "Atualizar URL do backend para produção"
git push origin main
```

### 3.3. Criar site no Netlify

1. Acesse [Netlify Dashboard](https://app.netlify.com)
2. Clique em **"Add new site"** → **"Import an existing project"**
3. Conecte seu repositório Git
4. Selecione o repositório

### 3.4. Configurar build

**Configurações:**
- **Base directory:** `poc-agente/frontend`
- **Build command:** (deixe vazio - não precisa build)
- **Publish directory:** `poc-agente/frontend` (ou apenas `.` se já estiver na pasta)

**⚠️ IMPORTANTE:** O Netlify precisa servir o arquivo `index.html` diretamente.

### 3.5. Deploy

1. Clique em **"Deploy site"**
2. Aguarde alguns segundos
3. Você receberá uma URL como: `https://random-name-12345.netlify.app`

### 3.6. Testar o frontend

1. Abra a URL do Netlify no navegador
2. Teste enviando uma mensagem de texto
3. Verifique se a resposta aparece corretamente

---

## 🔍 Passo 4: Verificações Finais

### 4.1. Verificar CORS

Se houver erros de CORS, verifique se o backend está permitindo a origem do Netlify:

No `backend/main.py`, linha ~33-39, o CORS já está configurado para `allow_origins=["*"]`, então deve funcionar.

### 4.2. Verificar logs

**Render (Backend):**
- Acesse o dashboard do Render
- Vá em **"Logs"** para ver os logs do servidor
- Procure por erros ou avisos

**Netlify (Frontend):**
- Acesse o dashboard do Netlify
- Vá em **"Deploys"** → Clique no deploy → **"Deploy log"**

### 4.3. Testar funcionalidades

- ✅ Enviar mensagem de texto
- ✅ Receber resposta do agente
- ✅ Histórico de conversas (LocalStorage)
- ✅ Modo Dark/Light
- ✅ Limpar histórico

---

## 🐛 Troubleshooting

### Erro: "Failed to fetch"

**Causa:** Frontend não consegue conectar ao backend.

**Solução:**
1. Verifique se a URL do backend está correta no `index.html`
2. Verifique se o backend está online no Render
3. Verifique os logs do Render para erros

### Erro: CORS

**Causa:** Backend bloqueando requisições do frontend.

**Solução:**
- O CORS já está configurado para `allow_origins=["*"]`
- Se persistir, adicione a URL do Netlify explicitamente no backend

### Backend não inicia

**Causa:** Erro no código ou dependências.

**Solução:**
1. Verifique os logs do Render
2. Teste localmente primeiro: `uvicorn main:app --reload`
3. Verifique se todas as dependências estão no `requirements.txt`

### Cache do FAISS não funciona

**Causa:** Cache pode não persistir entre deploys.

**Solução:**
- O cache será recriado automaticamente na primeira requisição
- Isso pode demorar alguns segundos na primeira vez

---

## 📝 Checklist Final

Antes de considerar o deploy completo, verifique:

- [ ] Backend está online no Render
- [ ] Frontend está online no Netlify
- [ ] URL do backend atualizada no `index.html`
- [ ] Teste de envio de mensagem funciona
- [ ] Resposta do agente aparece corretamente
- [ ] Histórico de conversas funciona
- [ ] Modo Dark/Light funciona
- [ ] Limpar histórico funciona

---

## 🎯 Próximos Passos (Futuro)

Após o deploy bem-sucedido, você pode implementar:

1. **Funcionalidade de Áudio:**
   - Input de áudio (gravação + transcrição)
   - Output de áudio (TTS com Edge-TTS)
   - Players de áudio estilo WhatsApp

2. **Melhorias:**
   - Autenticação de usuários
   - Banco de dados para histórico
   - Analytics e métricas

---

## 📞 Suporte

Se encontrar problemas:
1. Verifique os logs do Render e Netlify
2. Teste localmente primeiro
3. Verifique o console do navegador (F12)

---

**Boa sorte com o deploy! 🚀**

