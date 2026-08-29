import dataclasses

import pygit2
import os
import subprocess
import tempfile


@dataclasses.dataclass
class ABPackage:
    package_name: str
    package_dir: str


# 获取当前是否为root用户
def is_root_user():
    return os.getuid() == 0


# 获取最新的GIT树
def fetch_tree(root_dir):
    repo = pygit2.Repository(root_dir + "/" + 'TREE')
    repo.remotes["origin"].fetch()


# 重置仓库到最新状态
def reset_to_origin(root_dir):
    repo = pygit2.Repository(root_dir + "/" + 'TREE')
    status = repo.status()
    if len(status.keys()) > 0:
        remote_branch = repo.lookup_branch('origin/stable', pygit2.enums.BranchType.REMOTE)
        repo.reset(remote_branch.target, pygit2.enums.ResetMode.HARD)


# 获取当前ciel内的架构名称
def get_root_arch(root_dir):
    arch_key = "Architecture"
    state_file = root_dir + "/" + '.ciel/container/dist/var/lib/apt/extended_states'
    with open(state_file, 'r') as f:
        while f.readable():
            line = f.readline()
            if line.startswith(arch_key):
                return line[len(arch_key) + 2:]  # ": "
    return 'unknown'

# 获取当前ciel内的所有包
def get_all_package(root_dir):
    tree_dir = root_dir + "/" + "TREE"
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

