"""Codeforces 难度阶梯 · 独立本地小程序

入口只保留应用启动；UI/逻辑已拆到 app/ 深模块：
- app.theme           视觉常量与 QSS
- app.state           本地进度
- app.tier_page       档位知识树 + 算法卡
- app.reflection      复盘记事本
- app.stats_page      成长统计
- app.window          主窗口
"""

import sys

from PySide6.QtWidgets import QApplication

from app.theme import APP_NAME, ORG_NAME, load_qss
from app.window import MainWindow
from resource_paths import find_data


def main():
    QApplication.setOrganizationName(ORG_NAME)
    QApplication.setApplicationName(APP_NAME)
    app = QApplication(sys.argv)
    qss_path = find_data("style.qss")
    app.setStyleSheet(load_qss(qss_path))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
