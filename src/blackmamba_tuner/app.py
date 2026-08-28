from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .ui import TunerWindow


ORGANIZATION_NAME = "BlackMamba RECORDS"
ORGANIZATION_DOMAIN = "blackmamba.records"
APPLICATION_NAME = "BlackMamba Tuner"


def main() -> int:
    app = QApplication(sys.argv)
    app.setOrganizationName(ORGANIZATION_NAME)
    app.setOrganizationDomain(ORGANIZATION_DOMAIN)
    app.setApplicationName(APPLICATION_NAME)

    window = TunerWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
