from scrape import run
from pandas import DataFrame


def terms_test():
    terms = ["apple", "banana", "carrot", "dragonfruit", "edamame", "fennel", "ginger"]
    df = DataFrame([{"english":term, "chinese":""} for term in terms])
    run(termlist=df)

if __name__ == "__main__":
    terms_test()