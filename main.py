import bs4
import time
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
        for food in f_facts:
            food["Category"] = cat_name
            foods_df = foods_df.append(food)
    return foods_df


def food_facts(food: bs4.element.Tag) -> list:
    """Assembles the nutritional information for a particular food"""
    name = food.next.next.contents[0].strip(" ")
    base_url = r"https://fastfoodnutrition.org"
    urls = [food.find(attrs={"class": "listlink"}).attrs["href"]]
    table_exists = True
    try:
        food_nutrition = [food_info(urls[0]).transpose()]
    except ValueError:
        food = food.find(attrs={"class": "listlink"}).contents
        name = food[0]
        cals = food[1].contents[1].strip(" calories")
        food_nutrition = [pd.DataFrame(data=[[name, cals]], columns=["Food", "Calories"], index=["Value"])]
        table_exists = False
    if table_exists and food_nutrition[0].size <= 6:
        url = base_url + urls[0]
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0"}
        r = requests.get(url, headers=headers)
        options_soup = BeautifulSoup(r.text, 'html.parser')
        options = options_soup.find_all(attrs={"class": "stub_box"})
        urls = [o.attrs['href'] for o in options]
        food_nutrition = [food_info(link).transpose() for link in urls]
    for i, f_info in enumerate(food_nutrition):
        f_name = name
        f_name += ", " + urls[i].split("/")[-1] if len(food_nutrition) > 1 else ""
        f_info["Food"] = f_name
        f_info["URL"] = base_url + urls[i]
    print("\t\t", name)
    return food_nutrition


def food_info(food_url: str) -> pd.DataFrame:
    """Fetches the nutritional details for a food, given it's URL"""
    url = r"https://fastfoodnutrition.org" + food_url
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0"}
    r = requests.get(url, headers=headers)
    try:
        df = pd.read_html(r.text)[0]
    except ValueError:
        raise ValueError("No Nutritional Information")
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
    rebuild = True
    if rebuild:
        print("Initializing...")
        start = time.time()
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

        # Final Cleanup: resetting index and re-ordering columns
        dataset = dataset.reset_index().drop("index", axis=1)
        cols = ['Restaurant', 'Category', 'Food', 'Serving Size',
                'Calories From Fat', 'Calories', 'Total Fat', 'Saturated Fat', 'Trans Fat',
                'Cholesterol', 'Sodium', 'Total Carbohydrates', 'Dietary Fiber', 'Sugars', 'Protein',
                'Total Fat %', 'Saturated Fat %', 'Cholesterol %', 'Sodium %', 'Total Carbohydrates %',
                'Dietary Fiber %', 'Protein %', 'Vitamin A %', 'URL']
        dataset = dataset.reindex(columns=cols)
        print("Saving...")
        dataset.to_excel("Nutritional Facts.xlsx")
        print(f"Finished in {time.time() - start} seconds!")
    else:
        dataset = pd.read_excel("Nutritional Facts.xlsx")

    return 0


if __name__ == "__main__":
    main()
