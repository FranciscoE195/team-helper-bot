# Deploy BPI RAG System no Render.com

## 🚀 Setup Rápido (15 minutos)

### 1. Preparar Conta Groq (API LLM Grátis)
```bash
# 1. Vai a https://console.groq.com
# 2. Cria conta (grátis)
# 3. Cria API Key em "API Keys"
# 4. Copia a key (começa com gsk_...)
```

**Limites Free Tier:**
- 30 requests/minuto
- 6,000 tokens/minuto
- Modelos rápidos: llama-3.1-70b, qwen2.5:7b, etc

### 2. Push Código para GitHub
```bash
# No teu projeto local
git add .
git commit -m "Add Render deployment config"
git push origin main
```

### 3. Deploy no Render

#### A. Criar PostgreSQL Database
1. Vai a https://dashboard.render.com
2. Click "New +" → "PostgreSQL"
3. Nome: `bpi-rag-db`
4. Database: `rag_db`
5. User: `rag_user`
6. Plan: **Free** (1GB storage)
7. Click "Create Database"
8. **Guarda o Internal Database URL** (precisas depois)

#### B. Criar Web Service
1. Click "New +" → "Web Service"
2. Connect ao teu GitHub repo
3. Configuração:
   - Name: `bpi-rag-api`
   - Runtime: **Python 3**
   - Branch: `main`
   - Build Command: `pip install -r requirements-render.txt`
   - Start Command: `uvicorn rag_system.main:app --host 0.0.0.0 --port $PORT`
   - Plan: **Free** (512MB RAM)

#### C. Configurar Environment Variables
No dashboard do web service, vai a "Environment":

```bash
GROQ_API_KEY=gsk_...  # A tua key do Groq
DATABASE_URL=postgresql://...  # Do PostgreSQL que criaste
TRANSFORMERS_CACHE=/opt/render/.cache/huggingface
HF_HOME=/opt/render/.cache/huggingface
CONFIG_FILE=config/config.render.yaml
```

#### D. Deploy
1. Click "Manual Deploy" → "Deploy latest commit"
2. Aguarda ~5-10 minutos (download de modelos)
3. URL final: `https://bpi-rag-api.onrender.com`

### 4. Inicializar Database
```bash
# No teu PC, conecta ao Render PostgreSQL
export DATABASE_URL="postgresql://rag_user:...@dpg-xxx.oregon-postgres.render.com/rag_db"

# Cria tabelas
python scripts/init_db.py

# Ingere documentos (se quiseres fazer upload da tua BD local)
# Opção 1: Dump local e restore no Render
pg_dump -U postgres -d rag_db > backup.sql
psql $DATABASE_URL < backup.sql

# Opção 2: Re-ingest via API
curl -X POST https://bpi-rag-api.onrender.com/webhook/ingest-all
```

### 5. Atualizar Frontend
Edita `frontend/index.html`:
```javascript
// Linha ~380
const API_URL = 'https://bpi-rag-api.onrender.com/api/query';
```

### 6. Testar
```bash
curl -X POST https://bpi-rag-api.onrender.com/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Como funciona o RTC?", "max_sources": 5}'
```

---

## 📊 Velocidade Esperada

Com Groq API (llama-3.1-70b):
- Embedding: ~2-3s (local SentenceTransformers)
- Reranking: ~3-4s (local BGE reranker)
- LLM: **3-5s** (Groq API - MUITO RÁPIDO!)
- **Total: 8-12 segundos** ✅

---

## 🔧 Troubleshooting

### Build falha - Out of Memory
Render free tier tem 512MB RAM. Se falhar:
```bash
# Opção 1: Reduz batch_size em config.render.yaml
batch_size: 4  # ou menor

# Opção 2: Usa modelos menores (já estamos a usar os menores viáveis)
```

### 503 Service Unavailable
Render free tier "dorme" após 15 minutos sem uso.
Primeiro request acorda o serviço (~30s delay).

Solução: Upgrade para Paid ($7/mês) ou usa cron job para keep-alive:
```bash
# Cron job (opcional)
*/10 * * * * curl https://bpi-rag-api.onrender.com/health
```

### Groq Rate Limit
Free tier: 30 req/min.
Se passar: aguarda 1 minuto ou upgrade Groq plan.

---

## 💰 Custos

**GRÁTIS (com limitações):**
- Render PostgreSQL: 1GB storage
- Render Web Service: 512MB RAM, dorme após 15min
- Groq API: 30 req/min, 6k tokens/min

**Upgrade recomendado para produção ($14/mês):**
- Render Starter Plan: $7/mês (sempre ligado, 512MB RAM)
- Render PostgreSQL: $7/mês (256MB RAM, sempre ligado)
- Groq API: Grátis (suficiente para uso moderado)

---

## 🎯 Next Steps

1. **Hospedar Frontend:** 
   - Netlify/Vercel (grátis)
   - Ou Render Static Site (grátis)
   - Update API_URL para o endpoint Render

2. **Melhorar Performance:**
   - Adiciona Redis cache (Render Redis free tier)
   - Cache embeddings de queries comuns

3. **Monitorização:**
   - Render tem logs built-in
   - Adiciona Sentry para error tracking (grátis tier)

---

## 📚 Recursos

- Render Dashboard: https://dashboard.render.com
- Groq Console: https://console.groq.com
- Groq Docs: https://console.groq.com/docs
- Render Docs: https://render.com/docs
