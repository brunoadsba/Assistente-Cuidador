# 🚀 Guia de Deploy: POC Agente Cuidador (Fly.io + Netlify)

Este guia detalha o processo completo para fazer deploy da POC no **Fly.io** (backend) e **Netlify** (frontend).

---

## 📋 Pré-requisitos

- Conta no [Fly.io](https://fly.io) (gratuita, sem cartão necessário)
- Conta no [Netlify](https://netlify.com) (gratuita)
- Repositório Git (GitHub, GitLab ou Bitbucket)
- Chave API da Groq
- Fly CLI instalado (instruções abaixo)

---

## 🔧 Passo 1: Instalar Fly CLI

### Windows (PowerShell)
```powershell
iwr https://fly.io/install.ps1 -useb | iex
```

### macOS/Linux
```bash
curl -L https://fly.io/install.sh | sh
```

### Verificar instalação
```bash
fly version
```

---

## 🔧 Passo 2: Fazer Login no Fly.io

```bash
fly auth login
```

Isso abrirá o navegador para autenticação.

---

## 🖥️ Passo 3: Deploy do Backend no Fly.io

### 3.1. Navegar para a pasta do backend

```bash
cd poc-agente/backend
```

### 3.2. Criar aplicação no Fly.io

```bash
fly launch
```

**Durante o processo, você será perguntado:**
- **App name:** `agente-cuidador-backend` (ou escolha outro nome)
- **Region:** Escolha `gru` (São Paulo) ou outra região próxima
- **Postgres:** N (não precisamos)
- **Redis:** N (não precisamos)
- **Deploy now:** N (vamos configurar antes)

### 3.3. Configurar variáveis de ambiente

```bash
fly secrets set GROQ_API_KEY=sua_chave_aqui
```

**Substitua `sua_chave_aqui` pela sua chave real da Groq.**

### 3.4. Verificar configuração

O arquivo `fly.toml` já está criado. Verifique se está correto:

```bash
cat fly.toml
```

### 3.5. Fazer deploy

```bash
fly deploy
```

Aguarde o build e deploy (pode demorar 2-5 minutos).

### 3.6. Verificar se está funcionando

```bash
fly status
fly logs
```

Teste o endpoint:
```bash
fly open /health
```

Ou acesse no navegador: `https://agente-cuidador-backend.fly.dev/health`

**⚠️ IMPORTANTE:** Anote a URL do seu backend Fly.io! Você precisará dela no próximo passo.

A URL será algo como: `https://agente-cuidador-backend.fly.dev`

---

## 🌐 Passo 4: Deploy do Frontend no Netlify

### 4.1. Atualizar URL do backend no frontend

Antes de fazer deploy, atualize a URL do backend no arquivo `frontend/index.html`:

```javascript
// Linha ~307 (aproximadamente)
const BACKEND_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://agente-cuidador-backend.fly.dev'; // ← SUBSTITUA pela URL real do Fly.io
```

**Substitua `agente-cuidador-backend.fly.dev` pela URL real do seu backend no Fly.io.**

### 4.2. Commit a mudança

```bash
cd poc-agente
git add frontend/index.html
git commit -m "Atualizar URL do backend para Fly.io"
git push origin main
```

### 4.3. Criar site no Netlify

1. Acesse [Netlify Dashboard](https://app.netlify.com)
2. Clique em **"Add new site"** → **"Import an existing project"**
3. Conecte seu repositório Git
4. Selecione o repositório

### 4.4. Configurar build

**Configurações:**
- **Base directory:** `poc-agente/frontend`
- **Build command:** (deixe vazio - não precisa build)
- **Publish directory:** `poc-agente/frontend` (ou apenas `.` se já estiver na pasta)

### 4.5. Deploy

1. Clique em **"Deploy site"**
2. Aguarde alguns segundos
3. Você receberá uma URL como: `https://random-name-12345.netlify.app`

### 4.6. Testar o frontend

1. Abra a URL do Netlify no navegador
2. Teste enviando uma mensagem de texto
3. Verifique se a resposta aparece corretamente

---

## 🔍 Passo 5: Verificações Finais

### 5.1. Verificar CORS

O CORS já está configurado no backend para `allow_origins=["*"]`, então deve funcionar.

### 5.2. Verificar logs

**Fly.io (Backend):**
```bash
fly logs
```

**Netlify (Frontend):**
- Acesse o dashboard do Netlify
- Vá em **"Deploys"** → Clique no deploy → **"Deploy log"**

### 5.3. Testar funcionalidades

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
2. Verifique se o backend está online: `fly status`
3. Verifique os logs: `fly logs`

### Erro: CORS

**Causa:** Backend bloqueando requisições do frontend.

**Solução:**
- O CORS já está configurado para `allow_origins=["*"]`
- Se persistir, verifique os logs do Fly.io

### Backend não inicia

**Causa:** Erro no código ou dependências.

**Solução:**
1. Verifique os logs: `fly logs`
2. Teste localmente primeiro: `uvicorn main:app --reload`
3. Verifique se todas as dependências estão no `requirements.txt`

### Erro: "App not found"

**Causa:** Aplicação não foi criada ou nome incorreto.

**Solução:**
```bash
fly launch  # Cria a aplicação novamente
```

---

## 📝 Comandos Úteis do Fly.io

```bash
# Ver status da aplicação
fly status

# Ver logs em tempo real
fly logs

# Abrir aplicação no navegador
fly open

# Ver variáveis de ambiente
fly secrets list

# Adicionar variável de ambiente
fly secrets set NOME_VARIAVEL=valor

# Remover variável de ambiente
fly secrets unset NOME_VARIAVEL

# Reiniciar aplicação
fly apps restart agente-cuidador-backend

# Ver informações da aplicação
fly info
```

---

## 📝 Checklist Final

Antes de considerar o deploy completo, verifique:

- [ ] Backend está online no Fly.io (`fly status`)
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
1. Verifique os logs do Fly.io (`fly logs`)
2. Teste localmente primeiro
3. Verifique o console do navegador (F12)
4. Consulte a [documentação do Fly.io](https://fly.io/docs)

---

**Boa sorte com o deploy! 🚀**

