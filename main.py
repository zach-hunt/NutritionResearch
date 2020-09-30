import bs4
import requests
import pandas as pd
from bs4 import BeautifulSoup


def get_categories(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0"}
        r = requests.get(url, headers=headers)
    except requests.exceptions.MissingSchema:
        print("The supplied URL is invalid. Please update and run again.")
        raise Exception("InvalidURL")
    soup = BeautifulSoup(r.text, 'html.parser')

    return soup.find_all(attrs={"class": "category"})


def get_foods(category):
    cat_name = category.a.h2.text
    food_cats = category.find_all(attrs={"class": "filter_target"})
    foods = {(food := food_facts(f))["name"]: food["info"] for f in food_cats}
    return {"name": cat_name, "foods": foods}


def food_facts(food):
    info = food.next.next.contents
    name = info[0]
    cals = info[-1].contents[1]
    if type(cals) is bs4.element.NavigableString:
        cals = cals.strip(" calories")
    else:
        cals = ""
    if "-" in cals:
        rng = [int(c) for c in cals.split("-")]
        cal_avg = sum(rng) / 2
    elif not cals:
        cal_avg = -1  # No data available
    else:
        cal_avg = int(cals)
    url = food.find(attrs={"class": "listlink"}).attrs["href"]
    # TODO: Call create_food(url) once implemented
    return {"name": name, "info": {"calories": cal_avg, "url": url}}


def data_to_frame(data):
    base_url = r"https://fastfoodnutrition.org"
    columns = ["Restaurant", "Category", "Item", "URL", "Calories"]
    df = pd.DataFrame(columns=columns)
    for r, cats in data.items():
        for category, items in cats.items():
            for name, info in items.items():
                df = df.append({"Restaurant": r, "Category": category, "Item": name,
                                "URL": base_url + info["url"], "Calories": info["calories"]}, ignore_index=True)
    return df


def main():
    print("Initializing...")
    base_url = r"https://fastfoodnutrition.org/"
    with open("restaurants.txt") as r:
        restaurants = {(l := line.split(","))[0]: base_url + l[1].strip("\n") for line in r.readlines()}

    print("Downloading...")
    dataset = {}
    for restaurant, url in restaurants.items():
        categories = get_categories(url)
        dataset.update({restaurant: {(f := get_foods(cat))["name"]: f["foods"] for cat in categories}})

    print("Saving...")
    df = data_to_frame(dataset)

    df.to_excel("Nutritional Facts.xlsx")

    print("Finished!")
    return 0


if __name__ == "__main__":
    main()
