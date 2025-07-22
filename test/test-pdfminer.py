from pdfminer.high_level import extract_text

text = extract_text("data/Bank_Tariff_CN_simplified.pdf", codec="gb18030")
# text = extract_text("docs/Bank_Tarrif_CN_Tranditional.pdf", codec="utf-8")
# text = extract_text("docs/Bank_Tarrif_CN_simplified.pdf")

print(text)