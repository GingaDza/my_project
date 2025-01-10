from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# フォントの登録
pdfmetrics.registerFont(TTFont('ZenKakuGothicNew-Medium', 'src/ui/resources/fonts/ZenKakuGothicNew-Medium.ttf'))

# PDFの作成
c = canvas.Canvas("japanese_test.pdf")
c.setFont('ZenKakuGothicNew-Medium', 14)
c.drawString(100, 750, "日本語テスト")
c.save()