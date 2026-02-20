import sys
import os
from PyQt6.QtCore import QUrl, QSize, QPropertyAnimation, QEasingCurve, Qt
from PyQt6.QtGui import QIcon, QColor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QToolBar, QPushButton,
    QLineEdit, QWidget, QVBoxLayout, QListWidget, QTabBar, QHBoxLayout
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage

class AnimatedButton(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowIcon(QIcon("img/app.ico"))

        self._bg_color = QColor("transparent")
        self._anim = QPropertyAnimation(self, b"bgColor")
        self._anim.setDuration(500)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def enterEvent(self, event):
        self.animate_to(QColor("#666"))
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.animate_to(QColor("transparent"))
        super().leaveEvent(event)

    def animate_to(self, color):
        self._anim.stop()
        self._anim.setStartValue(self._bg_color)
        self._anim.setEndValue(color)
        self._anim.start()

    def get_bg(self):
        return self._bg_color

    def set_bg(self, color):
        self._bg_color = color
        self.setStyleSheet(f"""
            background-color: {color.name()};
            border-radius: 15px;
        """)

    bgColor = property(QColor, get_bg, set_bg)

class MainWindow(QMainWindow):
    HOME_URL = ("https://www.google.com/")

    def __init__(self):
        super().__init__()
        self.resize(1200, 800)
        self.history = []

        # Профиль клиента
        base_dir = os.path.join(os.path.dirname(__file__), "data")
        cache_dir = os.path.join(base_dir, "cache")
        store_dir = os.path.join(base_dir, "storage")
        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs(store_dir, exist_ok=True)

        self.profile = QWebEngineProfile("MyBrowserProfile", self)
        self.profile.setCachePath(cache_dir)
        self.profile.setPersistentStoragePath(store_dir)
        self.profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )

        # ---- Tabs ----
        self.tabs = QTabWidget()
        self.tabs.setElideMode(Qt.TextElideMode.ElideRight)  # обрезать длинные заголовки "..."
        self.tabs.setMovable(True)  # вкладки можно перетаскивать
        self.tabs.setDocumentMode(True)
        self.setCentralWidget(self.tabs)

        # ---- Toolbar ----
        self.navbar = QToolBar()
        self.addToolBar(self.navbar)

        # ---- Buttons ----

        back_btn = AnimatedButton()
        back_btn.setIcon(QIcon("img/back.png"))
        back_btn.setIconSize(QSize(18, 18))
        back_btn.clicked.connect(self.go_back)
        self.navbar.addWidget(back_btn)

        forward_btn = AnimatedButton()
        forward_btn.setIcon(QIcon("img/forward.png"))
        forward_btn.setIconSize(QSize(18, 18))
        forward_btn.clicked.connect(self.go_forward)
        self.navbar.addWidget(forward_btn)

        reload_btn = AnimatedButton()
        reload_btn.setIcon(QIcon("img/reload.png"))
        reload_btn.setIconSize(QSize(18, 18))
        reload_btn.clicked.connect(self.reload_page)
        self.navbar.addWidget(reload_btn)

        home_btn = AnimatedButton()
        home_btn.setIcon(QIcon("img/home.png"))
        home_btn.setIconSize(QSize(18, 18))
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

        # ---- First tab ----
        self.add_new_tab(QUrl(self.HOME_URL))


    # =========================
    # Этап 2: add_new_tab
    # =========================
    def add_new_tab(self, url: QUrl | None = None):
        if url is None:
            url = QUrl(self.HOME_URL)

        browser = QWebEngineView()

        page = Page(self.profile, self)
        browser.setPage(page)

        browser.titleChanged.connect(
            lambda title, b=browser: self.update_tab_title(b, title)
        )
        browser.urlChanged.connect(
            lambda qurl, b=browser: self.on_url_changed(qurl, b)
        )

        browser.setUrl(url)

        index = self.tabs.addTab(browser, "Загрузка...")
        self.tabs.setCurrentIndex(index)

    def createNewTab(self):
        browser = QWebEngineView()

        page = Page(self.profile, self)
        browser.setPage(page)

        browser.titleChanged.connect(
            lambda title, b=browser: self.update_tab_title(b, title)
        )
        browser.urlChanged.connect(
            lambda qurl, b=browser: self.on_url_changed(qurl, b)
        )

        index = self.tabs.addTab(browser, "Новая вкладка")
        self.tabs.setCurrentIndex(index)

        return page

    def update_tab_title(self, browser, title):
        index = self.tabs.indexOf(browser)
        if index == -1:
            return

        self.tabs.setTabText(index, title if title else "Новая вкладка")

        btn = AnimatedButton()
        btn.setFixedSize(18, 18)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                image: url("img/close.png");
                border-radius: 11px;
            }
            QPushButton:hover {
                image: url("img/close_active.png");
                transition: 0.9ms;
            }
        """)

        # ВАЖНО: закрывать по browser, чтобы при перетаскивании вкладок индекс не ломался
        btn.clicked.connect(lambda _, b=browser: self.close_tab_by_index(self.tabs.indexOf(b)))

        # ---- контейнер для сдвига кнопки влево ----
        holder = QWidget()
        lay = QHBoxLayout(holder)
        lay.setContentsMargins(0, 0, 8, 0)  # <-- увеличивай 8, чтобы сдвигать ВЛЕВО сильнее
        lay.setSpacing(0)
        lay.addWidget(btn)

        self.tabs.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, holder)

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

class Page(QWebEnginePage):
    def __init__(self, profile, main_win):
        super().__init__(profile, main_win)
        self.main_win = main_win

    def createWindow(self, win_type):
        return self.main_win.createNewTab()


if __name__ == '__main__':
    StyleBrowser = """
    /* ====== Base ====== */
    QMainWindow {
        background-color: #202124;
    }

    QWidget {
        font-family: "Segoe UI";
        font-size: 10.5pt;
    }

    /* ====== Toolbar (верхняя панель) ====== */
    QToolBar {
        background-color: #202124; 
        border: none;
        padding: 6px;
        spacing: 6px;
    }

    /* Кнопки на тулбаре (иконки + текстовые) */
    QToolBar QPushButton {
        background-color: transparent;
        border: none;
        border-radius: 12px;
        padding: 6px 10px;
        color: #E8EAED;
    }

    QToolBar QPushButton:hover {
        background-color: #303134;
    }

    QToolBar QPushButton:pressed {
        background-color: #3C4043;
    }

    /* Адресная строка - "pill" */
    QToolBar QLineEdit {
        background-color: #303134;
        border: 1px solid #303134;
        border-radius: 18px;
        padding: 8px 12px;
        color: #E8EAED;
        selection-background-color: #8AB4F8;
        selection-color: #202124;
        min-width: 420px;
    }

    QToolBar QLineEdit:focus {
        border: 1px solid #8AB4F8;
    }

    /* ====== Tabs ====== */
    QTabWidget::pane {
        border: none;
        background: #202124;
    }

    /* Полоса вкладок */
    QTabBar {
        background: #202124;
    }

    QTabBar::tab {
        background: #202124;
        color: #BDC1C6;
        padding: 8px 14px;
        margin-right: 4px;
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        min-width: 140px;
        max-width: 220px;
    }

    QTabBar::tab:hover {
        background: #2A2B2E;
        color: #E8EAED;
    }

    QTabBar::tab:selected {
        background: #303134;
        color: #E8EAED;
    }

    # /* Крестик вкладки */
    # QTabBar::close-button {
    #     image: none;
    #     border: none;
    #     border-radius: 8px;
    #     min-width: 16px;
    #     min-height: 16px;
    #     margin-left: 8px;
    # }
    # 
    # QTabBar::close-button:hover {
    #     background: #3C4043;
    # }

    /* Кнопка закрытия — рисуем "x" текстом (Qt не умеет text тут),
       поэтому оставляем как hover-area; если хочешь иконку — дам вариант ниже. */

    /* ====== Scrollbar (чуть ближе к Chrome) ====== */
    QScrollBar:vertical {
        background: #202124;
        width: 12px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background: #3C4043;
        border-radius: 6px;
        min-height: 24px;
    }
    QScrollBar::handle:vertical:hover {
        background: #5F6368;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: none;
    }

    QScrollBar:horizontal {
        background: #202124;
        height: 12px;
        margin: 0px;
    }
    QScrollBar::handle:horizontal {
        background: #3C4043;
        border-radius: 6px;
        min-width: 24px;
    }
    QScrollBar::handle:horizontal:hover {
        background: #5F6368;
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0px;
    }
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
        background: none;
    }
    """
    app = QApplication(sys.argv)
    app.setStyleSheet(StyleBrowser)
    app.setWindowIcon(QIcon("img/app.ico"))  # ← ВАЖНО
    window = MainWindow()
    window.setWindowTitle("Google Chrome")
    window.show()
    sys.exit(app.exec())

