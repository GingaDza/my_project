import sys
import os

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QListWidget,
    QMessageBox, QComboBox, QScrollArea, QTabWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QCloseEvent
from chart.mpl_chart_widget import MplChartWidget
from ui.utils.focus_clear_lineedit import FocusClearLineEdit
from data.data_manager import DataManager
from db.db_utils import init_db
from .ui.utils.excel_exporter import ExcelExporter
from .ui.utils.pdf_exporter import PdfExporter
from .ui.utils.worker_data import WorkerData
import os
from datetime import datetime

from .ui.overall_tab import OverallTab  # ここにインポート文を移動
from .ui.data_management_report_tab import DataManagementReportTab
from .ui.data_analysis_tab import DataAnalysisTab

class MainWindow(QMainWindow):
    """メインウィンドウのUIを管理するクラス。"""
    def __init__(self, data_manager):
        super().__init__()
        self.setWindowTitle("データベース整合性テストアプリ")
        self.setGeometry(100, 100, 1200, 900)  # 画面サイズを大きくする

        self.data_manager = data_manager
        self.categories = {
            'インダクション': ['アンローダー', 'エブリラベラー', 'オートラベラー', 'プッシャー', 'ウォータースパイダー', 'フィンガー'],
            'レーンソート': ['ストー', 'バッファー', '下流管理'],
            'ピック＆ステージ': ['ピック', '切り離し', 'TDR'],
            'その他': ['FC返送', 'リパック', '誘導']
        }
        # データベースからカテゴリを取得し、スキルレベルの数を決める
        self.categories_from_db = self.get_categories_from_db()
        self.num_skill_levels = len(self.categories_from_db)

        self.setup_ui()
        self.load_workers()
        self.selected_worker = None
        self.unsaved_changes = False
        self.skip_skill_level_change = False # 追加

         # PDF出力のためのインスタンスを作成
        self.pdf_exporter = PdfExporter() # 追加

        # アプリ起動時にチャートを初期値で描画
        self.update_chart_with_initial_values()

    def setup_ui(self):
        """UIのセットアップを行う。"""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        self.setup_left_panel()
        setup_right_panel() # この行を修正

    def setup_left_panel(self):
        """左側のパネル（ワーカーリスト）のセットアップ。"""
        left_panel_layout = QVBoxLayout()
        self.worker_list = QListWidget()
        # 選択した行の色を薄い青色にする
        self.worker_list.setStyleSheet("""
            QListWidget::item:selected {
                background-color: lightblue;
            }
        """)
        self.worker_list.itemClicked.connect(self.on_worker_selected)
        left_panel_layout.addWidget(self.worker_list)

        # ボタンを配置
        self.setup_buttons()
        left_panel_layout.addWidget(self.add_button)
        left_panel_layout.addWidget(self.delete_button)
        left_panel_layout.addWidget(self.export_data_button) # データ出力ボタン

        self.main_layout.addLayout(left_panel_layout)

    def setup_buttons(self):
        """ボタンのセットアップ。"""
        self.add_button = QPushButton("ワーカー追加")
        self.add_button.clicked.connect(self.new_worker)

        self.delete_button = QPushButton("ワーカー削除")
        self.delete_button.clicked.connect(self.delete_worker)

        self.export_data_button = QPushButton("データ出力")
        self.export_data_button.clicked.connect(lambda: self.export_data(os.path.join(os.path.dirname(__file__), "..", "output"))) # 変更

    def load_workers(self):
        """データベースからワーカーを読み込み、リストに表示する。"""
        workers = self.data_manager.get_all_workers()
        self.worker_list.clear()
        for worker in workers:
            self.worker_list.addItem(worker['name'])

    def on_worker_selected(self, item):
        """ワーカーが選択されたときの処理。"""
        print("--- MainWindow: on_worker_selected ---")
        print(f"  self.selected_worker: {self.selected_worker}")
        print(f"  self.name_input.text(): {self.name_input.text()}")

        # 未保存の変更がある場合、確認アラートを表示
        if self.unsaved_changes:
            reply = QMessageBox.question(self, '確認', '変更が保存されていません。保存しますか？',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
            if reply == QMessageBox.StandardButton.Yes:
                self.save_worker()
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        self.selected_worker = item.text()
        worker_name = item.text()
        worker = self.data_manager.get_worker_by_name(worker_name)
        if worker:
            self.name_input.setText(worker['name'])
            # スキルレベルをコンボボックスに設定する
            for tab_index in range(self.tab_widget.count()):
              current_tab_widget = self.tab_widget.widget(tab_index)
              skill_level_index = 0
              for child_layout_index in range(current_tab_widget.layout().count()):
                item = current_tab_widget.layout().itemAt(child_layout_index)
                if item:
                    if isinstance(item.layout(),QHBoxLayout):
                      child_layout = item.layout()
                      for inner_index in range(child_layout.count()):
                          widget = child_layout.itemAt(inner_index).widget()
                          if isinstance(widget, QComboBox):
                            if skill_level_index < len(worker['skill_levels']):
                                widget.setCurrentIndex(worker['skill_levels'][skill_level_index] - 1)
                                skill_level_index+=1
            # フォーカスを外して、フォーカスインイベントをトリガーしないようにする
            self.name_input.clearFocus()

            # 選択されたワーカーのスキルレベルでチャートを更新
            self.update_chart_with_selected_worker_skill_levels()

        self.unsaved_changes = False
        print("--- MainWindow: on_worker_selected End ---\n")

    def new_worker(self):
        """新規ワーカーの追加を開始する。"""
        print("--- MainWindow: new_worker ---")
        print(f"  self.selected_worker: {self.selected_worker}")
        print(f"  self.name_input.text(): {self.name_input.text()}")

        # 未保存の変更がある場合、確認アラートを表示
        if self.unsaved_changes:
            reply = QMessageBox.question(self, '確認', '変更が保存されていません。保存しますか？',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
            if reply == QMessageBox.StandardButton.Yes:
                self.save_worker()
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        # 新規追加モードに設定
        self.selected_worker = None

        # 入力欄とコンボボックスをクリア
        self.name_input.clear()
        for tab_index in range(self.tab_widget.count()):
          current_tab_widget = self.tab_widget.widget(tab_index)
          for child_layout_index in range(current_tab_widget.layout().count()):
            item = current_tab_widget.layout().itemAt(child_layout_index)
            if item:
                if isinstance(item.layout(),QHBoxLayout):
                    child_layout = item.layout()
                    for inner_index in range(child_layout.count()):
                        widget = child_layout.itemAt(inner_index).widget()
                        if isinstance(widget,QComboBox):
                           widget.setCurrentIndex(0)
        # 名前入力欄にフォーカスを設定
        self.name_input.setFocus()

        self.unsaved_changes = False

        # チャートを初期値で描画
        self.update_chart_with_initial_values()

        QMessageBox.information(self, "新規ワーカー", "新規ワーカーの情報を入力してください。")

        print("--- MainWindow: new_worker End ---\n")

    def save_worker(self):
        """ワーカーの保存処理（新規追加または更新）を行う。"""
        print("--- MainWindow: save_worker ---")
        print(f"  self.selected_worker: {self.selected_worker}")
        print(f"  self.name_input.text(): {self.name_input.text()}")

        name = self.name_input.text().strip()
        skill_levels = []
        for tab_index in range(self.tab_widget.count()):
            current_tab_widget = self.tab_widget.widget(tab_index)
            for child_layout_index in range(current_tab_widget.layout().count()):
              item = current_tab_widget.layout().itemAt(child_layout_index)
              if item:
                  if isinstance(item.layout(), QHBoxLayout):
                    child_layout = item.layout()
                    for inner_index in range(child_layout.count()):
                      widget = child_layout.itemAt(inner_index).widget()
                      if isinstance(widget, QComboBox):
                        skill_levels.append(int(widget.currentText()))

        if self.selected_worker:
            # 既存ワーカーの更新
            old_name = self.selected_worker
            if not name:
                QMessageBox.warning(self, "エラー", "名前を入力してください。")
                return
            if old_name != name and self.data_manager.get_worker_by_name(name):
                QMessageBox.warning(self, "エラー", "その名前の作業者は既に存在します。")
                return

            self.data_manager.update_worker(old_name, name, skill_levels)
            self.load_workers()
            self.clear_input_fields()
            self.name_input.reset_triggered = False
            QMessageBox.information(self, "成功", f"ワーカー {name} の情報を更新しました。")
            self.selected_worker = name
        else:
            # 新規ワーカーの追加
            if not name:
                QMessageBox.warning(self, "エラー", "名前を入力してください。")
                return

            if self.data_manager.get_worker_by_name(name):
                QMessageBox.warning(self, "エラー", "その名前の作業者は既に存在します。")
                return

            self.data_manager.add_worker(name, skill_levels)
            self.load_workers()
            self.clear_input_fields()
            self.name_input.reset_triggered = False
            QMessageBox.information(self, "成功", f"ワーカー {name} を追加しました。")
            self.selected_worker = None

        self.unsaved_changes = False
        print("--- MainWindow: save_worker End ---\n")

    def delete_worker(self):
        """選択されたワーカーを削除する。"""
        print("--- MainWindow: delete_worker ---")
        print(f"  self.selected_worker: {self.selected_worker}")
        print(f"  self.name_input.text(): {self.name_input.text()}")

        selected_item = self.worker_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "エラー", "ワーカーを選択してください。")
            return
        name = selected_item.text()
        reply = QMessageBox.question(self, "確認", f"{name} を削除しますか？\n削除前に保存することをお勧めします。",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.data_manager.delete_worker(name)
            self.load_workers()
            self.clear_input_fields()
            self.unsaved_changes = False
            QMessageBox.information(self, "成功", f"ワーカー {name} を削除しました。")

        print("--- MainWindow: delete_worker End ---\n")

    def clear_input_fields(self):
        """入力フィールドをクリアする。"""
        print("--- MainWindow: clear_input_fields ---")
        self.name_input.skip_on_text_changed = True  # 追加
        self.skip_skill_level_change = True  # 追加
        self.name_input.clear()
        for tab_index in range(self.tab_widget.count()):
          current_tab_widget = self.tab_widget.widget(tab_index)
          for child_layout_index in range(current_tab_widget.layout().count()):
            item = current_tab_widget.layout().itemAt(child_layout_index)
            if item:
                if isinstance(item.layout(), QHBoxLayout):
                    child_layout = item.layout()
                    for inner_index in range(child_layout.count()):
                        widget = child_layout.itemAt(inner_index).widget()
                        if isinstance(widget,QComboBox):
                           widget.setCurrentIndex(0)
        self.name_input.skip_on_text_changed = False # 追加
        self.skip_skill_level_change = False  # 追加
        print("--- MainWindow: clear_input_fields End ---\n")

    def closeEvent(self, event: QCloseEvent):
        """ウィンドウが閉じられるときの処理。未保存の変更がある場合は確認アラートを表示する。"""
        print("--- MainWindow: closeEvent ---")
        if self.unsaved_changes:
            reply = QMessageBox.question(self, '確認', '変更が保存されていません。保存しますか？',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
            if reply == QMessageBox.StandardButton.Yes:
                self.save_worker()
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
        event.accept()
        print("--- MainWindow: closeEvent End ---\n")

    def on_skill_level_changed(self):
        """スキルレベルが変更されたときに呼び出され、未保存状態にし、チャートを更新する。"""
        print("--- MainWindow: on_skill_level_changed ---")
        if self.skip_skill_level_change:  # 追加
            print("  Skill level change ignored due to skip_skill_level_change flag.")
            return
        self.unsaved_changes = True
        # 現在のタブのチャートを更新する
        current_tab_widget = self.tab_widget.currentWidget()
        current_tab_index = self.tab_widget.currentIndex()
        if current_tab_widget:
          skill_levels = []
          for child_layout_index in range(current_tab_widget.layout().count()):
            item = current_tab_widget.layout().itemAt(child_layout_index)
            if item:
                if isinstance(item.layout(), QHBoxLayout):
                    child_layout = item.layout()
                    for inner_index in range(child_layout.count()):
                        widget = child_layout.itemAt(inner_index).widget()
                        if isinstance(widget, QComboBox):
                          skill_levels.append(int(widget.currentText()))

          # 現在のタブに対応するカテゴリーとスキルレベルを抽出
          categories = self.get_categories_for_tab(current_tab_index)
          skill_levels = skill_levels[:len(categories)]
          skill_levels += [1] * (len(categories) - len(skill_levels))

          # チャートウィジェットの取得
          for layout_index in range(current_tab_widget.layout().count()):
            item = current_tab_widget.layout().itemAt(layout_index)
            if item:
                widget = item.widget() # QLayoutItem からウィジェットを取得
                if isinstance(widget, MplChartWidget):
                    chart_widget = widget
                    chart_widget.update_chart(skill_levels,categories)
        # 総合評価タブが選択されている場合もチャートを更新する
        if self.tab_widget.currentWidget() == self.overall_tab:
           self.overall_tab.update_chart()

        print("--- MainWindow: on_skill_level_changed End ---\n")

    def get_categories_from_db(self):
        """データベースからカテゴリーを取得するメソッド"""
        workers = self.data_manager.get_all_workers()
        if workers:
            # データベースにワーカーが存在する場合、最初のワーカーのスキルレベルの数をカテゴリー数として使用
            num_categories = len(workers[0]['skill_levels'])
        else:
            # ワーカーが存在しない場合、self.categories からカテゴリー数を計算
            num_categories = sum(len(sub_categories) for sub_categories in self.categories.values())

        categories = []
        for children in self.categories.values():
            for child in children:
                categories.append(child)
        return categories

    def update_chart_with_initial_values(self):
      """チャートを初期値（すべてのスキルレベルが1）で描画する。"""
      for tab_index in range(self.tab_widget.count()):
          current_tab_widget = self.tab_widget.widget(tab_index)

          # 現在のタブに対応するカテゴリーを取得
          categories = self.get_categories_for_tab(tab_index)
          initial_skill_levels = [1] * len(categories)  # すべてのスキルレベルを1に設定

          # チャートウィジェットの取得
          for layout_index in range(current_tab_widget.layout().count()):
              item = current_tab_widget.layout().itemAt(layout_index)
              if item:
                  widget = item.widget()  # QLayoutItem からウィジェットを取得
                  if isinstance(widget, MplChartWidget):
                      chart_widget = widget
                      chart_widget.update_chart(initial_skill_levels, categories)
        # 総合評価タブのチャートを更新する
      self.overall_tab.update_chart()

    def update_chart_with_selected_worker_skill_levels(self):
        """選択されたワーカーのスキルレベルでチャートを更新する。"""
        if self.selected_worker:
            worker = self.data_manager.get_worker_by_name(self.selected_worker)
            if not worker:
              return
            # タブごとにチャートを更新
            for tab_index in range(self.tab_widget.count()):
              current_tab_widget = self.tab_widget.widget(tab_index)

              # 現在のタブに対応するカテゴリーを取得
              categories = self.get_categories_for_tab(tab_index)

              # スキルレベルをリストに格納
              skill_levels_per_tab = []
              skill_levels = worker['skill_levels']
            #   現在のタブに対応するスキルレベルを抽出する
              tab_categories = []
              start_index = 0
              for sub_categories in self.categories.values():
                  for child in sub_categories:
                      tab_categories.append(child)

              skill_levels_for_tab = []
              tab_skill_count = 0
              tab_index_from_main = 0
              for key, value in self.categories.items():
                  if self.tab_widget.tabText(tab_index) == key:
                      start_index = tab_skill_count
                      for _ in value:
                          tab_skill_count +=1
                      tab_index_from_main = tab_skill_count
                      break
                  else:
                      for _ in value:
                          tab_skill_count +=1
              skill_levels_for_tab = skill_levels[start_index:tab_index_from_main]
            #   スキルレベルのリストの長さをカテゴリー数に合わせる
              skill_levels_for_tab = skill_levels_for_tab[:len(categories)]
              # 不足している場合は1で埋める
              skill_levels_for_tab += [1] * (len(categories) - len(skill_levels_for_tab))
              for layout_index in range(current_tab_widget.layout().count()):
                item = current_tab_widget.layout().itemAt(layout_index)
                if item:
                    widget = item.widget()  # QLayoutItem からウィジェットを取得
                    if isinstance(widget, MplChartWidget):
                        chart_widget = widget
                        chart_widget.update_chart(skill_levels_for_tab, categories)
        # 総合評価タブのチャートを更新する
        self.overall_tab.update_chart()

    def get_categories_for_tab(self, tab_index):
        """指定されたタブインデックスに対応するカテゴリーリストを返す。"""
        parent_category = self.tab_widget.tabText(tab_index)
        return self.categories.get(parent_category, [])