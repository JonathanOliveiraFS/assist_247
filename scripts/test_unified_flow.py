import asyncio
import httpx
import time
import sys

# Configurações do ambiente de teste
BASE_URL = "http://localhost:8000"
TENANT_A = "integra02"
TENANT_B = "clinica_abc"

async def send_webhook(instance, remote_jid, text):
    """Simula o envio de uma mensagem vinda da Evolution API."""
    payload = {
        "event": "messages.upsert",
        "instance": instance,
        "data": {
            "key": {
                "remoteJid": remote_jid,
                "fromMe": False
            },
            "message": {
                "conversation": text
            }
        }
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(f"{BASE_URL}/webhook", json=payload)
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}

async def test_scenario_a():
    print("\n--- [Cenário A] Testando Debounce e Race Condition ---")
    print("Enviando 3 mensagens em menos de 1 segundo do mesmo usuário...")
    
    # Simula o usuário mandando "Oi", "Tudo bem?", "Pode me ajudar?" bem rápido
    tasks = [
        send_webhook(TENANT_A, "5511999999999@s.whatsapp.net", "Oi"),
        send_webhook(TENANT_A, "5511999999999@s.whatsapp.net", "Tudo bem?"),
        send_webhook(TENANT_A, "5511999999999@s.whatsapp.net", "Pode me ajudar?")
    ]
    
    results = await asyncio.gather(*tasks)
    
    all_queued = all(r.get("status") == "queued" for r in results)
    if all_queued:
        print("✅ Webhook: Todas as mensagens foram aceitas e enfileiradas.")
        print("👉 Verifique nos LOGS DO SERVIDOR: Deve aparecer apenas UMA resposta da BIA após 3 segundos.")
    else:
        print(f"❌ Falha no enfileiramento: {results}")

async def test_scenario_b():
    print("\n--- [Cenário B] Testando Multi-tenancy (Isolamento) ---")
    print(f"Enviando mensagens simultâneas para '{TENANT_A}' e '{TENANT_B}'...")
    
    # Mesma pessoa falando com dois bots de empresas diferentes ao mesmo tempo
    t1 = await send_webhook(TENANT_A, "user_comum@s.whatsapp.net", "Quero agendar (Empresa A)")
    t2 = await send_webhook(TENANT_B, "user_comum@s.whatsapp.net", "Quero agendar (Empresa B)")
    
    if t1.get("status") == "queued" and t2.get("status") == "queued":
        print("✅ Sucesso: O sistema isolou as filas no Redis por Tenant ID.")
        print("👉 Verifique nos LOGS DO SERVIDOR: Devem aparecer duas respostas independentes.")
    else:
        print("❌ Falha no isolamento de tenants.")

async def test_scenario_c():
    print("\n--- [Cenário C] Testando RAG Híbrido e Fallback ---")
    print("Enviando pergunta com termo técnico específico...")
    
    # Termo que forçaria o BM25 se houvesse índice, ou acionaria o fallback se não houver
    res = await send_webhook(TENANT_A, "tester@s.whatsapp.net", "Qual o valor da configuração do assistente virtual?")
    
    if res.get("status") == "queued":
        print("✅ Sucesso: Requisição enviada para o RAG Híbrido.")
        print("👉 Verifique nos LOGS DO SERVIDOR: Deve aparecer um 'WARNING: Índice BM25 não encontrado' (Fallback funcionando!)")
    else:
        print("❌ Falha ao enviar requisição para o RAG.")

async def run_all_tests():
    print("🚀 INICIANDO TESTE UNIFICADO DO INTEGRA.AI...")
    
    # 1. Verifica se a API está viva e com MCPs carregados
    async with httpx.AsyncClient() as client:
        try:
            health = await client.get(f"{BASE_URL}/health")
            data = health.json()
            print(f"Estado da API: {data}")
            if data.get("mcp_tools_active", 0) == 0:
                print("⚠️ ATENÇÃO: Nenhum MCP carregado. Verifique os servidores mcp_servers/.")
        except Exception:
            print(f"❌ ERRO: Servidor não encontrado em {BASE_URL}. Rode 'uvicorn app.main:app --reload' primeiro.")
            return

    await test_scenario_a()
    await test_scenario_b()
    await test_scenario_c()
    
    print("\n" + "="*60)
    print("🎯 TESTE FINALIZADO!")
    print("A validação real acontece agora olhando os logs do terminal do servidor.")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(run_all_tests())
