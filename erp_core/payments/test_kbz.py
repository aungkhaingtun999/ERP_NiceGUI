from erp_core.payments.kbz_qr_analyzer import KBZQRAnalyzer


samples = [

"hQZLQlpQYXlhPE8C8FACEFcWCSZ3cjZ9JggQEB+fCAQBAZ8kAzEuMA==F+19fbc3e3e34",

"hQZLQlpQYXlhPE8C8FACEFcWCSZ3cjZ9JggQEB+fCAQBAZ8kAzIuMA==FJ19fbc3ea850=",

"hQZLQlpQYXlhPE8C8FACEFcWCSZ3cjZ9JggQEB+fCAQBAZ8kAzMuMA==FS19fbc3ef275"

]


for qr in samples:

    print("====================")

    result = KBZQRAnalyzer.analyze(qr)

    print(result)