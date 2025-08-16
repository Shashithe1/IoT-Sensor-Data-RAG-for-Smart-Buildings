from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

# Ensure manuals folder exists
os.makedirs("data/manuals", exist_ok=True)

pdf_path = "data/manuals/sample_manual.pdf"

c = canvas.Canvas(pdf_path, pagesize=letter)
width, height = letter

c.setFont("Helvetica-Bold", 16)
c.drawString(72, height - 72, "Pump Maintenance Manual")

c.setFont("Helvetica", 12)
c.drawString(72, height - 120, "Maintenance Procedure for Pumps:")
c.drawString(72, height - 140, "1. Check oil levels and refill if below minimum.")
c.drawString(72, height - 160, "2. Inspect seals and replace if damaged.")
c.drawString(72, height - 180, "3. Measure vibration levels, should not exceed 0.5 mm/s.")
c.drawString(72, height - 200, "4. Clean filters every 30 days.")
c.drawString(72, height - 220, "5. Record maintenance in logbook.")

c.save()

print(f"✅ Dummy manual created at: {pdf_path}")
