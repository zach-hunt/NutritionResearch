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


def get_foods(category: bs4.element.Tag, log_file=None) -> pd.DataFrame:
    """Fetches all entries within a food category"""
    cat_name = category.a.h2.text
    cat_foods = category.find_all(attrs={"class": "filter_target"})
    foods_df = pd.DataFrame()
    log(cat_name, "Category", log_file)
    for food in cat_foods:
        f_facts = food_facts(food, log_file)
        for sub_food in f_facts:
            sub_food["Category"] = cat_name
            foods_df = foods_df.append(sub_food)
    return foods_df


def food_facts(food: bs4.element.Tag, log_file=None) -> list:
    """Assembles the nutritional information for a particular food"""
    # TODO: This is where the None fails for Starbucks (milk) and McDonalds (pictures)
    try:
        name = food.next.next.contents[0].strip(" ")
    except TypeError:
        raise AttributeError("These foods have pictures and need to be special-cased")
    base_url = r"https://fastfoodnutrition.org"
    urls = [food.find(attrs={"class": "listlink"}).attrs["href"]]
    table_exists = True
    try:
        food_nutrition = [food_info(urls[0]).transpose()]
    except ValueError:
        food_c = food.find(attrs={"class": "listlink"}).contents
        name = food_c[0]
        cals = food_c[1].contents[1].strip(" calories")
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
    log(name, "Food", log_file)
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


def get_restaurants(base_url: str, source_filename) -> dict:
    with open(source_filename, "r") as r:
        restaurants = {(splitline := line.split(","))[0]: base_url + splitline[1].strip("\n") for line in r.readlines()}
    return restaurants


def star_drink_facts(food_info: bs4.element.Tag) -> pd.DataFrame:
    drinks = pd.DataFrame()
    try:
        for food in food_facts(food_info):
            drinks = drinks.append(food)
    except TypeError:
        base_url = "https://fastfoodnutrition.org"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0"}
        url = food_info.find(attrs={"class": "listlink"}).attrs["href"]
        r = requests.get(base_url + url, headers=headers)
        milk_soup = BeautifulSoup(r.text, 'html.parser')
        links = [milk.attrs['href'] for milk in milk_soup.find_all(attrs={"class": "large_list_item"})]
        for link in links:
            r = requests.get(base_url + link, headers=headers)
            drink_soup = BeautifulSoup(r.text, 'html.parser')
            # FIXME: Clean this up so food_facts actually receives food text!
            for drink in food_facts(drink_soup):
                drinks = drinks.append(drink)

    return drinks


def starbucks(url: str, log_file=None) -> pd.DataFrame:
    categories = get_categories(url)
    items = pd.DataFrame()
    for cat in categories:
        cat_name = cat.a.h2.text
        cat_foods = cat.find_all(attrs={"class": "filter_target"})
        log(cat_name, "Category", log_file)
        for food in cat_foods:
            f_facts = star_drink_facts(food)
            f_facts.insert(f_facts.shape[1], "Category", cat_name)
            items = items.append(f_facts)
        items["Restaurant"] = "Starbucks"
    return items


def mc_food_info(url: str):
    """Fetches the nutritional details for a McDonald's food item, given it's URL"""
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
            new_entry = pd.Series(name=f"{entry} Pct", index=["Values"], data=value.iloc[0])
            df = df.append(new_entry)

    df.index.name = "Nutrient"
    food_name = pd.Series(BeautifulSoup(r.text, features="lxml").h2.text.strip(" Calories"), ["Values"], name="Food")
    df = df.append(food_name)
    return df


