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
import logging

logger = logging.getLogger(__name__)

class PdfExporter:
    def __init__(self):
        logger.debug("PdfExporter.__init__ called")
        self.output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'output')
        self.setup_font()
        logger.debug("PdfExporter.__init__ finished")

    def setup_font(self):
        logger.debug("PdfExporter.setup_font called")
        font_path = os.path.join(
            os.path.dirname(__file__),
            '../resources/fonts/ZenKakuGothicNew-Medium.ttf'
        )
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('ZenKakuGothicNew-Medium', font_path))
                self.font_name = "ZenKakuGothicNew-Medium"
                logger.debug(f"--- PdfExporter: setup_font: Font registered successfully: {self.font_name}")
            except Exception as e:
                logger.error(f"Font registration error: {e}, using default font.")
                self.font_name = "Helvetica"
        else:
            logger.error(f"Font file not found: {font_path}, using default font.")
            self.font_name = "Helvetica"
        logger.debug("PdfExporter.setup_font finished")

    def export_to_pdf(self, worker_data, filepath, output_folder):
        logger.debug(f"PdfExporter.export_to_pdf called, filepath: {filepath}")
        full_filepath = os.path.join(output_folder, filepath)
        logger.debug(f"PdfExporter.export_to_pdf: full_filepath = {full_filepath}")
        # A4横のキャンバスを作成
        c = None
        try:
            c = canvas.Canvas(full_filepath, pagesize=landscape(A4))
            width, height = landscape(A4)

            # ページ背景を白に設定
            c.setFillColor(colors.white)
            c.rect(0, 0, width, height, stroke=0, fill=1)
            c.setFillColor(colors.black)  # 文字や線の色を設定

            # レイアウト設定
            margin = 0.5 * inch
            frame_width = (width - 2.5 * margin) / 4  # 4つのフレームを配置
            frame_height = (height - 3 * margin) / 2  # 2行に配置
            chart_radius = frame_height * 0.25  # チャートの半径

            x_positions = [0.8*margin, 0.8*margin + frame_width, 0.8*margin + 2 * frame_width, 0.8*margin + 3 * frame_width]
            y_positions = [height - margin - frame_height, height - 2 * margin - 2 * frame_height]

            for index, (name, worker) in enumerate(worker_data.items()):
                if index // 8 != 0:  # ページ分割を削除
                    continue
                row = index % 4
                col = index // 4
                x = x_positions[row]
                y = y_positions[col]

                logger.debug(f"PdfExporter.export_to_pdf: Processing worker: {name}")

                # 枠の描画
                self.draw_frame(c, x, y, frame_width, frame_height)

                # チャートの中心座標を計算
                center_x = x + frame_width / 2
                center_y = y + frame_height / 2 + chart_radius * 0.5  # チャートを上にずらす

                if not worker.categories or not worker.skill_levels:
                    logger.warning(f"Skipping chart for {name}: Missing categories or skill levels.")
                    continue
                if len(worker.skill_levels) != len(worker.categories):
                    logger.error(f"Skipping chart for {name}: Mismatched lengths (skills: {len(worker.skill_levels)}, categories: {len(worker.categories)}).")
                    continue

                # レーダーチャートを描画
                self.draw_radar_chart(c, center_x, center_y, chart_radius, worker.categories, worker.skill_levels, name)

                # チャートと名前の間に線を描画
                line_y = y + frame_height * 0.25  # 線を少し上に配置
                c.setStrokeColor(colors.black)
                c.setLineWidth(1)
                c.line(x, line_y, x + frame_width, line_y)

                # 名前の描画位置を調整
                try:
                    c.setFont(self.font_name, 8)
                except Exception as e:
                    logger.error(f"--- PdfExporter: draw_worker_name: Error setting font: {e}")
                    c.setFont("Helvetica", 8)
                name_width = c.stringWidth(name, self.font_name, 8)
                name_height = c.stringWidth("Ay", self.font_name, 8)  # 修正: "Ay"で高さを推定
                name_x = center_x - name_width / 2
                name_y = line_y - name_height * 1.5  # 修正: 名前が枠内に収まるように調整
                c.drawString(name_x, name_y, name)

                if (index + 1) % 8 == 0:
                    c.showPage()
                    # 新しいページも白背景に設定
                    c.setFillColor(colors.white)
                    c.rect(0, 0, width, height, stroke=0, fill=1)
                    c.setFillColor(colors.black)
                    logger.debug("PdfExporter.export_to_pdf: New page added")

            if c:
                c.save()
                if os.path.exists(full_filepath):
                    logger.debug(f"PdfExporter.export_to_pdf: PDF saved to {full_filepath}")
                    logger.debug("PdfExporter.export_to_pdf finished")
                    return full_filepath
                else:
                     logger.error(f"PdfExporter.export_to_pdf: Failed to save PDF file. , file path is: {full_filepath}")
                     return None
        except Exception as e:
            logger.error(f"PdfExporter.export_to_pdf: Canvas Creation Error {e}, file path is: {full_filepath}")
            return None


    def draw_frame(self, c, x, y, width, height):
        """指定された位置とサイズで枠を描画する"""
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.rect(x, y, width, height)

    def draw_worker_name(self, c, name, center_x, line_y):
        """ワーカー名の描画 (修正)"""
        try:
            c.setFont(self.font_name, 8)
        except Exception as e:
            logger.error(f"--- PdfExporter: draw_worker_name: Error setting font: {e}")
            c.setFont("Helvetica", 8)

        name_width = c.stringWidth(name, self.font_name, 8)
        name_height = c.stringWidth("Ay", self.font_name, 8)  # 修正: "Ay"で高さを推定

        name_x = center_x - name_width / 2
        name_y = line_y - name_height * 1.5  # 修正: 名前が枠内に収まるように調整

        c.drawString(name_x, name_y, name)

    def draw_radar_chart(self, c, center_x, center_y, radius, categories, data, name):
        """reportlabを使用してレーダーチャートを描画する"""
        logger.debug(f"Drawing radar chart for: {name}")
        if not categories or not data or len(categories) != len(data):
            logger.error(f"Invalid data for {name}: categories and skill levels must match.")
            return

        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        angles += angles[:1]
        data += data[:1]

        # スケールを描画 (円と軸)
        c.setLineWidth(0.5)
        c.setStrokeColor(colors.black)
        for i in range(1, 5):
            c.circle(center_x, center_y, radius * i / 4, stroke=1, fill=0)
        for angle in angles[:-1]:
            x = center_x + radius * np.cos(angle)
            y = center_y + radius * np.sin(angle)
            c.line(center_x, center_y, x, y)

        # データポイントを計算
        points = []
        for i, d in enumerate(data):
            scaled_radius = radius * d / 4
            angle = angles[i]
            x = center_x + scaled_radius * np.cos(angle)
            y = center_y + scaled_radius * np.sin(angle)
            points.append((x, y))

        # 塗りつぶしと輪郭の描画
        fill_color = colors.Color(0, 0, 1, alpha=0.25)
        c.setFillColor(fill_color)
        c.setStrokeColor(colors.blue)
        c.setLineWidth(2)
        for i in range(len(points) - 1):
            c.line(points[i][0], points[i][1], points[i+1][0], points[i+1][1])
        c.line(points[-1][0], points[-1][1], points[0][0], points[0][1])  # 最後の点と最初の点を結ぶ

        # カテゴリラベルを追加
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
         line_height = 10  # 行の高さを設定
         total_height = len(text_lines) * line_height

         text_start_y = label_y - (total_height / 2) + y_offset

         for j, line in enumerate(text_lines):
            line_width = c.stringWidth(line, self.font_name, 6)
            line_x = label_x - line_width / 2 + x_offset
            line_y = text_start_y + j * line_height
            logger.debug(f"--- PdfExporter: draw_label: Drawing text: '{line}' at ({line_x}, {line_y}), x_offset: {x_offset}, y_offset: {y_offset}")
            c.drawString(line_x, line_y, line)


    def calculate_label_offset(self, angle):
        """ラベルのオフセットを計算"""
        angle_deg = np.degrees(angle)
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