#!/usr/bin/env python3
import sys
import os
import time
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QListWidget, QListWidgetItem,
    QSplitter, QComboBox, QMessageBox, QFrame, QInputDialog, QMenu, QAction
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from database import DiaryDB
from styles import get_stylesheet


MONTH_NAMES = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
}


def format_russian_date(date_str):
    if not date_str:
        return ""
    try:
        parts = date_str.split()[0].split("-")
        year = int(parts[0])
        month = int(parts[1])
        day = int(parts[2])
        today = datetime.now().date()
        entry_date = datetime(year, month, day).date()

        if entry_date == today:
            prefix = "Сегодня, "
        elif (today - entry_date).days == 1:
            prefix = "Вчера, "
        else:
            prefix = ""

        return f"{prefix}{day} {MONTH_NAMES.get(month, '')} {year}"
    except Exception:
        return date_str


def format_duration(seconds):
    if not seconds or seconds <= 0:
        return "менее минуты"
    minutes = seconds // 60
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0:
        return f"{hours} ч {mins} мин"
    if mins > 0:
        return f"{mins} мин"
    return f"{seconds} сек"


class EntryEditorWindow(QMainWindow):
    """
    Отдельное полноэкранное окно создания / редактирования записи.
    Не блокирует главное окно (немодальное).
    """
    saved = pyqtSignal()

    def __init__(self, db, entry=None, categories=None, preselected_category=None):
        super().__init__()
        self.db = db
        self.entry = entry
        self.categories = [c["name"] for c in (categories or [])]
        self.preselected_category = preselected_category
        self.start_timestamp = time.time()

        self.setWindowTitle("Редактирование записи" if entry else "Новая запись")
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(14)
        layout.setContentsMargins(40, 30, 40, 30)

        # Row 1: Title
        vbox_title = QVBoxLayout()
        vbox_title.setSpacing(6)
        lbl_title = QLabel("Заголовок")
        lbl_title.setObjectName("sectionHeader")
        self.edit_title = QLineEdit()
        self.edit_title.setPlaceholderText("О чем эта запись?")
        self.edit_title.setFont(QFont("", 14))
        vbox_title.addWidget(lbl_title)
        vbox_title.addWidget(self.edit_title)
        layout.addLayout(vbox_title)

        # Row 2: Category Selector
        vbox_topic = QVBoxLayout()
        vbox_topic.setSpacing(6)
        lbl_topic = QLabel("Категория")
        lbl_topic.setObjectName("sectionHeader")

        row_cat = QHBoxLayout()
        row_cat.setSpacing(10)

        self.combo_category = QComboBox()
        self.combo_category.setEditable(False)
        self.populate_categories()

        self.btn_add_category = QPushButton("+ Новая категория")
        self.btn_add_category.setObjectName("btnSecondarySmall")
        self.btn_add_category.clicked.connect(self.on_create_new_category)

        row_cat.addWidget(self.combo_category, stretch=3)
        row_cat.addWidget(self.btn_add_category, stretch=1)

        vbox_topic.addWidget(lbl_topic)
        vbox_topic.addLayout(row_cat)
        layout.addLayout(vbox_topic)

        # Row 3: Text Content
        vbox_content = QVBoxLayout()
        vbox_content.setSpacing(6)
        lbl_content = QLabel("Текст")
        lbl_content.setObjectName("sectionHeader")

        self.text_content = QTextEdit()
        self.text_content.setAcceptRichText(False)
        self.text_content.setObjectName("editorText")
        self.text_content.setPlaceholderText("Пишите сюда свои мысли...")
        self.text_content.textChanged.connect(self.update_counts)

        vbox_content.addWidget(lbl_content)
        vbox_content.addWidget(self.text_content)
        layout.addLayout(vbox_content, stretch=1)

        # Footer Row
        row_footer = QHBoxLayout()
        self.lbl_counter = QLabel("0 слов")
        self.lbl_counter.setObjectName("statItem")
        row_footer.addWidget(self.lbl_counter)

        row_footer.addStretch()

        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.clicked.connect(self.close)
        row_footer.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("Сохранить запись")
        self.btn_save.setObjectName("btnPrimary")
        self.btn_save.clicked.connect(self.save_entry)
        row_footer.addWidget(self.btn_save)

        layout.addLayout(row_footer)

        # Populate
        if self.entry:
            self.edit_title.setText(self.entry["title"])
            index = self.combo_category.findText(self.entry["topic"])
            if index >= 0:
                self.combo_category.setCurrentIndex(index)
            self.text_content.setPlainText(self.entry["content"])
        elif self.preselected_category:
            index = self.combo_category.findText(self.preselected_category)
            if index >= 0:
                self.combo_category.setCurrentIndex(index)

        self.update_counts()

    def populate_categories(self):
        self.combo_category.clear()
        if not self.categories:
            self.categories = ["Мысли", "Личное", "Работа", "Идеи", "Планы"]
        for cat in sorted(self.categories):
            self.combo_category.addItem(cat)

    def on_create_new_category(self):
        name, ok = QInputDialog.getText(
            self,
            "Новая категория",
            "Введите название новой категории:"
        )
        if ok and name.strip():
            cat_name = name.strip()
            self.db.add_category(cat_name)
            if cat_name not in self.categories:
                self.categories.append(cat_name)
                self.populate_categories()
            index = self.combo_category.findText(cat_name)
            if index >= 0:
                self.combo_category.setCurrentIndex(index)

    def update_counts(self):
        text = self.text_content.toPlainText().strip()
        words = len(text.split()) if text else 0
        chars = len(self.text_content.toPlainText())
        self.lbl_counter.setText(f"{words} слов  •  {chars} знаков")

    def save_entry(self):
        title = self.edit_title.text().strip()
        content = self.text_content.toPlainText().strip()
        if not title and not content:
            QMessageBox.warning(self, "Внимание", "Запись не может быть пустой.")
            return

        elapsed_seconds = int(time.time() - self.start_timestamp)
        topic = self.combo_category.currentText().strip() or "Общее"

        if self.entry:
            self.db.update_entry(
                entry_id=self.entry["id"],
                title=title or "Запись без названия",
                topic=topic,
                content=content,
                added_duration_seconds=elapsed_seconds
            )
        else:
            self.db.add_entry(
                title=title or "Запись без названия",
                topic=topic,
                content=content,
                duration_seconds=elapsed_seconds
            )

        self.saved.emit()
        self.close()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DiaryDB()
        self.selected_topic = None
        self.selected_date = None
        self.current_entry_id = None
        self.active_editor_windows = []

        self.setWindowTitle("Дневник")
        self.setMinimumSize(850, 540)
        self.init_ui()
        self.load_all()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)

        # 1. Left Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("sidebarFrame")
        sidebar.setMinimumWidth(220)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(14, 16, 14, 16)
        sb_layout.setSpacing(12)

        lbl_app = QLabel("Дневник")
        lbl_app.setObjectName("appTitle")
        sb_layout.addWidget(lbl_app)

        self.btn_new = QPushButton("+ Новая запись")
        self.btn_new.setObjectName("btnPrimary")
        self.btn_new.clicked.connect(self.on_new_entry)
        sb_layout.addWidget(self.btn_new)

        # Categories Section Header with Add Button
        row_cat_hdr = QHBoxLayout()
        lbl_topics = QLabel("Категории")
        lbl_topics.setObjectName("sectionHeader")
        lbl_topics.setToolTip("Правый клик по категории для редактирования или удаления")

        self.btn_add_cat_sidebar = QPushButton("+")
        self.btn_add_cat_sidebar.setObjectName("btnSecondarySmall")
        self.btn_add_cat_sidebar.setToolTip("Создать новую категорию")
        self.btn_add_cat_sidebar.setFixedWidth(26)
        self.btn_add_cat_sidebar.clicked.connect(self.on_add_category_prompt)

        row_cat_hdr.addWidget(lbl_topics)
        row_cat_hdr.addStretch()
        row_cat_hdr.addWidget(self.btn_add_cat_sidebar)
        sb_layout.addLayout(row_cat_hdr)

        self.topics_list = QListWidget()
        self.topics_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.topics_list.setMaximumHeight(160)
        self.topics_list.itemClicked.connect(self.on_topic_clicked)
        self.topics_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.topics_list.customContextMenuRequested.connect(self.on_category_context_menu)
        sb_layout.addWidget(self.topics_list)

        # Days Section
        lbl_days = QLabel("Дни")
        lbl_days.setObjectName("sectionHeader")
        sb_layout.addWidget(lbl_days)

        self.days_list = QListWidget()
        self.days_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.days_list.setMaximumHeight(180)
        self.days_list.itemClicked.connect(self.on_day_clicked)
        sb_layout.addWidget(self.days_list)

        sb_layout.addStretch()

        # Stats Card
        stats_box = QFrame()
        stats_box.setObjectName("statsBox")
        stats_layout = QVBoxLayout(stats_box)
        stats_layout.setContentsMargins(10, 10, 10, 10)
        stats_layout.setSpacing(4)

        lbl_stats = QLabel("Статистика")
        lbl_stats.setObjectName("statTitle")
        stats_layout.addWidget(lbl_stats)

        self.stat_time = QLabel("Время письма: 0 мин")
        self.stat_time.setObjectName("statItem")
        stats_layout.addWidget(self.stat_time)

        self.stat_count = QLabel("Всего записей: 0")
        self.stat_count.setObjectName("statItem")
        stats_layout.addWidget(self.stat_count)

        sb_layout.addWidget(stats_box)
        splitter.addWidget(sidebar)

        # 2. Middle Panel: Entries List (Cards)
        center = QFrame()
        center.setObjectName("centerFrame")
        center.setMinimumWidth(300)
        c_layout = QVBoxLayout(center)
        c_layout.setContentsMargins(12, 16, 12, 16)
        c_layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по записям...")
        self.search_input.textChanged.connect(self.on_search_changed)
        c_layout.addWidget(self.search_input)

        self.lbl_filter_info = QLabel("Все записи")
        self.lbl_filter_info.setObjectName("statItem")
        c_layout.addWidget(self.lbl_filter_info)

        self.entries_list = QListWidget()
        self.entries_list.setObjectName("entriesListWidget")
        self.entries_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.entries_list.setWordWrap(True)
        self.entries_list.itemSelectionChanged.connect(self.on_entry_selected)
        c_layout.addWidget(self.entries_list)

        splitter.addWidget(center)

        # 3. Right Panel: Content Reader
        content_panel = QFrame()
        content_panel.setObjectName("contentFrame")
        content_panel.setMinimumWidth(340)
        cp_layout = QVBoxLayout(content_panel)
        cp_layout.setContentsMargins(28, 20, 28, 20)
        cp_layout.setSpacing(12)

        # Actions
        row_actions = QHBoxLayout()
        self.btn_edit = QPushButton("Редактировать")
        self.btn_edit.clicked.connect(self.on_edit_entry)
        self.btn_delete = QPushButton("Удалить")
        self.btn_delete.setObjectName("btnDanger")
        self.btn_delete.clicked.connect(self.on_delete_entry)

        row_actions.addWidget(self.btn_edit)
        row_actions.addWidget(self.btn_delete)
        row_actions.addStretch()
        cp_layout.addLayout(row_actions)

        # Title
        self.view_title = QLabel("Выберите запись для чтения")
        self.view_title.setObjectName("appTitle")
        self.view_title.setWordWrap(True)
        cp_layout.addWidget(self.view_title)

        # Meta
        self.view_meta = QLabel("")
        self.view_meta.setObjectName("statItem")
        self.view_meta.setStyleSheet("color: #a1a1aa; font-size: 12px;")
        self.view_meta.setWordWrap(True)
        cp_layout.addWidget(self.view_meta)

        # Content
        self.view_content = QTextEdit()
        self.view_content.setAcceptRichText(False)
        self.view_content.setObjectName("viewerText")
        self.view_content.setReadOnly(True)
        cp_layout.addWidget(self.view_content)

        splitter.addWidget(content_panel)

        splitter.setSizes([240, 360, 540])
        layout.addWidget(splitter)

    # Context Menu for Categories (Right-Click)
    def on_category_context_menu(self, pos):
        item = self.topics_list.itemAt(pos)
        category_name = item.data(Qt.UserRole) if item else None

        menu = QMenu(self)

        if category_name:
            action_rename = QAction(f"Переименовать «{category_name}»", self)
            action_rename.triggered.connect(lambda: self.on_rename_category(category_name))
            menu.addAction(action_rename)

            action_delete = QAction(f"Удалить категорию «{category_name}»", self)
            action_delete.triggered.connect(lambda: self.on_delete_category(category_name))
            menu.addAction(action_delete)
            menu.addSeparator()

        action_add = QAction("Создать новую категорию...", self)
        action_add.triggered.connect(self.on_add_category_prompt)
        menu.addAction(action_add)

        menu.exec_(self.topics_list.mapToGlobal(pos))

    def on_rename_category(self, old_name):
        new_name, ok = QInputDialog.getText(
            self,
            "Переименовать категорию",
            f"Новое название для категории «{old_name}»:",
            text=old_name
        )
        if ok and new_name.strip() and new_name.strip() != old_name:
            success = self.db.rename_category(old_name, new_name.strip())
            if success:
                if self.selected_topic == old_name:
                    self.selected_topic = new_name.strip()
                self.load_all()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось переименовать категорию (возможно, имя уже занято).")

    def on_delete_category(self, category_name):
        reply = QMessageBox.question(
            self,
            "Удаление категории",
            f"Удалить категорию «{category_name}»?\n"
            f"(Все заметки из этой категории будут перемещены в категорию «Общее»)",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.delete_category(category_name)
            if self.selected_topic == category_name:
                self.selected_topic = None
            self.load_all()

    # Data Loading
    def load_all(self):
        self.load_stats()
        self.load_categories()
        self.load_days()
        self.load_entries()

    def load_stats(self):
        stats = self.db.get_stats()
        self.stat_time.setText(f"Время письма: {format_duration(stats['total_duration'])}")
        self.stat_count.setText(f"Всего записей: {stats['total_entries']}")

    def load_categories(self):
        self.topics_list.blockSignals(True)
        self.topics_list.clear()

        all_item = QListWidgetItem("Все категории")
        all_item.setData(Qt.UserRole, None)
        self.topics_list.addItem(all_item)

        categories = self.db.get_categories()
        for cat in categories:
            item = QListWidgetItem(f"{cat['name']}  ({cat['count']})")
            item.setData(Qt.UserRole, cat["name"])
            self.topics_list.addItem(item)
            if self.selected_topic == cat["name"]:
                self.topics_list.setCurrentItem(item)

        if not self.selected_topic:
            self.topics_list.setCurrentItem(all_item)

        self.topics_list.blockSignals(False)

    def load_days(self):
        self.days_list.blockSignals(True)
        self.days_list.clear()

        all_item = QListWidgetItem("Все дни")
        all_item.setData(Qt.UserRole, None)
        self.days_list.addItem(all_item)

        dates = self.db.get_dates()
        for d in dates:
            label = f"{format_russian_date(d['date'])}  ({d['count']})"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, d["date"])
            self.days_list.addItem(item)
            if self.selected_date == d["date"]:
                self.days_list.setCurrentItem(item)

        if not self.selected_date:
            self.days_list.setCurrentItem(all_item)

        self.days_list.blockSignals(False)

    def load_entries(self):
        search_query = self.search_input.text().strip()
        entries = self.db.get_entries(
            topic=self.selected_topic,
            date=self.selected_date,
            search=search_query
        )

        self.entries_list.blockSignals(True)
        self.entries_list.clear()

        for entry in entries:
            date_formatted = format_russian_date(entry["date"])
            preview = entry["content"].replace("\n", " ").strip()
            if len(preview) > 55:
                preview = preview[:55] + "..."

            card_text = (
                f"{entry['title']}\n"
                f"{date_formatted}  •  {entry['topic']}\n"
                f"{preview}"
            )
            item = QListWidgetItem(card_text)
            item.setData(Qt.UserRole, entry["id"])
            self.entries_list.addItem(item)

        self.entries_list.blockSignals(False)

        # Status text
        parts = []
        if self.selected_topic:
            parts.append(f"Категория: {self.selected_topic}")
        if self.selected_date:
            parts.append(f"День: {format_russian_date(self.selected_date)}")
        if search_query:
            parts.append(f"Поиск: «{search_query}»")

        if parts:
            self.lbl_filter_info.setText(" | ".join(parts))
        else:
            self.lbl_filter_info.setText(f"Все записи ({len(entries)})")

        if entries:
            self.entries_list.setCurrentRow(0)
            self.on_entry_selected()
        else:
            self.clear_viewer()

    def clear_viewer(self):
        self.current_entry_id = None
        self.view_title.setText("Нет записей")
        self.view_meta.setText("")
        self.view_content.clear()
        self.btn_edit.setEnabled(False)
        self.btn_delete.setEnabled(False)

    # Handlers
    def on_entry_selected(self):
        current_item = self.entries_list.currentItem()
        if not current_item:
            self.clear_viewer()
            return

        entry_id = current_item.data(Qt.UserRole)
        entry = self.db.get_entry_by_id(entry_id)
        if not entry:
            self.clear_viewer()
            return

        self.current_entry_id = entry["id"]
        self.view_title.setText(entry["title"])

        created_time = entry.get("created_at", "")
        time_part = created_time.split()[1] if len(created_time.split()) > 1 else ""
        date_formatted = format_russian_date(entry["date"])
        if time_part:
            date_formatted += f" в {time_part}"

        writing_duration = format_duration(entry["duration_seconds"])

        meta_text = (
            f"{date_formatted}   •   Категория: {entry['topic']}   •   "
            f"Время письма: {writing_duration}   •   {entry['word_count']} слов"
        )
        self.view_meta.setText(meta_text)
        self.view_content.setPlainText(entry["content"])
        self.btn_edit.setEnabled(True)
        self.btn_delete.setEnabled(True)

    def on_topic_clicked(self, item):
        topic = item.data(Qt.UserRole)
        self.selected_topic = topic
        self.load_entries()

    def on_day_clicked(self, item):
        day = item.data(Qt.UserRole)
        self.selected_date = day
        self.load_entries()

    def on_search_changed(self):
        self.load_entries()

    def on_add_category_prompt(self):
        name, ok = QInputDialog.getText(
            self,
            "Новая категория",
            "Название новой категории:"
        )
        if ok and name.strip():
            self.db.add_category(name.strip())
            self.load_categories()

    # Modeless Fullscreen Editor Window Openers
    def on_new_entry(self):
        categories = self.db.get_categories()
        editor = EntryEditorWindow(
            db=self.db,
            categories=categories,
            preselected_category=self.selected_topic
        )
        editor.saved.connect(self.load_all)
        self.active_editor_windows.append(editor)
        editor.destroyed.connect(lambda: self._cleanup_editor(editor))
        editor.showMaximized()

    def on_edit_entry(self):
        if not self.current_entry_id:
            return
        entry = self.db.get_entry_by_id(self.current_entry_id)
        if not entry:
            return

        categories = self.db.get_categories()
        editor = EntryEditorWindow(
            db=self.db,
            entry=entry,
            categories=categories
        )
        editor.saved.connect(self.load_all)
        self.active_editor_windows.append(editor)
        editor.destroyed.connect(lambda: self._cleanup_editor(editor))
        editor.showMaximized()

    def _cleanup_editor(self, editor):
        if editor in self.active_editor_windows:
            self.active_editor_windows.remove(editor)

    def on_delete_entry(self):
        if not self.current_entry_id:
            return
        reply = QMessageBox.question(
            self,
            "Удаление записи",
            "Удалить эту запись из дневника?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.delete_entry(self.current_entry_id)
            self.load_all()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(get_stylesheet())
    window = MainWindow()
    # Главное окно открывается сразу в полный экран
    window.showMaximized()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
