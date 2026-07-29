import sys
sys.path.insert(0, "/home/m1881/pycharm_projects/0226_DeepResearch/")
from code_test.test_celery_app import app

def my_producer():
    """
    测试执行异步后台任务
    """
    # 把这个任务，写到celery中间件
    app.send_task("task_1",args=(7, "abc"))

    print("当前 生产者 代码，继续执行，不被阻塞")


my_producer()