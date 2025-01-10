from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, String, Polygon, Line
from reportlab.graphics import renderPDF
from reportlab.lib import colors
import os
import numpy as np
from datetime import datetime

class PdfExporter:
    def __init__(self, font_path=None, config=None):
        self.config = config if config else {}
        self.default_font_path = os.path.join(
            os.path.dirname(__file__),
            '..', 'resources', 'fonts', 'ZenKakuGothicNew-Medium.ttf'
        )
        self.font_path = font_path or self.config.get('font_path', self.default_font_path)
        self.setup_font()

        # 設定から値を取得、ない場合はデフォルト値を適用
        self.margin = self.config.get('margin', 0.5) * inch
        self.page_size = landscape(A4)
        self.frame_width = self.config.get('frame_width', (self.page_size[0] - 2.5 * self.margin) / 4)
        self.frame_height = self.config.get('frame_height', (self.page_size[1] - 3 * self.margin) / 2)
        self.chart_radius = self.config.get('chart_radius', self.frame_height * 0.25)

    def setup_font(self):
        """フォントの設定を行う。"""
        print(f"--- PdfExporter: setup_font: Font path: {self.font_path}")
        try:
            pdfmetrics.registerFont(TTFont('ZenKakuGothicNew-Medium', self.font_path))
            self.font_name = "ZenKakuGothicNew-Medium"
            print(f"--- PdfExporter: setup_font: Font registered successfully: {self.font_name}")
        except Exception as e:
            print(f"Font registration error: {e}, using default font.")
            self.font_name = "Helvetica"

        # フォント登録確認
        try:
            pdfmetrics.getFont(self.font_name)
            print(f"--- PdfExporter: setup_font: Font '{self.font_name}' is available.")
        except Exception as e:
            print(f"--- PdfExporter: setup_font: Font '{self.font_name}' is not available: {e}")
            self.font_name = "Helvetica"  # デフォルトフォントに戻す
            print(f"--- PdfExporter: setup_font: Using default font: {self.font_name}")

    def export_to_pdf(self, worker_data, filepath):
        """ワーカーデータをPDFファイルに出力する。"""
        c = canvas.Canvas(filepath, pagesize=self.page_size)
        width, height = self.page_size

        # ページ背景を白に設定
        c.setFillColor(colors.white)
        c.rect(0, 0, width, height, stroke=0, fill=1)
        c.setFillColor(colors.black)  # 文字や線の色を設定

        x_positions = [0.8*self.margin + i * self.frame_width for i in range(4)]
        y_positions = [height - self.margin - self.frame_height, height - 2 * self.margin - 2 * self.frame_height]

        # ページ数計算 (修正)
        num_workers = len(worker_data)
        num_pages = (num_workers + 7) // 8  # 8人ごとにページを追加

        for page in range(num_pages):
            for index, (name, worker) in enumerate(worker_data.items()):
                if index // 8 != page:
                    continue  # 現在のページに該当しないデータはスキップ

                row = index % 4
                col = (index // 4) % 2
                x = x_positions[row]
                y = y_positions[col]

                # 枠の描画
                self.draw_frame(c, x, y, self.frame_width, self.frame_height)

                # チャートの中心座標を計算
                center_x = x + self.frame_width / 2
                center_y = y + self.frame_height / 2 + self.chart_radius * 0.5

                if not worker.categories or not worker.skill_levels:
                    print(f"Skipping chart for {name}: Missing categories or skill levels.")
                    continue
                if len(worker.skill_levels) != len(worker.categories):
                    print(f"Skipping chart for {name}: Mismatched lengths (skills: {len(worker.skill_levels)}, categories: {len(worker.categories)}).")
                    continue

                # レーダーチャートを描画
                try:
                    self.draw_radar_chart(c, center_x, center_y, self.chart_radius, worker.categories, worker.skill_levels, name)
                except Exception as e:
                    print(f"Error creating chart for {name}: {e}")
                    continue

                # チャートと名前の間に線を描画
                line_y = y + self.frame_height * 0.25
                c.setStrokeColor(colors.black)
                c.setLineWidth(1)
                c.line(x, line_y, x + self.frame_width, line_y)

                # 名前の描画 (修正)
                self.draw_worker_name(c, name, center_x, line_y)

            # 最後のページ以外はページを追加
            if page < num_pages - 1:
                c.showPage()
                c.setFillColor(colors.white)
                c.rect(0, 0, width, height, stroke=0, fill=1)
                c.setFillColor(colors.black)

        c.save()
        return filepath

    def draw_frame(self, c, x, y, width, height):
        """枠線の描画"""
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.rect(x, y, width, height)

    def draw_worker_name(self, c, name, center_x, line_y):
        """ワーカー名の描画 (修正)"""
        try:
            c.setFont(self.font_name, 8)
        except Exception as e:
            print(f"--- PdfExporter: draw_worker_name: Error setting font: {e}")
            c.setFont("Helvetica", 8)

        name_width = c.stringWidth(name, self.font_name, 8)
        name_height = c.stringWidth("Ay", self.font_name, 8)  # 修正: "Ay"で高さを推定

        name_x = center_x - name_width / 2
        name_y = line_y - name_height * 1.5  # 修正: 名前が枠内に収まるように調整

        c.drawString(name_x, name_y, name)

    def draw_radar_chart(self, c, center_x, center_y, radius, categories, data, name):
        """レーダーチャートの描画"""
        print(f"--- PdfExporter: draw_radar_chart: Drawing chart for worker: {name}")
        if not categories or not data or len(categories) != len(data):
            print(f"Invalid data for {name}: categories and skill levels must match.")
            return

        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        angles += angles[:1]
        data += data[:1]

        # スケールを描画 (円と軸)
        self.draw_chart_scale(c, center_x, center_y, radius)

        # データポイントを計算
        points = self.calculate_data_points(data, angles, center_x, center_y, radius)

        # 塗りつぶしと輪郭の描画
        self.draw_chart_polygon(c, points)

        # カテゴリラベルを追加
        self.draw_category_labels(c, categories, angles, center_x, center_y, radius)

    def draw_chart_scale(self, c, center_x, center_y, radius):
        """チャートのスケール（円と軸）を描画"""
        c.setLineWidth(0.5)
        c.setStrokeColor(colors.black)
        for i in range(1, 5):
            c.circle(center_x, center_y, radius * i / 4, stroke=1, fill=0)
        angles = np.linspace(0, 2 * np.pi, 15, endpoint=False).tolist() # 15は仮の数値
        for angle in angles:
            x = center_x + radius * np.cos(angle)
            y = center_y + radius * np.sin(angle)
            c.line(center_x, center_y, x, y)

    def calculate_data_points(self, data, angles, center_x, center_y, radius):
        """データポイントを計算"""
        points = []
        for i, d in enumerate(data):
            scaled_radius = radius * d / 4
            angle = angles[i]
            x = center_x + scaled_radius * np.cos(angle)
            y = center_y + scaled_radius * np.sin(angle)
            points.append((x, y))
        return points

    def draw_chart_polygon(self, c, points):
        """チャートのポリゴンを描画"""
        fill_color = colors.Color(0, 0, 1, alpha=0.25)
        c.setFillColor(fill_color)
        c.setStrokeColor(colors.blue)
        c.setLineWidth(2)
        for i in range(len(points) - 1):
            c.line(points[i][0], points[i][1], points[i+1][0], points[i+1][1])
        c.line(points[-1][0], points[-1][1], points[0][0], points[0][1])

    def draw_category_labels(self, c, categories, angles, center_x, center_y, radius):
        """カテゴリラベルを描画"""
        label_radius = radius * 1.15
        try:
            c.setFont(self.font_name, 6)
            print(f"--- PdfExporter: draw_category_labels: Font set to: {self.font_name}, size: 6")
        except Exception as e:
            print(f"--- PdfExporter: draw_category_labels: Error setting font: {e}")
            c.setFont("Helvetica", 6)

        c.setFillColor(colors.black)
        line_color = colors.Color(0.5, 0.5, 0.5, alpha=0.5)

        for i, category in enumerate(categories):
            angle = angles[i]
            label_x = center_x + label_radius * np.cos(angle)
            label_y = center_y + label_radius * np.sin(angle)
            vertex_x = center_x + radius * np.cos(angle)
            vertex_y = center_y + radius * np.sin(angle)

            # 補助線を描画
            c.setStrokeColor(line_color)
            c.setLineWidth(0.3)
            c.line(vertex_x, vertex_y, label_x, label_y)

            # ラベルを描画
            self.draw_label(c, category, label_x, label_y, angle)

    def draw_label(self, c, label, label_x, label_y, angle):
        """ラベルの描画と位置調整"""
        label = label.replace('ウォータースパイダー', 'ウォーター\nスパイダー').replace('エブリラベラー', 'エブリ\nラベラー')
        text_lines = label.split('\n')

        # ラベルの位置を調整
        x_offset, y_offset = self.calculate_label_offset(angle)

        c.setFillColor(colors.black)
        for j, line in enumerate(text_lines):
            line_width = c.stringWidth(line, self.font_name, 6)
            line_x = label_x - line_width / 2 + x_offset
            line_y = label_y + (len(text_lines) - 1 - j) * 10 - 5 / 2 + y_offset
            print(f"--- PdfExporter: draw_label: Drawing text: '{line}' at ({line_x}, {line_y}) with font: {self.font_name}")
            c.drawString(line_x, line_y, line)

    def calculate_label_offset(self, angle):
        """ラベルのオフセットを計算"""
        angle_deg = angle * 180 / np.pi
        if 0 <= angle_deg < 25 or 335 <= angle_deg <= 360:
            return 5, -5
        elif 25 <= angle_deg < 65:
            return 3, 3
        elif 65 <= angle_deg < 115:
            return 0, 5
        elif 115 <= angle_deg < 155:
            return -3, 3
        elif 155 <= angle_deg < 205:
            return -5, -5
        elif 205 <= angle_deg < 245:
            return -3, -5
        elif 245 <= angle_deg < 295:
            return 0, -10
        elif 295 <= angle_deg < 335:
            return 3, -5
        else:
            return 0, 0