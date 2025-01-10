from PyQt6.QtWidgets import QWidget, QVBoxLayout
from src.chart.mpl_chart_widget import MplChartWidget
from src.data.data_manager import DataManager
import matplotlib.pyplot as plt
import numpy as np

class OverallTab(QWidget):
    def __init__(self, data_manager, categories):
        super().__init__()
        self.data_manager = data_manager
        self.categories = categories
        self.chart = MplChartWidget()
        self.pie_chart = MplChartWidget()

        layout = QVBoxLayout(self)
        layout.addWidget(self.chart)
        layout.addWidget(self.pie_chart)

    def update_chart(self):
        """全ワーカーのデータを集約してレーダーチャートと円グラフを更新する"""
        all_workers = self.data_manager.get_all_workers()
        if all_workers:
            # 全ワーカーのスキルレベルを集約
            aggregated_skill_levels = [0] * len(self.categories)
            for worker in all_workers:
                for i, level in enumerate(worker['skill_levels']):
                    aggregated_skill_levels[i] += level

            # 平均値を計算
            num_workers = len(all_workers)
            average_skill_levels = [level / num_workers if num_workers > 0 else 0 for level in aggregated_skill_levels]

            # レーダーチャートを更新
            self.chart.plot_radar_chart(average_skill_levels, self.categories, "全ワーカーの平均スキルレベル")

            # 円グラフを更新
            self.update_pie_chart(average_skill_levels)
        else:
            print("No worker data available to update the chart.")

    def update_pie_chart(self, skill_levels):
        """スキルレベルの割合を円グラフで表示する"""
        labels = ['Level 1', 'Level 2', 'Level 3', 'Level 4', 'Level 5']

        # 各レベルの合計値を計算
        level_counts = [0] * 5
        for level in skill_levels:
            level_counts[int(level) - 1] += 1

        # 0の要素を取り除く
        non_zero_levels = [(label, count) for label, count in zip(labels, level_counts) if count > 0]
        labels, level_counts = zip(*non_zero_levels) if non_zero_levels else ([], [])

        # 円グラフを描画
        if labels:
            self.pie_chart.figure.clear()
            ax = self.pie_chart.figure.add_subplot(111)

            # レーダーチャートの半径を取得して、円グラフのサイズを調整
            radar_radius = self.chart.ax.get_ylim()[1]
            pie_radius = radar_radius * 0.8  # 円グラフを少し小さくする

            # モダンな配色を使用 (例: https://coolors.co/ から選択)
            colors = ['#264653', '#2a9d8f', '#e9c46a', '#f4a261', '#e76f51']

            wedges, texts, autotexts = ax.pie(
                level_counts,
                labels=labels,
                autopct='%1.1f%%',
                startangle=140,
                radius=pie_radius,  # サイズ調整
                colors=colors,  # 配色設定
            )

            # タイトル追加
            ax.set_title("スキルレベル分布", pad=20, fontdict={'fontsize': 12, 'fontweight': 'bold'})

            ax.axis('equal')
            self.pie_chart.canvas.draw()
        else:
            print("No data to display in pie chart.")

    def on_worker_selected(self, worker_name):
        """ワーカーが選択されたときに呼び出される (このタブでは使用しない)"""
        self.update_chart()