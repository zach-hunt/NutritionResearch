import sys
import pickle
import requests
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
    cals = info[1].contents[1].strip(" calories")  # Left as string because some are ranges
    if "-" in cals:
        rng = [int(c) for c in cals.split("-")]
        cal_avg = sum(rng) / 2
    else:
        cal_avg = int(cals)
    url = food.find(attrs={"class": "listlink"}).attrs["href"]
    # TODO: Call create_food(url) once implemented
    return {"name": name, "info": {"calories": cal_avg, "url": url}}


def main():
    base_url = r"https://fastfoodnutrition.org/"
    with open("restaurants.txt") as r:
        restaurants = {(l := line.split(","))[0]: base_url + l[1] for line in r.readlines()}

    dataset = {}
    for restaurant, url in restaurants.items():
        categories = get_categories(url)
        dataset.update({restaurant: {(f := get_foods(cat))["name"]: f["foods"] for cat in categories}})

    return 0


if __name__ == "__main__":
    main()