def mcdonalds(url: str, log_file=None) -> pd.DataFrame:
    categories = get_categories(url)
    items = pd.DataFrame()
    base_url = r"https://fastfoodnutrition.org"
    for cat in categories:
        cat_name = cat.a.h2.text
        cat_foods = cat.find_all(attrs={"class": "filter_target"})
        log(cat_name, "Category", log_file)
        for food in cat_foods:
            if len(food.contents[0].attrs) == 1:
                url = food.contents[0].contents[0].attrs["href"]
            else:
                url = food.contents[0].attrs["href"]
            food_url = base_url + url
            f_facts = mc_food_info(food_url)
            if len(f_facts) < 10:  # Subcategories
                headers = {"User-Agent":
                           "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0"}
                r = requests.get(food_url, headers=headers)
                soup = BeautifulSoup(r.text, features='lxml')
                options = soup.find_all(attrs={"class": "stub_box"})
                urls = [base_url + option.attrs["href"] for option in options]
                f_facts = pd.DataFrame()
                for url in urls:
                    new_f_facts = mc_food_info(url).T
                    new_f_facts["URL"] = url
                    f_facts = f_facts.append(new_f_facts)
            else:
                f_facts = f_facts.T
                f_facts["URL"] = food_url
                # f_facts["Food"] = f_name  # TODO: Implement inside mc_food_info()
            f_facts.insert(f_facts.shape[1], "Category", cat_name)
            items = items.append(f_facts)
    items["Restaurant"] = "McDonald's"
    if "Amount Per Serving" in items.columns:
        items.drop(["Amount Per Serving"], axis=1, inplace=True)
    return items


def build_dataset(restaurants: dict, log_filename=None) -> pd.DataFrame:
    if log_filename:
        log_file = open(log_filename, "w")
    else:
        log_file = None
    dataset = pd.DataFrame()
    skips = {}
    special_cases = {"Chick-fil-A": mcdonalds, "McDonald's": mcdonalds}  # "Starbucks": starbucks}
    for restaurant, url in restaurants.items():
        if restaurant[0] == "#":
            skips.update({restaurant: url})
            continue
        else:
            continue
        log(restaurant, "Restaurant", log_file)
        print(restaurant)
        categories = get_categories(url)
        for cat in categories:
            foods = get_foods(cat, log_file)
            foods["Restaurant"] = restaurant
            dataset = dataset.append(foods)
    for restaurant, url in skips.items():
        if restaurant[1:] in special_cases.keys():
            special_row = special_cases[restaurant[1:]](url, log_file)
            special_row.rename(columns={col: col.replace("Pct", "%") for col in special_row.columns}, inplace=True)
            dataset = dataset.append(special_row)
        else:
            log(f"\n\nCannot handle special case {restaurant}: "
                "no function defined in special_cases. Make sure the cases match.", "", log_file)
    if log_filename:
        log_file.close()
    return dataset


def clean_dataset(dataset: pd.DataFrame) -> pd.DataFrame:
    data = dataset.reset_index()
    if "index" in data.columns:
        data.drop("index", axis=1, inplace=True)
    cols = ['Restaurant', 'Category', 'Food', 'Serving Size',
            'Calories From Fat', 'Calories', 'Total Fat', 'Saturated Fat', 'Trans Fat',
            'Cholesterol', 'Sodium', 'Total Carbohydrates', 'Dietary Fiber', 'Sugars', 'Protein',
            'Total Fat %', 'Saturated Fat %', 'Cholesterol %', 'Sodium %', 'Total Carbohydrates %',
            'Dietary Fiber %', 'Protein %', 'Vitamin A %', 'URL']
    data = data.reindex(columns=cols)
    return data


def log(text: str, ttype: str, log_file=None) -> None:
    log_prefixes = {"Restaurant": "### ", "Category": "- ", "Food": "\t* "}
    print_prefixes = {"Restaurant": "", "Category": "\t", "Food": "\t\t"}
    if log_file is None:
        if ttype in print_prefixes.keys():
            print(print_prefixes[ttype] + text)
        else:
            print(text)
    else:
        if ttype in log_prefixes.keys():
            print(log_prefixes[ttype] + text, file=log_file)
        else:
            print(text, file=log_file)


def main(rebuild=False):
    if not rebuild:
        data = pd.read_excel("Nutritional Facts.xlsx")
        return data

    print("Initializing...")
    start = time.time()
    base_url = r"https://fastfoodnutrition.org/"
    filename = "restaurants.txt"
    restaurants = get_restaurants(base_url, filename)

    print("Downloading...")
    dataset = build_dataset(restaurants, "Foods Log.md")

    # Final Cleanup: resetting index and re-ordering columns
    data = clean_dataset(dataset)

    print("Saving...")
    data.to_excel("Nutritional Facts - Specials.xlsx")
    print(f"Finished in {time.time() - start} seconds!")

    return data


if __name__ == "__main__":
    main(True)
