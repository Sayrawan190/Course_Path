text = """
》قناة هتان بالتلقرام واغلب الشروحات تلاقيها هناك:  https://t.me/+babLk34AKvRhMGE0  》مصادر زيادة للمادة (اختبارات سابقة، ملفات مفيدة، طبعًا بينضاف ملفات مع الوقت):  https://drive.google.com/drive/folders/1EcH6CbMuuIc-flu1i8X0oPQ_iuQs0T6x  شرح يوتيوب للمادة : || https://youtube.com/playlist?list=PLxIvc-MGOs6ib0oK1z9C46DeKd9rRcSMY&si=s4kblcMs9H3MkDWv
"""

result = " || ".join(line.strip() for line in text.splitlines() if line.strip())
print(result)