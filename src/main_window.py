from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QListWidget,
    QMessageBox, QComboBox, QScrollArea, QTabWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent
from .chart.mpl_chart_widget import MplChartWidget
from src.ui.utils.focus_clear_lineedit import FocusClearLineEdit
from src.data.data_manager import DataManager
from src.ui.overall_tab import OverallTab
from src.ui.data_management_report_tab import DataManagementReportTab
from src.ui.data_analysis_tab import DataAnalysisTab
import os
from datetime import datetime

class MainWindow(QMainWindow):
    """メインウィンドウのUIを管理するクラス。"""
    def __init__(self, data_manager):
        super().__init__()
        self.setWindowTitle("データベース整合性テストアプリ")
        self.setGeometry(100, 100, 1200, 900)  # 画面サイズを大きくする
        self.project_root = os.path.dirname(os.path.abspath(__file__))

        self.data_manager = data_manager
        self.categories = {
            'インダクション': ['アンローダー', 'エブリラベラー', 'オートラベラー', 'プッシャー', 'ウォータースパイダー', 'フィンガー'],
            'レーンソート': ['ストー', 'バッファー', '下流管理'],
            'ピック＆ステージ': ['ピック', '切り離し', 'TDR'],
            'その他': ['FC返送', 'リパック', '誘導']
        }
        # データベースからカテゴリを取得し、スキルレベルの数を決める
        self.categories_from_db = self.get_categories_from_db()
        self.num_skill_levels = len(self.get_categories_from_db())

        self.setup_ui()
        self.load_workers()
        self.selected_worker = None
        self.unsaved_changes = False
        self.skip_skill_level_change = False # 追加

        # アプリ起動時にチャートを初期値で描画
        self.update_chart_with_initial_values()

    def setup_ui(self):
        """UIのセットアップを行う。"""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        self.setup_left_panel()
        self.setup_right_panel()

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

        self.main_layout.addLayout(left_panel_layout)

    def setup_buttons(self):
        """ボタンのセットアップ。"""
        self.add_button = QPushButton("ワーカー追加")
        self.add_button.clicked.connect(self.new_worker)

        self.delete_button = QPushButton("ワーカー削除")
        self.delete_button.clicked.connect(self.delete_worker)

    def setup_right_panel(self):  # ここでselfを追加
        """右側のパネル（ワーカー情報の編集）のセットアップ。"""
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # 名前入力欄
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("名前:"))
        self.name_input = FocusClearLineEdit(parent=self)
        self.name_input.setPlaceholderText("名前を入力")
        name_layout.addWidget(self.name_input)
        right_layout.addLayout(name_layout)

        # タブウィジェットの作成
        self.tab_widget = QTabWidget()

        # 親カテゴリごとのレイアウトを作成し、タブに追加
        for parent_category, child_categories in self.categories.items():
            tab_widget = QWidget()
            tab_layout = QVBoxLayout(tab_widget)

            # 各子カテゴリに対応するコンボボックスを追加
            skill_combo_boxes = []
            for child_category in child_categories:
                child_layout = QHBoxLayout()
                child_layout.addWidget(QLabel(child_category))
                combo_box = QComboBox()
                combo_box.addItems([str(i) for i in range(1, 6)])
                combo_box.currentIndexChanged.connect(self.on_skill_level_changed)
                child_layout.addWidget(combo_box)
                skill_combo_boxes.append(combo_box) # コンボボックスをリストに追加
                tab_layout.addLayout(child_layout)
            # チャートウィジェットを追加
            chart_widget = MplChartWidget()
            tab_layout.addWidget(chart_widget)
            self.tab_widget.addTab(tab_widget, parent_category)
            
        # 総合評価タブ
        self.overall_tab = OverallTab(self.data_manager, self.get_categories_from_db())
        self.tab_widget.addTab(self.overall_tab, "総合評価")
        self.overall_tab.update_chart()

        # データ管理・レポートタブ
        self.data_management_report_tab = DataManagementReportTab(self.data_manager, self.categories)
        self.tab_widget.addTab(self.data_management_report_tab, "データ管理・レポート")

         # データ分析タブ
        self.data_analysis_tab = DataAnalysisTab(self.data_manager, self.get_categories_from_db)
        self.tab_widget.addTab(self.data_analysis_tab, "データ分析")

        right_layout.addWidget(self.tab_widget)

        # ボタン
        button_layout = QHBoxLayout()
        self.new_button = QPushButton("新規")
        self.new_button.clicked.connect(self.new_worker)
        button_layout.addWidget(self.new_button)

        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.save_worker)
        button_layout.addWidget(self.save_button)

        self.delete_button = QPushButton("削除")
        self.delete_button.clicked.connect(self.delete_worker)
        button_layout.addWidget(self.delete_button)

        right_layout.addLayout(button_layout)
        self.main_layout.addWidget(right_panel)

    def load_workers(self):
        """データベースからワーカーを読み込み、リストに表示する。"""
        workers = self.data_manager.get_all_workers()
        self.worker_list.clear()
        print("--- MainWindow: load_workers ---")
        for worker in workers:
            print(f"  Worker: {worker}")
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
                            try:
                               if skill_level_index < len(worker['skill_levels']):
                                  widget.setCurrentIndex(worker['skill_levels'][skill_level_index] - 1)
                                  skill_level_index+=1
                            except Exception as e:
                              print(f"Error setting skill level: {e}")
            # フォーカスを外して、フォーカスインイベントをトリガーしないようにする
            self.name_input.clearFocus()

            # 選択されたワーカーのスキルレベルでチャートを更新
            self.update_chart_with_selected_worker_skill_levels()

            # 他のタブのチャートも更新
            for tab_index in range(self.tab_widget.count()):
              if self.tab_widget.tabText(tab_index) != "総合評価":
                    self.update_chart_for_tab(tab_index)
            # 総合評価タブのチャートを更新する
            self.overall_tab.update_chart()

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
    
    def update_chart_for_tab(self, tab_index):
         """タブに対応するチャートを更新する"""
         current_tab_widget = self.tab_widget.widget(tab_index)
         if current_tab_widget:
          # 現在のタブに対応するカテゴリーを取得
          categories = self.get_categories_for_tab(tab_index)
          
          if self.selected_worker:
             worker = self.data_manager.get_worker_by_name(self.selected_worker)
             if not worker:
               return
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
          else:
            initial_skill_levels = [1] * len(categories)  # すべてのスキルレベルを1に設定

            # チャートウィジェットの取得
            for layout_index in range(current_tab_widget.layout().count()):
              item = current_tab_widget.layout().itemAt(layout_index)
              if item:
                 widget = item.widget()  # QLayoutItem からウィジェットを取得
                 if isinstance(widget, MplChartWidget):
                    chart_widget = widget
                    chart_widget.update_chart(initial_skill_levels, categories)

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
        if not self.categories_from_db:
          return []
        
        parent_categories = list(self.categories.keys())
        if tab_index >= len(parent_categories):
            return []
        
        parent_category = self.tab_widget.tabText(tab_index)
        return self.categories.get(parent_category, [])