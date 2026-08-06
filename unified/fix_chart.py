"""Quick fix for AnswerFirst AI revenue chart."""
from pathlib import Path

path = Path(r"C:\Users\azelt\answerfirst-ai\unified\app.py")
text = path.read_text()

# 1) Ensure timedelta import exists
if "from datetime import datetime" in text and "timedelta" not in text:
    text = text.replace("from datetime import datetime", "from datetime import datetime, timedelta")

# 2) Find the revenue timeline route block and ensure weekly always emits labels
old_weekly = '''    if period == "weekly":
        monday = now - timedelta(days=now.weekday())
        labels = []
        values = []
        for i in range(5):
            d = monday + timedelta(days=i)
            day_total = 0
            for r in orders:
                if r["created_at"]:
                    try:
                        order_date = datetime.fromisoformat(r["created_at"]).date()
                        if order_date == d.date():
                            day_total += int(r["amount"] or 0)
                    except (ValueError, TypeError):
                        pass
            labels.append(d.strftime("%a"))
            values.append(day_total)'''

new_weekly = '''    if period == "weekly":
        monday = now - timedelta(days=now.weekday())
        labels = ["Mon","Tue","Wed","Thu","Fri"]
        values = [0,0,0,0,0]
        for i in range(5):
            d = monday + timedelta(days=i)
            day_total = 0
            for r in orders:
                if r["created_at"]:
                    try:
                        order_date = datetime.fromisoformat(r["created_at"]).date()
                        if order_date == d.date():
                            day_total += int(r["amount"] or 0)
                    except (ValueError, TypeError):
                        pass
            values[i] = day_total'''

if old_weekly in text:
    text = text.replace(old_weekly, new_weekly)
    print("Replaced weekly block")
else:
    print("Weekly block not found, checking alternate form...")
    if 'if period == "weekly"' in text:
        idx = text.find('if period == "weekly"')
        end = text.find("elif period ==", idx)
        print("Weekly block exists from", idx, "to", end)
        print(text[idx:end])

path.write_text(text)
print("Saved")
