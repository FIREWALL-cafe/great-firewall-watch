from scrape import run
from pandas import DataFrame


def terms_test():
    label = "test"
    # terms = ["apple", "banana", "carrot", "dragonfruit", "edamame", "fennel", "ginger"]
    # terms = ["asparagus", "broccoli"]
    terms = [("hong kong", "香港")]
    # df = DataFrame([{"english": term, "chinese": "test", "label": label} for term in terms])
    df = DataFrame([{"english": en_term, "chinese": cn_term, "label": label} for en_term,cn_term in terms])
    run(termlist=df, shuffle=True)

if __name__ == "__main__":
    terms_test()