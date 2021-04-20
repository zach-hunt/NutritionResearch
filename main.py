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


def get_foods(category: bs4.element.Tag, log_file=None, v: bool = True) -> pd.DataFrame:
    """Fetches all entries within a food category"""
    cat_name = category.a.h2.text
    cat_foods = category.find_all(attrs={"class": "filter_target"})
    foods_df = pd.DataFrame()
    log(cat_name, "Category", log_file, v)
    for food in cat_foods:
        f_facts = food_facts(food, log_file, v)
        for sub_food in f_facts:
            sub_food["Category"] = cat_name
            foods_df = foods_df.append(sub_food)
    return foods_df


def food_facts(food: bs4.element.Tag, log_file=None, v: bool = True) -> list:
    """Assembles the nutritional information for a particular food"""
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
    log(name, "Food", log_file, v)
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


def get_restaurants(base_url: str) -> dict:
    url = r"https://fastfoodnutrition.org"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser').find(attrs={"class": "d-lg-block"})
    res_list = list(soup.stripped_strings)[1:]
    restaurants = {res: base_url + res.replace(r"'", "").replace(" ", "-") for res in res_list}
    return restaurants


def star_drink_facts(food_inf: bs4.element.Tag) -> pd.DataFrame:
    drinks = pd.DataFrame()
    try:
        for food in food_facts(food_inf):
            drinks = drinks.append(food)
    except TypeError:
        base_url = "https://fastfoodnutrition.org"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0"}
        url = food_inf.find(attrs={"class": "listlink"}).attrs["href"]
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


def starbucks(url: str, log_file=None, v: bool=True) -> pd.DataFrame:
    # FIXME: Never run because manually skipped in build_dataset because this function doesn't work :)
    categories = get_categories(url)
    items = pd.DataFrame()
    for cat in categories:
        cat_name = cat.a.h2.text
        cat_foods = cat.find_all(attrs={"class": "filter_target"})
        log(cat_name, "Category", log_file, v)
        for food in cat_foods:
            f_facts = star_drink_facts(food)
            f_facts.insert(f_facts.shape[1], "Category", cat_name)
            items = items.append(f_facts)
        items["Restaurant"] = "Starbucks"
    return items


def pic_food_info(url: str, log_file=None, v: bool=True):
    """Fetches the nutritional details for a food item with a picture, given it's URL"""
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
    food_name = BeautifulSoup(r.text, features="lxml").h2.text
    food_name = food_name.replace("Calories", "").strip(" ") if "Calories" in food_name else food_name.strip(" ")
    food_name_series = pd.Series(food_name, ["Values"], name="Food")
    df = df.append(food_name_series)
    if len(df) >= 10:
        log(food_name, "Food", log_file, v)
    return df


def pictured(url: str, log_file=None, v: bool = True) -> pd.DataFrame:
    categories = get_categories(url)
    items = pd.DataFrame()
    base_url = r"https://fastfoodnutrition.org"
    for cat in categories:
        cat_name = cat.a.h2.text
        cat_foods = cat.find_all(attrs={"class": "filter_target"})
        log(cat_name, "Category", log_file, v)
        for food in cat_foods:
            if len(food.contents[0].attrs) == 1:
                url = food.contents[0].contents[0].attrs["href"]
            else:
                url = food.contents[0].attrs["href"]
            food_url = base_url + url
            f_facts = pic_food_info(food_url, log_file)
            if len(f_facts) < 10:  # Subcategories
                headers = {"User-Agent":
                           "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0"}
                r = requests.get(food_url, headers=headers)
                soup = BeautifulSoup(r.text, features='lxml')
                options = soup.find_all(attrs={"class": "stub_box"})
                urls = [base_url + option.attrs["href"] for option in options]
                f_facts = pd.DataFrame()
                for url in urls:
                    new_f_facts = pic_food_info(url, log_file, v).T
                    new_f_facts["URL"] = url
                    f_facts = f_facts.append(new_f_facts)
            else:
                f_facts = f_facts.T
                f_facts["URL"] = food_url
            f_facts.insert(f_facts.shape[1], "Category", cat_name)
            items = items.append(f_facts)
    if "Amount Per Serving" in items.columns:
        items.drop(["Amount Per Serving"], axis=1, inplace=True)
    return items


def build_dataset(restaurants: dict, log_filename=None, v: bool = True) -> pd.DataFrame:
    if log_filename:
        log_file = open(log_filename, "w")
    else:
        log_file = None
    dataset = pd.DataFrame()
    skips = {}
    special_cases = {"Chick-fil-A": pictured, "McDonald's": pictured, "Starbucks": starbucks}
    for restaurant, url in restaurants.items():
        if restaurant in special_cases.keys():
            skips.update({restaurant: url})
            continue
        log(restaurant, "Restaurant", log_file, v)
        categories = get_categories(url)
        for cat in categories:
            foods = get_foods(cat, log_file, v)
            foods["Restaurant"] = restaurant
            dataset = dataset.append(foods)
    for restaurant, url in skips.items():
        if restaurant == "Starbucks":  # TODO: Remove if / once the Starbucks function works
            log(f"\n\nCannot handle special case {restaurant}: "
                "no function defined in special_cases. Make sure the cases match.", "", log_file)
            continue

        log(restaurant, "Restaurant", log_file, v)
        special_row = special_cases[restaurant](url, log_file, v)
        special_row.rename(columns={col: col.replace("Pct", "%") for col in special_row.columns}, inplace=True)
        special_row["Restaurant"] = restaurant
        dataset = dataset.append(special_row)

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
            'Dietary Fiber %', 'Protein %', 'Vitamin A %', 'Vitamin C %', 'URL']
    data = data.reindex(columns=cols)

    return data


def log(text: str, ttype: str, log_file=None, log_console=True) -> None:
    log_prefixes = {"Restaurant": "### ", "Category": "- ", "Food": "\t* "}
    print_prefixes = {"Restaurant": "", "Category": "\t", "Food": "\t\t"}
    if log_file is None or log_console:
        if ttype in print_prefixes.keys():
            print(print_prefixes[ttype] + text)
        else:
            print(text)
    if log_file is not None:
        if ttype in log_prefixes.keys():
            print(log_prefixes[ttype] + text, file=log_file)
        else:
            print(text, file=log_file)


def main(rebuild=False):
    if not rebuild:
        data = pd.read_excel("Nutritional Facts - Raw Data.xlsx")
        return data

    print("Initializing...")
    start = time.time()
    base_url = r"https://fastfoodnutrition.org/"
    restaurants = get_restaurants(base_url)

    print("Downloading...")
    dataset = build_dataset(restaurants, "./References/Foods Log.md", v=True)

    # Final Cleanup: resetting index and re-ordering columns
    print("Cleaning data...")
    data = clean_dataset(dataset)

    print("Saving...")
    data.to_excel("Nutritional Facts - April 14.xlsx", index=False)
    print(f"Finished in {time.time() - start} seconds!")

    return data


if __name__ == "__main__":
    main(True)
