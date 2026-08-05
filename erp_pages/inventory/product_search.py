from database import get_products


def search_product(keyword):

    print("SEARCH:", keyword)

    products = get_products()

    print("TOTAL:", len(products))


    for p in products:

        print(
            "CHECK:",
            p.get("name"),
            p.get("barcode")
        )


        if str(p.get("barcode")) == str(keyword):
            print("FOUND:", p)
            return p


    print("NOT FOUND")

    return None
