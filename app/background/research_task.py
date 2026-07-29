import asyncio
from app.celery_app import app
from app.schemas.router_schema import TaskType

def schedule_task(task:dict, *args):
    """
    调度任务执行，这个方法是一个非阻塞的调用。也就是说，task_id传过来只能够，该方法所做的事情，就是将任务投递到后台任务中执行就可以了
    task_id：当前任务的任务id
    *args: 当前任务，其他的参数

    当任务具体执行时，状态才改成running，执行成功，改成succeed,失败，改成failed
    """
    task_type = task["task_type"]
    project_id = task["project_id"]

    if task_type == TaskType.GENERATE_RESEARCH_BRIEF.value:
        # 所谓调度任务，就是将 任务，写到 celery 的中间件 redis当中，通过send_task来写
        app.send_task("generate_brief_and_outline", args=(project_id,))

    elif task_type  == TaskType.REVISE_OUTLINE.value:

        revision_instruction = args[0]
        app.send_task("revise_outline",args = (project_id, revision_instruction))


    elif task_type == TaskType.GENERATE_REPORT.value:

        user_instruction =  args[0]
        app.send_task("generate_report", args=(project_id, user_instruction))

    else:
        raise Exception(f"当前任务类型{task_type} 尚未定义")


_work_loop = None

def _get_worker_event_loop():
    """
    创建一个事件循环对象，
    后面通过该对象的run_until_complete() 方法，来执行协程。

    在Python当中，通过async def 所定义的，是一个异步方法,
    调用该异步方法(不带await)，得到的就是一个协程对象。

    所有的协程对象，都必须要在事件循环（event loop）去执行

    事件循环的作用：找到可以执行的协程，并执行它，直到这个协程，有新的异步操作了，event loop就会把该协程，重新放到事件循环，再先去执行其他的协程，直到所有的协程，全部都执行完毕

    该方法，在celery 任务消费者（也就是我们启动worker 进程）当中，创建一个全局的event_loop，供协程运行
    """

    global _work_loop

    if _work_loop is None:
        _work_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_work_loop)

    return _work_loop
    
def _run_async(coroutine):
    """
    将实际任务的协程对象，传递给_run_async方法，其会通过event_loop来执行 该协程，从而就能够实现在，在同步方法里面，去调用异步方法
    """

    loop = _get_worker_event_loop()

    loop.run_until_complete(coroutine)

# celery的app当中所包含的任务一： 项目初始化时，生成项目任务书的大纲的任务
@app.task(name = "generate_brief_and_outline")
def generate_brief_and_outline(project_id: str):
    """
    生成项目任务书的大纲的任务，接收的project_id
    """

    _run_async(_generate_brief_and_outline(project_id))

    


@app.task(name = "revise_outline")
def revise_outline(project_id:str, revision_instruction:str):
    """
    修订大纲的任务：
        project_id: 项目id
        revision_instruction: 用户传入的，大纲修订的意见
    """

    _run_async(_revise_outline(project_id=project_id,revision_instruction=revision_instruction))


@app.task(name = "generate_report")
def generate_report(project_id:str, user_instruction:str):
    """
    生成报告的任务：
        project_id: 项目id
        user_instruction：用户传入的，生成报告时的要求
    """

    _run_async(_generate_report(project_id, user_instruction))



async def _generate_brief_and_outline(project_id:str):
    """
    实际执行的任务
    """


async def _revise_outline(project_id:str,revision_instruction:str):
    """
    
    """

async def _generate_report(project_id:str, user_instruction:str):
    """
    
    """
