from scrape import run
from pandas import DataFrame


def terms_test():
    terms = ["apple", "banana", "carrot", "dragonfruit", "edamame", "fennel", "ginger"]
    # terms = ["asparagus"]
    df = DataFrame([{"english":term, "chinese":"test"} for term in terms])
    run(termlist=df, shuffle=True)

if __name__ == "__main__":
    terms_test()