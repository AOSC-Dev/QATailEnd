import dataclasses

import os
import subprocess
import tempfile
import datetime
import dulwich
import dulwich.repo
import dulwich.client
import dulwich.diff_tree
import dulwich.porcelain
import sys
import logging

logger = logging.getLogger()


@dataclasses.dataclass
class ABPackage:
    package_name: str
    package_dir: str
    # 秒
    last_commit_time: int = 0


# 获取当前是否为root用户
def is_root_user():
    return os.getuid() == 0


# 获取最新的GIT树
def fetch_tree(root_dir):
    subprocess.Popen(
        ["git", "fetch"],
        cwd=root_dir + "/" + 'TREE',
        stdout=sys.stdout,
        stderr=sys.stderr,
        text=True,
    ).wait()


# 重置仓库到最新状态
def reset_to_origin(root_dir):
    with dulwich.repo.Repo(root_dir + "/" + 'TREE') as repo:
        remote_ref = repo.refs[b'refs/remotes/origin/stable']
        if remote_ref is not None:
            dulwich.porcelain.reset(repo, mode='hard', treeish=remote_ref)


# 获取当前ciel内的架构名称
def get_root_arch(root_dir):
    arch_key = "Architecture"
    state_file = root_dir + "/" + '.ciel/container/dist/var/lib/apt/extended_states'
    with open(state_file, 'r') as f:
        while f.readable():
            line = f.readline().strip()
            if line.startswith(arch_key):
                return line[len(arch_key) + 2:]  # ": "
    return 'unknown'


def __split_to_package_dir(dir: str):
    return "/".join(dir.split("/")[:2])


# 获取当前ciel内的所有包
def get_all_package(root_dir, need_last_commit_time=False):
    tree_dir = root_dir + "/" + 'TREE'
    packages = []
    for group_dir in os.listdir(tree_dir):
        group_file_dir = tree_dir + "/" + group_dir
        if not os.path.isdir(group_file_dir):
            continue
        for package_dir in os.listdir(group_file_dir):
            package_file_dir = group_file_dir + "/" + package_dir
            if not os.path.isdir(package_file_dir):
                continue
            # test groupDir/packageDir/spec file
            if not os.path.isfile(package_file_dir + "/" + "spec"):
                continue
            packages.append(ABPackage(package_name=package_dir, package_dir=group_dir + '/' + package_dir))

    if not need_last_commit_time:
        return packages

    # 最后一次提交查询
    packages_index = {packages[i].package_dir: packages[i] for i in range(len(packages))}
    with dulwich.repo.Repo(tree_dir) as repo:
        _, last = repo.refs.follow(b"HEAD")
        walker = repo.get_walker(include=[last])
        limit_time = datetime.datetime(datetime.datetime.now().year - 1, 1, 1).timestamp()
        for entry in walker:
            commit = entry.commit
            if commit.commit_time < limit_time:
                break
            for change in entry.changes():
                if change.new is None:
                    continue
                package_dir = __split_to_package_dir(change.new.path.decode("utf-8"))
                if package_dir not in packages_index:
                    continue
                pack = packages_index[package_dir]
                if pack.last_commit_time != 0:
                    continue
                pack.last_commit_time = commit.commit_time
                logger.debug("Found Package:%s, last commit time:%s ", package_dir, commit.commit_time)
                del packages_index[package_dir]
            if len(packages_index) == 0:
                break
    return packages


# 构建
# 注意"返回信息"需要自己释放
def build(root_dir, inst, pack: ABPackage):
    fd, path = tempfile.mkstemp(suffix='.out', prefix="ciel-test-build-", dir=None)
    command = []
    if not is_root_user():
        command.append("sudo")
    command.extend(['ciel', 'build', '-i', inst, pack.package_name])
    out = open(fd, mode="wt+")
    process = subprocess.Popen(
        command,
        cwd=root_dir,
        stdout=out,
        stderr=out,
        text=True,
    )
    return {'file': path, 'out': out, 'process': process}
