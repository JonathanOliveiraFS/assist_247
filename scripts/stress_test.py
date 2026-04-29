import asyncio
import httpx
import time

async def send_webhook(client, message_id):
    url = "http://localhost:8000/webhook"
    payload = {
        "event": "messages.upsert",
        "instance": "integra_ai",
        "data": {
            "key": {
                "remoteJid": f"551199999{message_id}@s.whatsapp.net",
                "fromMe": False,
                "id": f"STRESS_{message_id}"
            },
            "message": {
                "conversation": f"Teste de estresse mensagem {message_id}. O que é a Integra.ai?"
            }
        }
    }
    try:
        start = time.time()
        resp = await client.post(url, json=payload, timeout=5.0)
        end = time.time()
        print(f"Msg {message_id} -> Status: {resp.status_code} | Resposta: {resp.json()} | Tempo: {end-start:.3f}s")
    except Exception as e:
        print(f"Msg {message_id} -> Erro: {e}")

async def run_stress_test(total_messages=20):
    print(f"🔥 Iniciando Bombardeio de {total_messages} mensagens simultâneas...")
    async with httpx.AsyncClient() as client:
        tasks = [send_webhook(client, i) for i in range(total_messages)]
        await asyncio.gather(*tasks)
    print("\n🏁 Bombardeio concluído. Verifique os logs do Bot para ver o processamento em background.")

if __name__ == "__main__":
    asyncio.run(run_stress_test())
