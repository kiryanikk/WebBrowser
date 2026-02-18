import sys
from PyQt6.QtCore import QUrl, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QToolBar, QPushButton,
    QLineEdit, QWidget, QVBoxLayout, QListWidget
)
from PyQt6.QtWebEngineWidgets import QWebEngineView


class MainWindow(QMainWindow):
    HOME_URL = "http://www.google.com"

    def __init__(self):
        super().__init__()
        self.history = []

        # ---- Tabs ----
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)  # крестики на вкладках
        self.tabs.tabCloseRequested.connect(self.close_tab_by_index)
        self.tabs.currentChanged.connect(self.on_current_tab_changed)
        self.setCentralWidget(self.tabs)

        # ---- Toolbar ----
        self.navbar = QToolBar()
        self.addToolBar(self.navbar)

        # ---- Buttons ----
        back_btn = QPushButton()
        back_btn.setIcon(QIcon("img/back.png"))
        back_btn.setIconSize(QSize(24, 24))
        back_btn.clicked.connect(self.go_back)
        self.navbar.addWidget(back_btn)

        forward_btn = QPushButton()
        forward_btn.setIcon(QIcon("img/forward.png"))
        forward_btn.setIconSize(QSize(24, 24))
        forward_btn.clicked.connect(self.go_forward)
        self.navbar.addWidget(forward_btn)

        reload_btn = QPushButton()
        reload_btn.setIcon(QIcon("img/reload.png"))
        reload_btn.setIconSize(QSize(24, 24))
        reload_btn.clicked.connect(self.reload_page)
        self.navbar.addWidget(reload_btn)

        home_btn = QPushButton()
        home_btn.setIcon(QIcon("img/home.png"))
        home_btn.setIconSize(QSize(24, 24))
        home_btn.clicked.connect(self.go_home)
        self.navbar.addWidget(home_btn)

        # ---- URL bar ----
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.navbar.addWidget(self.url_bar)

        # ---- New tab / Close tab / History ----
        newTab_btn = QPushButton("Новая вкладка")
        newTab_btn.clicked.connect(self.open_new_tab)
        self.navbar.addWidget(newTab_btn)

        history_btn = QPushButton("История")
        history_btn.clicked.connect(self.show_history)
        self.navbar.addWidget(history_btn)

        # ---- Styles (оставил твои) ----
        btn_style = """
            QPushButton {
                border-radius: 5px;
                background-color: #A9CCE3;
                color: white;
                font-size: 12px;
                padding: 5px;
                margin-right: 5px;
            }
            QPushButton:hover {
                background-color: #B0E0E6;
            }
        """
        back_btn.setStyleSheet(btn_style)
        forward_btn.setStyleSheet(btn_style)
        home_btn.setStyleSheet(btn_style)
        reload_btn.setStyleSheet(btn_style)

        newTab_btn.setStyleSheet("""
            QPushButton {
                border-radius: 5px;
                background-color: #A9CCE3;
                color: white;
                font-size: 12px;
                padding: 8px;
                margin-right: 5px;
                margin-left: 5px;
            }
        """)

        history_btn.setStyleSheet("""
            QPushButton {
                border-radius: 5px;
                background-color: #A9CCE3;
                color: white;
                font-size: 12px;
                padding: 8px;
                margin-right: 5px;
            }
        """)

        self.url_bar.setStyleSheet("""
            QLineEdit {
                background-color: #A9CCE3;
                border: 2px solid #A9CCE3;
                border-radius: 5px;
                padding: 5px;
                font-size: 12px;
            }
        """)

        # ---- First tab ----
        self.add_new_tab(QUrl(self.HOME_URL))

    # =========================
    # Этап 2: add_new_tab
    # =========================
    def add_new_tab(self, url: QUrl | None = None):
        if url is None:
            url = QUrl(self.HOME_URL)

        browser = QWebEngineView()
        browser.setUrl(url)

        # Заголовок вкладки
        browser.titleChanged.connect(lambda title, b=browser: self.update_tab_title(b, title))

        # URL и история
        browser.urlChanged.connect(lambda qurl, b=browser: self.on_url_changed(qurl, b))

        index = self.tabs.addTab(browser, "Загрузка...")
        self.tabs.setCurrentIndex(index)

    def update_tab_title(self, browser: QWebEngineView, title: str):
        index = self.tabs.indexOf(browser)
        if index != -1:
            self.tabs.setTabText(index, title if title else "Новая вкладка")

    def on_url_changed(self, qurl: QUrl, browser: QWebEngineView):
        url = qurl.toString()

        # обновляем url_bar только если это активная вкладка
        if self.tabs.currentWidget() is browser:
            self.url_bar.setText(url)

        # история без дублей подряд
        if not self.history or self.history[-1] != url:
            self.history.append(url)

    def on_current_tab_changed(self, _index: int):
        w = self.tabs.currentWidget()
        if isinstance(w, QWebEngineView):
            self.url_bar.setText(w.url().toString())
        else:
            self.url_bar.setText("")

    # =========================
    # Навигация
    # =========================
    def current_browser(self):
        w = self.tabs.currentWidget()
        return w if isinstance(w, QWebEngineView) else None

    def go_back(self):
        b = self.current_browser()
        if b and b.history().canGoBack():
            b.back()

    def go_forward(self):
        b = self.current_browser()
        if b and b.history().canGoForward():
            b.forward()

    def reload_page(self):
        b = self.current_browser()
        if b:
            b.reload()

    def go_home(self):
        b = self.current_browser()
        if b:
            b.setUrl(QUrl(self.HOME_URL))

    def navigate_to_url(self):
        text = self.url_bar.text().strip()
        if not text:
            return

        # если пользователь ввёл без схемы — добавим https://
        if "://" not in text:
            text = "https://" + text

        b = self.current_browser()
        if b:
            b.setUrl(QUrl(text))

    # =========================
    # История
    # =========================
    def show_history(self):
        history_widget = QWidget()
        layout = QVBoxLayout(history_widget)
        history_list = QListWidget()

        for url in self.history:
            history_list.addItem(url)

        history_list.itemClicked.connect(self.navigate_from_history)

        layout.addWidget(history_list)

        index = self.tabs.addTab(history_widget, "История")
        self.tabs.setCurrentIndex(index)

    def navigate_from_history(self, item):
        url = item.text()
        self.add_new_tab(QUrl(url))  # открываем выбранное в новой вкладке

    def open_new_tab(self):
        self.add_new_tab(QUrl(self.HOME_URL))

    def close_tab_by_index(self, index: int):
        # не даём закрыть последнюю вкладку
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
