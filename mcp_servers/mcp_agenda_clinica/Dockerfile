FROM python:3.11.9-slim
WORKDIR /app

# Instala as dependências necessárias para o MCP
RUN pip install mcp asyncio pyairtable

# Copia o código do servidor para dentro do container
COPY server.py .

# O comando agora roda o Python, mantendo o container VIVO e ouvindo
CMD ["python", "server.py"]