# src/ui/data_analysis_tab.py
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QListWidget, QStackedWidget, QListWidgetItem,
    QPushButton
)
from PyQt6.QtCore import Qt
from src.chart.mpl_chart_widget import MplChartWidget
from src.data.data_manager import DataManager

class DataAnalysisTab(QWidget):
    """データ分析タブのUIとロジックを管理するクラス。"""
    def __init__(self, data_manager, get_categories_from_db_func):
        super().__init__()
        self.data_manager = data_manager
        self.get_categories_from_db = get_categories_from_db_func
        self.selected_worker = None
        self.setup_ui()

    def setup_ui(self):
        """UIのセットアップを行う。"""
        layout = QHBoxLayout(self)

        # サイドバー
        sidebar = QVBoxLayout()
        self.analysis_list = QListWidget()
        self.analysis_list.addItems(["統計分析", "ワーカー比較", "検索", "スキルギャップ分析"])
        self.analysis_list.currentItemChanged.connect(self.switch_analysis_view)
        sidebar.addWidget(self.analysis_list)

        # メインエリア (スタックウィジェットを使用)
        self.stacked_widget = QStackedWidget()

        # 各分析用のウィジェット
        self.statistics_widget = QWidget()
        self.setup_statistics_widget_ui()
        self.comparison_widget = QWidget()
        self.setup_comparison_widget_ui()
        self.search_widget = QWidget()
        self.setup_search_widget_ui()
        self.skill_gap_widget = QWidget()
        self.setup_skill_gap_widget_ui()

        self.stacked_widget.addWidget(self.statistics_widget)
        self.stacked_widget.addWidget(self.comparison_widget)
        self.stacked_widget.addWidget(self.search_widget)
        self.stacked_widget.addWidget(self.skill_gap_widget)

        layout.addLayout(sidebar)
        layout.addWidget(self.stacked_widget)

    def switch_analysis_view(self, current: QListWidgetItem, previous: QListWidgetItem):
        """選択された分析の種類に応じて表示を切り替える。"""
        if not current:
            current = previous

        if current.text() == "統計分析":
            self.stacked_widget.setCurrentWidget(self.statistics_widget)
        elif current.text() == "ワーカー比較":
            self.stacked_widget.setCurrentWidget(self.comparison_widget)
            self.update_comparison_worker_list()
        elif current.text() == "検索":
            self.stacked_widget.setCurrentWidget(self.search_widget)
        elif current.text() == "スキルギャップ分析":
            self.stacked_widget.setCurrentWidget(self.skill_gap_widget)

    def setup_statistics_widget_ui(self):
        """統計情報ウィジェットのUIをセットアップする。"""
        layout = QVBoxLayout(self.statistics_widget)
        layout.addWidget(QLabel("統計情報（未実装）"))

    def setup_comparison_widget_ui(self):
        """ワーカー比較ウィジェットのUIをセットアップする。"""
        layout = QVBoxLayout(self.comparison_widget)

        # ワーカー選択リスト
        self.comparison_list = QListWidget()
        self.comparison_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.comparison_list.itemSelectionChanged.connect(self.update_comparison_chart)
        layout.addWidget(self.comparison_list)

        # 比較チャート
        self.comparison_chart_widget = MplChartWidget()
        layout.addWidget(self.comparison_chart_widget)

    def setup_search_widget_ui(self):
        """検索ウィジェットのUIをセットアップする。"""
        layout = QVBoxLayout(self.search_widget)
        layout.addWidget(QLabel("検索（未実装）"))

    def setup_skill_gap_widget_ui(self):
        """スキルギャップ分析ウィジェットのUIをセットアップする。"""
        layout = QVBoxLayout(self.skill_gap_widget)
        layout.addWidget(QLabel("スキルギャップ分析（未実装）"))

    def update_comparison_worker_list(self):
        """ワーカー比較リストを更新する。"""
        self.comparison_list.clear()
        workers = self.data_manager.get_all_workers()
        for worker in workers:
            self.comparison_list.addItem(worker['name'])

    def update_comparison_chart(self):
        """選択されたワーカーの比較チャートを更新する。"""
        selected_workers = [item.text() for item in self.comparison_list.selectedItems()]
        all_categories = self.get_categories_from_db()
        data_to_plot = []

        for worker_name in selected_workers:
            worker = self.data_manager.get_worker_by_name(worker_name)
            if worker:
                skill_levels = worker['skill_levels'][:len(all_categories)]
                skill_levels += [1] * (len(all_categories) - len(skill_levels))
                data_to_plot.append(skill_levels)
        
        if data_to_plot: # 追加
           self.comparison_chart_widget.update_comparison_chart(data_to_plot, all_categories, selected_workers)
    def on_worker_selected(self, worker_name):
        """ワーカーが選択されたときの処理。"""
        self.selected_worker = worker_name
        self.update_comparison_worker_list()

    def new_worker(self):
        """新しいワーカーが追加されたときの処理。"""
        self.selected_worker = None
        self.update_comparison_worker_list()