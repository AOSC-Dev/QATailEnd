import os
import random
from datetime import datetime, timezone
import time
from typing import List
from models.models import QARequestBuilds
from file_read_backwards import FileReadBackwards
import service.ciel_root
import logging

logger = logging.getLogger()


class QAProcess:
    def __init__(self, config, qaapiclient):
        self.config = config
        self.qaapiclient = qaapiclient
        self.arch = service.ciel_root.get_root_arch(self.ciel_path)
        logger.info("Ciel Root arch: %s", self.arch)

    @property
    def ciel_path(self):
        return self.config.ciel.path

    @property
    def weights_enable(self):
        return self.config.qata.weights.enable

    @property
    def inst(self):
        return self.config.ciel.instance

    @property
    def buildbot(self):
        return self.config.remote.buildbot

    # package_list懒加载+按需刷新
    package_last_fetch_timestamp = 0
    package_last_list: List[service.ciel_root.ABPackage]
    package_weights = []

    @property
    def package_list(self):
        # 格式 秒
        now = time.time()
        # 48小时以内不做fetch和reset
        if (now - (48 * 60 * 60)) > self.package_last_fetch_timestamp:
            self.package_last_fetch_timestamp = now
            service.ciel_root.fetch_tree(self.ciel_path)
            service.ciel_root.reset_to_origin(self.ciel_path)
            self.package_last_list = service.ciel_root.get_all_package(self.ciel_path, self.weights_enable)
            # if arch!=amd64 then remove "*+32"
            if self.arch != "amd64":
                self.package_last_list = [package for package in self.package_last_list
                                          if not package.package_name.endswith("+32")]
            self.__compute_package_weights(self.package_last_list)
        return self.package_last_list

    def __compute_package_weights(self, packages):
        # default weight
        self.package_weights = [1.0 for _ in packages]
        if not self.weights_enable:
            return
        min_commit_time = 0
        max_commit_time = 0
        for pack in packages:
            if pack.last_commit_time == 0:
                continue
            min_commit_time = pack.last_commit_time if min_commit_time == 0 else min(min_commit_time,
                                                                                     pack.last_commit_time)
            max_commit_time = max(max_commit_time, pack.last_commit_time)
        for pack_index in range(len(packages)):
            pack = packages[pack_index]
            if pack.last_commit_time == 0:
                # 当last_commit_time为0 说明读取失败或者最后一次更新时间"过旧"
                # 按照最大方式处理
                self.package_weights[pack_index] *= 2
            else:
                # 此处，为 提交越旧 最终权重越接近 *2，提交越新 最终权重越接近 *1
                self.package_weights[pack_index] *= ((max_commit_time - pack.last_commit_time) /
                                                     (max_commit_time - min_commit_time)) + 1

    def execute_build(self):
        package_list = self.package_list
        a_pack = random.choices(package_list, weights=self.package_weights, k=1)[0]
        logger.info("start build package %s", a_pack.package_name)
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
                        logger.info("ACBS Build Successful")
                        build_status = True
                        break
                    if 'Nothing to do after dependency resolution' in line:
                        logger.info("end build None")
                        return
                    if 'Build error' in line:
                        logger.warning("Build Error")
                        build_status = False
                        break
            build_status_n = False if build_status is None else build_status

            qa_request_builds = QARequestBuilds(package_name=a_pack.package_name,
                                                success=build_status_n,
                                                timestamp="{:.0f}".format(int(datetime.now(timezone.utc).timestamp() * 1000)),
                                                architecture=self.arch,
                                                buildbot=self.buildbot, failure_reason="")
            response = self.qaapiclient.add_build(qa_request_builds)
            if not build_status_n:
                self.qaapiclient.upload_log(response.id, context["file"])
        finally:
            if context["file"] is not None:
                os.remove(context["file"])

    def execute(self):
        try:
            self.execute_build()
        except Exception as e:
            logger.error("{}", type(e), exc_info=e)
