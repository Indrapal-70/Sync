import asyncio
import httpx
import time

async def spawn_workflow(client, i):
    try:
        response = await client.post(
            "http://localhost:8000/api/workflows",
            json={"name": f"Load Test {i}", "description": f"Calculate the {i}th Fibonacci number"}
        )
        workflow_id = response.json()["id"]
        
        await client.post(f"http://localhost:8000/api/workflows/{workflow_id}/execute", json={})
        return True
    except Exception as e:
        print(f"Error on {i}: {e}")
        return False

async def main():
    concurrency = 5  # 5 concurrent workflows = 5 simultaneous initial agents (coders)
    print(f"Starting {concurrency} workflows concurrently...")
    start_time = time.time()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [spawn_workflow(client, i) for i in range(concurrency)]
        results = await asyncio.gather(*tasks)
    
    success_count = sum(1 for r in results if r)
    print(f"Successfully spawned {success_count}/{concurrency} workflows in {time.time() - start_time:.2f}s")

if __name__ == "__main__":
    asyncio.run(main())
