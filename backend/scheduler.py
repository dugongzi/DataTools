"""抖音监控调度进程入口。

独立于 Web 进程运行，避免 gunicorn 多 worker 重复执行定时任务：

    python -m backend.scheduler
"""
import logging
import os
import signal
import threading

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler

from backend.app import create_app
from backend.app.services.douyin_monitor import get_config, is_due, start_run

TICK_SECONDS = 60

logger = logging.getLogger('douyin.scheduler')


def tick(app):
    """每分钟检查一次配置，到点则启动一轮采集。"""
    with app.app_context():
        cfg = get_config()
        if not cfg.enabled:
            return
        if not is_due(cfg):
            return

        run, running = start_run(app, trigger_type='schedule')
        if run is None:
            logger.info('已有采集任务在运行（run_id=%s），跳过本轮', running.id)
        else:
            logger.info('已启动定时采集（run_id=%s）', run.id)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
    )

    app = create_app(os.getenv('FLASK_ENV', 'development'))
    stop_event = threading.Event()

    def shutdown(signum, _frame):
        logger.info('收到信号 %s，正在停止调度器…', signum)
        stop_event.set()

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    scheduler = BackgroundScheduler(
        timezone='Asia/Shanghai',
        executors={'default': ThreadPoolExecutor(4)},
    )
    scheduler.add_job(
        tick,
        'interval',
        seconds=TICK_SECONDS,
        args=[app],
        id='douyin-monitor-tick',
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    logger.info('抖音监控调度器已启动，tick 间隔 %s 秒', TICK_SECONDS)

    try:
        while not stop_event.wait(1):
            pass
    finally:
        scheduler.shutdown(wait=False)
        logger.info('调度器已停止')


if __name__ == '__main__':
    main()
