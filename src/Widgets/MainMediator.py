from importlib import metadata
from typing import List, Tuple
from PyQt5.QtWidgets import QMainWindow, QDesktopWidget, QMessageBox, QPushButton, QLineEdit, QLabel, QDialog, QHBoxLayout, QVBoxLayout, QWidget, QApplication, QAction, QStackedWidget, QTabWidget, QSizePolicy, QTabBar
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtCore import QSize
from main import VERSION_MINOR, VERSION_MAJOR

from CacheManager import CacheManager, CACHE_STD_PATH
from GameListener import GameListener
import resources
from Widgets.ArenaView import ArenaView
from Widgets.LibraryView import LibraryView
from utils.Thread import Thread, send_to_thread, CardsDownloadThread
from DataPresenter import DataPresenter
from Widgets.CardBuilderView import CardBuilderView

from DataTypes import CardMetadata, Deck, Response, StdMetadata
from Widgets.components.ConnectionSettings import ConnectionSettingsDialog
from Widgets.components.NotificationWidget import NotificationWidget
from Widgets.components.LoadingOverlay import LoadingOverlay

class MainMediator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(':icons/icon.ico'))
        self.setWindowTitle(f'Hearthtrice Manager {VERSION_MAJOR}.{VERSION_MINOR}')
        self.data_presenter = DataPresenter()

        self.bool = True
        
        self.set_up_ui()
        self.set_up_connections()
        self.center()

    def set_up_connections(self):
        self.card_builder_view.upload_requested.connect(self.upload_card)
            #lambda n: send_to_thread(self, self.upload_card, args=(n,), kwargs=()))
        self.card_builder_view.upload_edit_requested.connect(self.upload_edit_card)

        self.library_view.update_library_requested.connect(self._on_update_library_requested)
        self.library_view.finished_loading.connect(self._on_library_finished_loading)
        self.library_view.create_new_deck_requested.connect(
            lambda name: send_to_thread(self, self.data_presenter.create_new_deck, self.on_deck_created, args=(name,)))
        self.library_view.update_deck_requested.connect(
            lambda deckdata: send_to_thread(self, self.data_presenter.update_deck, self.on_deck_updated, args=(deckdata[0],deckdata[1],)))
        self.library_view.rename_deck_requested.connect(
            lambda tid_name: send_to_thread(self, self.data_presenter.rename_deck,
                lambda resp: self.on_deck_renamed(resp, tid_name[0], tid_name[1]),
                args=(tid_name[0], tid_name[1])))
        self.library_view.duplicate_deck_requested.connect(self.on_duplicate_deck_requested)
        self.library_view.delete_deck_requested.connect(
            lambda deck_id: send_to_thread(self, self.data_presenter.delete_deck, self.on_deck_deleted, args=(deck_id,)))
        self.library_view.get_decks_requsted.connect(
            lambda: send_to_thread(self, self.data_presenter.get_decks, self.update_decks))
        self.library_view.edit_card_requested.connect(self.on_edit_card_requested_A)
        self.library_view.delete_card_requested.connect(self.on_delete_card_requested)
        self.library_view.infobase_load_requested.connect(self._on_infobase_load_requested)
        self.library_view.infobase_save_requested.connect(self._on_infobase_save_requested)

        self.game_listener.switch_to_library.connect(
            lambda: self.stacked_widget.setCurrentIndex(1))

        self.connection_settings.settings_button.button.clicked.connect(self.on_settings_clicked)
        self.connection_settings.connection_response_received.connect(self.on_connection_response_received)

    def set_up_ui(self):
        self.connection_settings = ConnectionSettingsDialog(self.data_presenter, self)

        self.cache_manager = CacheManager(self.data_presenter)
        self.std_cache_manager = CacheManager(
            self.data_presenter,
            cache_subdir=CACHE_STD_PATH,
            meta_cls=StdMetadata,
        )

        self.card_builder_view = CardBuilderView(self.cache_manager, self)
        self.library_view = LibraryView(self)
        self.arena_view = ArenaView(self.library_view, self)
        self.game_listener = GameListener(self.library_view, self)

        self.central_widget = QWidget(self)
        self.gen_layout = QVBoxLayout()
        self.layout_inlay1 = QHBoxLayout()
        self.connection_settings.settings_button.setParent(self)


        self.tab_bar = QTabBar(self)
        self.stacked_widget = QStackedWidget(self)
        self.tab_bar.currentChanged.connect(self.stacked_widget.setCurrentIndex)
        
        self.tab_bar.addTab("Редактор карт")
        self.stacked_widget.addWidget(self.card_builder_view)
        self.tab_bar.addTab("Библиотека")
        self.stacked_widget.addWidget(self.library_view)
        self.tab_bar.addTab("Арена")
        self.stacked_widget.addWidget(self.arena_view)

        self.stacked_widget.setCurrentIndex(0)        

        self.layout_inlay1.addWidget(self.tab_bar)
        self.layout_inlay1.addWidget(self.connection_settings.settings_button)
        self.gen_layout.addLayout(self.layout_inlay1)
        self.gen_layout.addWidget(self.stacked_widget)

        self.central_widget.setLayout(self.gen_layout)
        self.setCentralWidget(self.central_widget)
        
        self.loading_overlay = LoadingOverlay(self)
        self.loading_overlay.hide()

    def center(self):
        screen = QDesktopWidget().availableGeometry()
        screen_width = screen.width()
        screen_height = screen.height()
        win_w, win_h = 1280, 940
        x = max(0, (screen_width - win_w) // 2)
        y = max(0, (screen_height - win_h) // 2)
        self.setMinimumSize(1200, 900)
        self.resize(win_w, win_h)
        self.move(x, y)

    def on_connection_response_received(self, response: Response):
        if response.ok:
            self.library_view.update()
        else:
            NotificationWidget(self, f"Ошибка подключения: {response.msg}", "error")

    def on_hashes_received(self, hashlist: List[dict]):
        if not hashlist:
            print("Custom hashes empty")
            self._start_std_library_update()
            return
        ids_to_request = self.cache_manager.get_discrepant_ids(hashlist)
        if not ids_to_request:
            print("Nothing no download")
            self.update_library_from_cache()
            return
        
        print("\nIDs to download:", ids_to_request)
        self.show_loading("Скачивание карт")
        self._start_cards_download(
            self.data_presenter.get_library,
            ids_to_request,
            self.on_library_part_received,
        )

    def _start_cards_download(self, fetch_fn, ids, finished_handler):
        thread = CardsDownloadThread(fetch_fn, ids, self)
        thread.progress.connect(self._on_download_progress)
        thread.finished_ok.connect(finished_handler)
        thread.finished_ok.connect(thread.deleteLater)
        thread.start()
        self._download_thread = thread

    def _on_download_progress(self, current: int, total: int, card_id):
        self.loading_overlay.set_progress(current, total, card_id)

    def on_library_part_received(self, received_card_metadata):
        if isinstance(received_card_metadata, Response) and not received_card_metadata.ok:
            NotificationWidget(self, received_card_metadata.msg, "error")
            self._start_std_library_update()
            return
        if not received_card_metadata:
            print("Custom library fetch empty")
            self.update_library_from_cache()
            return
        self.show_loading("Кэширование карт")
        self.cache_manager.save_cache(received_card_metadata)
        print("Updated cards have been cached.")
        
        def export_after_update(cached_library):
            self.library_view.set_updated_library(cached_library)
            self.library_view.on_export_clicked(received_card_metadata, cached_library)
            self._start_std_library_update()
        
        send_to_thread(self, self.cache_manager.get_cache, export_after_update)

    def update_library_from_cache(self):
        def callback(cached_library):
            self.library_view.set_updated_library(cached_library)
            self._start_std_library_update()
        send_to_thread(self, self.cache_manager.get_cache, callback)

    def _start_std_library_update(self):
        self.show_loading("Загрузка стандартных карт")
        send_to_thread(self, self.data_presenter.get_std_hashes, self.on_std_hashes_received)

    def on_std_hashes_received(self, hashlist: List[dict]):
        if not hashlist:
            print("Std hashes empty")
            self.update_std_library_from_cache()
            return
        ids_to_request = self.std_cache_manager.get_discrepant_ids(hashlist)
        if not ids_to_request:
            print("Nothing to download for std")
            self.update_std_library_from_cache()
            return

        print("\nStd IDs to download:", ids_to_request)
        self.show_loading("Скачивание стандартных карт")
        self._start_cards_download(
            self.data_presenter.get_std_library,
            ids_to_request,
            self.on_std_library_part_received,
        )

    def on_std_library_part_received(self, received_card_metadata):
        if isinstance(received_card_metadata, Response) and not received_card_metadata.ok:
            NotificationWidget(self, received_card_metadata.msg, "error")
            self.update_std_library_from_cache()
            return
        if not received_card_metadata:
            print("Std library fetch empty")
            self.update_std_library_from_cache()
            return
        self.show_loading("Кэширование стандартных карт")
        self.std_cache_manager.save_cache(received_card_metadata)
        print("Updated std cards have been cached.")

        def callback(cached_library):
            self.library_view.set_updated_std_library(cached_library)
            self._refresh_set_filters()
        send_to_thread(self, self.std_cache_manager.get_cache, callback)

    def update_std_library_from_cache(self):
        def callback(cached_library):
            self.library_view.set_updated_std_library(cached_library)
            self._refresh_set_filters()
        send_to_thread(self, self.std_cache_manager.get_cache, callback)

    def _refresh_set_filters(self):
        def callback(sets_data):
            if not sets_data:
                return
            custom_map = sets_data.get("custom_map") or {}
            std_map = sets_data.get("std_map") or {}
            self.cache_manager.patch_sets(custom_map)
            self.std_cache_manager.patch_sets(std_map)
            self.library_view.set_available_sets(
                sets_data.get("custom", []),
                sets_data.get("std", []),
                custom_map,
                std_map,
            )
        send_to_thread(self, self.data_presenter.get_card_sets, callback)

    def on_deck_created(self, new_deck_data: tuple):
        if not new_deck_data:
            return
        self.library_view.deck_view.on_new_deck_data_received(new_deck_data)

    def on_deck_updated(self, response: Response):
        if response.ok:
            deck_name = ""
            if self.library_view.deck_view.current_deck:
                deck_name = self.library_view.deck_view.current_deck.name.upper()
            
            if deck_name:
                NotificationWidget(self, f"Колода {deck_name} успешно обновлена.", "success", deck_name)
            else:
                NotificationWidget(self, "Колода успешно обновлена.", "success")
        else:
            NotificationWidget(self, f"Ошибка: {response.msg}", "error")

    def on_deck_renamed(self, response: Response, deck_id: int, new_name: str):
        if response.ok:
            self.library_view.deck_view.on_deck_name_renamed(new_name)
            NotificationWidget(self, f"Колода переименована: {new_name}", "success")
        else:
            NotificationWidget(self, f"Ошибка переименования: {response.msg}", "error")

    def on_duplicate_deck_requested(self):
        dv = self.library_view.deck_view
        if not dv.current_deck:
            return
        name = dv.current_deck.name + " (копия)"
        cards_str = dv.tree_widget.current_decktree_to_str()
        rich_cards = dv.get_current_rich_deck().cards
        send_to_thread(self, self.data_presenter.create_new_deck,
            lambda data: self._on_duplicate_created(data, cards_str, rich_cards), args=(name,))

    def _on_duplicate_created(self, new_deck_data, cards_str, rich_cards):
        if not new_deck_data:
            return
        deck_id, deck_name, owner = new_deck_data
        send_to_thread(self, self.data_presenter.update_deck,
            lambda resp: self._on_duplicate_updated(resp, new_deck_data, rich_cards), args=(deck_id, cards_str))

    def _on_duplicate_updated(self, response: Response, new_deck_data, rich_cards):
        if not response.ok:
            NotificationWidget(self, f"Ошибка дублирования: {response.msg}", "error")
            return
        deck_id, deck_name, owner = new_deck_data
        self.library_view.deck_view.set_duplicated_deck(deck_id, deck_name, owner, rich_cards or [])
        NotificationWidget(self, f"Колода «{deck_name}» создана.", "success")

    def on_deck_deleted(self, response: Response):
        if response.ok:
            self.library_view.deck_view.on_deck_deleted()
            NotificationWidget(self, "Колода удалена.", "success")
        else:
            NotificationWidget(self, f"Ошибка удаления: {response.msg}", "error")


    def on_settings_clicked(self):
        self.connection_settings.show()

    def update_decks(self, decks):
        if isinstance(decks, Response):
            NotificationWidget(self, f"Ошибка загрузки колод: {decks.msg}", "error")
            return
        if not decks:
            return
        self.library_view.set_updated_decks(decks)

    def upload_card(self, metadata: CardMetadata):
        response = self.data_presenter.upload_card(metadata)
        if response.ok:
            self.library_view.update_uploaded_card(metadata)
            self.library_view.on_export_clicked([metadata])
            if hasattr(metadata, 'id') and metadata.id:
                self.cache_manager.save_cache([metadata])
            NotificationWidget(self, "Карта загружена в библиотеку.", "success")
            self._refresh_set_filters()
        else:
            NotificationWidget(self, f"Ошибка: {response.msg}", "error")


    def upload_edit_card(self, metas: Tuple[CardMetadata]):
        response = self.data_presenter.upload_edit_card(metas[0])
        if response.ok:
            is_std = isinstance(metas[0], StdMetadata)
            if not is_std:
                self.data_presenter.upload_edit_changelog(metas[0], metas[1])
            self.library_view.update_edited_card(metas[0])
            self.library_view.on_export_clicked([metas[0]])
            if hasattr(metas[0], 'id') and metas[0].id:
                if is_std:
                    self.std_cache_manager.save_cache([metas[0]])
                else:
                    self.cache_manager.save_cache([metas[0]])
            NotificationWidget(self, "Карта изменена.", "success")
            self._refresh_set_filters()
        else:
            NotificationWidget(self, f"Ошибка: {response.msg}", "error")

    def upload_edit_card_changelog(self, metadata: CardMetadata, old_metadata: CardMetadata = None):
        response = self.data_presenter.upload_edit_card(metadata, old_metadata)
        if response.ok:
            self.library_view.update_edited_card(metadata)
            print("Logs updated")

    def on_edit_card_requested_A(self, metadata: CardMetadata):
        def callback(edit_data: CardMetadata):
            if not edit_data:
                self.hide_loading()
                NotificationWidget(self, "Не удалось загрузить данные карты.", "error")
                return
            self.card_to_edit_metadata.update(edit_data.dict())
            self.card_builder_view.on_edit_card_requested(self.card_to_edit_metadata)
            self.stacked_widget.setCurrentIndex(0)
            self.tab_bar.setCurrentIndex(0)
            self.hide_loading()
        self.card_to_edit_metadata = metadata
        self.show_loading("Загрузка данных...")
        from_std = isinstance(metadata, StdMetadata)
        send_to_thread(self, self.data_presenter.get_edit_data, callback, args=(metadata.id, from_std))
    

    def on_delete_card_requested(self, metadata: CardMetadata):
        dialog = QDialog(self)
        dialog.setWindowTitle("Удаление карты")

        label = QLabel(f"Удалить карту ID:{metadata.id} {metadata.name}?")

        ok_button = QPushButton("Удалить", dialog)
        ok_button.clicked.connect(dialog.accept)

        no_button = QPushButton("Отмена", dialog)
        no_button.clicked.connect(dialog.reject)

        layout = QVBoxLayout(dialog)
        layout.addWidget(label)
        layout.addWidget(ok_button)
        layout.addWidget(no_button)

        dialog.setLayout(layout)

        if not dialog.exec_():
            return        
        
        response = self.data_presenter.delete_card(metadata)
        if response.ok:
            if isinstance(metadata, StdMetadata):
                self.std_cache_manager.delete_from_cache(metadata.id)
            else:
                self.cache_manager.delete_from_cache(metadata.id)
            self.library_view.update()
            NotificationWidget(self, "Карта удалена.", "success")
        else:
            NotificationWidget(self, f"Ошибка: {response.msg}", "error")

    # def f(self, c=None, d='r'):
    #     print(c,d)
    #     return requests.get('http://example.com').text

    # def handle_reply2(self, data):
    #     print(data)

    def resizeEvent(self, a0) -> None:
        tab_width = str( (self.width() / self.tab_bar.count()) - 45)
        self.tab_bar.setStyleSheet("QTabBar::tab {min-width: " + tab_width + "px; min-height: 50px; font-family: Arial; font-weight: bold; font-size: 16pt}")
        if self.width() > 1500 and self.bool:
            self.bool = False

        self.loading_overlay.setGeometry(self.rect())

        return super().resizeEvent(a0)
    
    def show_loading(self, text: str = "Загрузка..."):
        self.loading_overlay.setGeometry(self.rect())
        self.loading_overlay.show_overlay(text)
    
    def hide_loading(self):
        self.loading_overlay.hide_overlay()
    
    def _on_update_library_requested(self):
        self.show_loading("Загрузка библиотеки...")
        send_to_thread(self, self.data_presenter.get_hashes, self.on_hashes_received)
    
    def _on_library_finished_loading(self, is_finished: bool):
        if is_finished:
            self.hide_loading()

    def _on_infobase_load_requested(self):
        def callback(content: str):
            self.library_view.set_infobase_content(content or "")
        send_to_thread(self, self.data_presenter.get_infobase, callback)

    def _on_infobase_save_requested(self, content: str):
        response = self.data_presenter.save_infobase(content)
        if response.ok:
            NotificationWidget(self, "Текст InfoBase сохранен.", "success")
        else:
            NotificationWidget(self, f"Ошибка сохранения: {response.msg}", "error")
