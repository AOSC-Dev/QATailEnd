import conf.conf
import qa_service

import schedule
import time
import qa_process
import logging
import traceback
import sys
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s]-%(asctime)s: %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger()
logger.info("qate Start")

qaapiclient = qa_service.QAAPIClient(conf.conf.config.remote.qa, conf.conf.config.remote.token)

proc=qa_process.QAProcess(conf.conf.config, qaapiclient)
try:
    proc.package_list
except Exception as e:
    logger.error("{}", type(e), exc_info=e)


schedule.every(10).seconds.do(lambda: proc.execute())
logger.info("qate Init Finish.")

while True:
    schedule.run_pending()
    time.sleep(1)
