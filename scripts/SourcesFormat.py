text = """
قناة عبدالله شارح فيها اغلب جزئية الفاينل ونماذج للميد والفاينل 
https://t.me/+5EVA2w8wIgc4YWQ0

• الكتاب || https://drive.google.com/file/d/1fbNEGoTmfgfUsw5jEMmYQdObphK5yxrk/view?usp=drive_li || nk || • قناة تليجرام || https://t.me/joinchat/8ZCyxruirnw4Mzlk || • د.غسان ام القرى || https://youtube.com/playlist?list=PLGqb1w5WKZITfAcpt_q8oUYb1yHtFEgeU || • احمد فتحي || https://youtube.com/playlist?list=PLQkyODvJ8ywv5YjAQ2uC550ZP1ZCIP4yn || • نتالي || https://youtube.com/playlist?list=PLjiyR6nPcbxzv1MHhyxJqXIOyZ8c1Or_D || • اختبارات قديمة البترول || https://faculty.kfupm.edu.sa/COE/mudawar/coe301/201/index.htm || • احمد || https://youtube.com/playlist?list=PLx4bx4MMxLANj6SS0uPlj17BPaXiv61ZR&si=t6DjBkiV3H || 6z_iE5 || • عملي نجود || https://t.me/joinchat/JlOW8KnxqwRiZGFk || • شرح اسمبلي || https://youtube.com/playlist?list=PL5b07qlmA3P6zUdDf-o97ddfpvPFuNa5A&si=Nm0fVp2UqnRYctA || • درايف 23 || https://drive.google.com/drive/folders/1VofUe_1qRC2ROxPmI_F7qjdwiSexgxnd || • درايف 22 || https://drive.google.com/drive/folders/1-UBfoiiVKE3JcfPCXNxx-7U_pkiXwYCQ || • درايف الطالب || https://drive.google.com/drive/folders/1TZu5EogFItySGb3abrfcNs5VekqstQrs
"""
result = " || ".join(line.strip() for line in text.splitlines() if line.strip())
print(result)