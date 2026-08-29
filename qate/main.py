import conf.conf
import qa_service

import schedule
import time
import qa_process

qaapiclient = qa_service.QAAPIClient(conf.conf.config.remote.qa, conf.conf.config.remote.token)

proc=qa_process.QAProcess(conf.conf.config, qaapiclient)


schedule.every(10).seconds.do(lambda: proc.execute())
while True:
    schedule.run_pending()
    time.sleep(1)
