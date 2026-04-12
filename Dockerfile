# Usamos uma imagem oficial e leve do Python
FROM python:3.11-slim

# Impede que o Python grave arquivos .pyc e força o log no terminal
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Define o diretório de trabalho dentro do container
WORKDIR /app

# curl é necessário para o healthcheck do Docker Compose
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Instala o uv (o gerenciador de pacotes ultrarrápido)
RUN pip install uv

# Copia apenas os arquivos de dependência primeiro (para aproveitar o cache do Docker)
COPY pyproject.toml uv.lock ./

# Instala as dependências usando o uv 
# (O comando sync cria o ambiente e instala tudo ultra rápido)
RUN uv sync --frozen --no-cache

# Agora copia o restante do código do projeto
COPY . .

# Expõe a porta que o FastAPI vai usar
EXPOSE 8000

# Comando para iniciar o servidor em tempo real da Integra.ai
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]