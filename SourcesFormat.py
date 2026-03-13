text = """
▪ قناة ليندا عملي
https://t.me/+6ipyXfEfn6s3NzE8
▪ قناة ليندا نظري
https://t.me/+cuPLyJedoXBhNWY0
"""

result = " || ".join(line.strip() for line in text.splitlines() if line.strip())
print(result)