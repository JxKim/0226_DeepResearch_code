import asyncio

async def fetch_data(name, delay):
    print(f"{name}: 开始")
    await asyncio.sleep(delay)
    print(f"{name}: 结束")
    return name

async def demo_await():
    print("=== await 方式 ===")
    result = await fetch_data("A", 2)   # 开始执行 A，并等待 2 秒
    print("主协程拿到结果后继续")
    result = await fetch_data("B", 1)   # 等 A 完成才开始 B
    print("结束")

async def demo_create_task():
    print("=== create_task 方式 ===")
    task_a = asyncio.create_task(fetch_data("A", 2))
    task_b = asyncio.create_task(fetch_data("B", 1))
    print("两个任务已在后台运行，主协程继续")
    await asyncio.sleep(0.5)            # 主协程做其他事
    results = await asyncio.gather(task_a, task_b)  # 等待两者完成
    print("结束")

asyncio.run(demo_await())
asyncio.run(demo_create_task())