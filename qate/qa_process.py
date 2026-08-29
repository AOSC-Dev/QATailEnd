import os
import random
from datetime import datetime
import time
from typing import List
from models.models import QARequestBuilds
from file_read_backwards import FileReadBackwards
import service.ciel_root


class QAProcess:
    def __init__(self, config, qaapiclient):
        self.config = config
        self.qaapiclient = qaapiclient

    @property
    def ciel_path(self):
        return self.config.ciel.path

    @property
    def inst(self):
        return self.config.ciel.instance

    @property
    def buildbot(self):
        return self.config.remote.buildbot

    # package_list懒加载+按需刷新
    package_last_fetch_timestamp = 0
    package_last_list: List[service.ciel_root.ABPackage]

    @property
    def package_list(self):
        # 格式 秒
        now = time.time()
        # 一小时以内不做fetch和reset
        if (now - (60 * 60)) > self.package_last_fetch_timestamp:
            self.package_last_fetch_timestamp = now
            service.ciel_root.fetch_tree(self.ciel_path)
            service.ciel_root.reset_to_origin(self.ciel_path)
            self.package_last_list = service.ciel_root.get_all_package(self.ciel_path)
        return self.package_last_list

    def execute_build(self):
        package_list = self.package_list
        index = random.randint(0, len(package_list) - 1)
        a_pack = package_list[index]
        print("start build package ", a_pack.package_name)
        context = service.ciel_root.build(self.ciel_path, self.inst, a_pack)
        try:
            # 等待结束
            context['process'].wait()
            # 关闭写入文件
            context["out"].close()
            build_status = None
            # 读取日志 分析
            with FileReadBackwards(context["file"]) as f:
                for line in f:
                    if 'ACBS Build Successful' in line:
                        print("ACBS Build Successful")
                        build_status = True
                        break
                    if 'Nothing to do after dependency resolution' in line:
                        print("end build None")
                        return
                    if 'Build error' in line:
                        print("Build Error")
                        build_status = False
                        break
            build_status_n = False if build_status is None else build_status

            qa_request_builds = QARequestBuilds(package_name=a_pack.package_name,
                                                success=build_status_n, timestamp=datetime.now(),
                                                architecture=service.ciel_root.get_root_arch(self.ciel_path),
                                                buildbot=self.buildbot, failure_reason="")
            response = self.qaapiclient.add_build(qa_request_builds)
            if not build_status_n:
                self.qaapiclient.upload_log(response.id, context["file"])
        finally:
            if context["file"] is not None:
                os.remove(context["file"])

    def execute(self):
        self.execute_build()
