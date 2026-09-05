"""Codeforces 难度阶梯 · 独立本地小程序

入口只保留应用启动；UI/逻辑已拆到 app/ 深模块：
- app.theme           视觉常量与 QSS
- app.state           本地进度
- app.dialogs         信息论微缩模块
- app.tier_page       档位知识树
- app.dissect_page    动态熵减拆题页
- app.teacher_consensus 教师共识数据层
- app.window          主窗口
"""

import os
import sys

from PySide6.QtWidgets import QApplication

from app.theme import APP_NAME, ORG_NAME, load_qss
from app.window import MainWindow


def main():
    QApplication.setOrganizationName(ORG_NAME)
    QApplication.setApplicationName(APP_NAME)
    app = QApplication(sys.argv)
    qss_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.qss")
    app.setStyleSheet(load_qss(qss_path))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
