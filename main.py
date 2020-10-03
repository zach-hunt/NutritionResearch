import time
import bs4
import requests
import pandas as pd
from bs4 import BeautifulSoup


def get_categories(url: str) -> bs4.element.ResultSet:
    """Each restaurants dishes are grouped into categories such as Sandwiches, Beverages, etc."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0"}
        r = requests.get(url, headers=headers)
    except requests.exceptions.MissingSchema:
        print("The supplied URL is invalid. Please update and run again.")
        raise Exception("InvalidURL")
    soup = BeautifulSoup(r.text, 'html.parser')
    return soup.find_all(attrs={"class": "category"})


def get_foods(category: bs4.element.Tag) -> pd.DataFrame:
    """Fetches all entries within a food category"""
    cat_name = category.a.h2.text
    cat_foods = category.find_all(attrs={"class": "filter_target"})
    foods_df = pd.DataFrame()
    print("\t", cat_name)
    for food in cat_foods:
        f_facts = food_facts(food)
        f_facts["Category"] = cat_name
        foods_df = foods_df.append(f_facts)
    return foods_df


def food_facts(food: bs4.element.Tag) -> pd.DataFrame:
    """Assembles the nutritional information for a particular food"""
    name = food.next.next.contents[0].strip(" ")
    url = food.find(attrs={"class": "listlink"}).attrs["href"]
    food_nutrition = food_info(url).transpose()
    food_nutrition["Food"] = name
    food_nutrition["URL"] = url
    print("\t\t", name)
    return food_nutrition


def food_info(food_url: str) -> pd.DataFrame:
    """Fetches the nutritional details for a food, given it's URL"""
    url = r"https://fastfoodnutrition.org" + food_url
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0"}
    r = requests.get(url, headers=headers)
    df = pd.read_html(r.text)[0]
    df.index = df[0]
    df = df.loc[df.index.dropna()]
    percents = df.drop([0, 1], axis=1)
    df.drop([0, 2], axis=1, inplace=True)
    df.columns = ["Values"]
    df.dropna(how="any", inplace=True)
    for entry, value in percents.iterrows():
        if not value.isnull().iloc[0] and "%" in value.iloc[0]:
            new_entry = pd.Series(name=f"{entry} %", index=["Values"], data=value.iloc[0])
            df = df.append(new_entry)

    df.index.name = "Nutrient"
    return df


def main():
    start = time.time()
    print("Initializing...")
    base_url = r"https://fastfoodnutrition.org/"
    with open("restaurants.txt") as r:
        restaurants = {(l := line.split(","))[0]: base_url + l[1].strip("\n") for line in r.readlines()}

    print("Downloading...")
    dataset = pd.DataFrame()
    for restaurant, url in restaurants.items():
        print(restaurant)
        categories = get_categories(url)
        for cat in categories:
            foods = get_foods(cat)
            foods["Restaurant"] = restaurant
            dataset = dataset.append(foods)
        if restaurant == "Arby\'s":
            break

    print("Saving...")
    dataset.to_excel("Nutritional Facts.xlsx")

    print(f"Finished in {time.time() - start} seconds!")
    return 0


if __name__ == "__main__":
    main()
