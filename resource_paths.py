"""运行时数据文件定位：适配源码运行、PyInstaller 打包与 pip 安装。

数据文件（JSON / QSS）通过 pyproject 的 data-files 安装到环境根目录；
本模块按“源码目录 → PyInstaller _MEIPASS → sys.prefix”顺序查找，
保证 pip install 后 EntropyEngine / 桌面端仍能读到资源。
"""

import os
import sys


def _candidate_roots() -> list[str]:
    roots = [os.path.dirname(os.path.abspath(__file__))]
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        roots.append(meipass)
    roots.append(sys.prefix)
    unique: list[str] = []
    for root in roots:
        if root and root not in unique:
            unique.append(root)
    return unique


def find_data(*parts: str) -> str:
    """返回存在的资源文件路径；找不到时返回源码目录下的预期路径（保持可读报错）。"""
    rel = os.path.join(*parts)
    for root in _candidate_roots():
        candidate = os.path.join(root, rel)
        if os.path.isfile(candidate):
            return candidate
    return os.path.join(_candidate_roots()[0], rel)
