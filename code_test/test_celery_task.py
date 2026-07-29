"""
定义当前celery app当中所有的任务

"""
from code_test.test_celery_app import app



@app.task(name = "task_1", autoretry_for = (Exception,),retry_kwargs = {"max_retries":3})
def task_1(sleep_time:int, print_a:str):
    """
    celery的第一个task
    """
    import time
    print(f"当前需要睡{sleep_time}s")
    time.sleep(7)
    print(f"正在执行task_1这个任务，当前打印:{print_a}")




