# NutritionResearch
Collection of code used in our nutrition research project, looking at eating healthily at fast food restaurants.

### Webscraping
Web scraping to gather data for building a nutrition focused dieting network model

Built entirely in Python, using BeautifulSoup to fetch data from [FastFoodNutrition](https://fastfoodnutrition.org/).

Check out ```restaurants.txt``` for the list of 40 restaurants* with data on FastFoodNutrition.

Read through ```main.py``` to see how the scraping was done, or take a look at the results in ```Nutritional Facts.xlsm```!

###### * Fast Food Nutrition also has data for Starbucks, which was not considered *

### Data Manipulation
Categorization and cleanup was handled by Python and VBA.

Take a look in ```CategorizationVBA.bas``` for the VBA code that filters foods into general categories like
```Appetizers```, ```Sandwiches```, and ```Seafood```.

### Next Steps
Ongoing maintenance is required as FastFoodNutrition adds images to their menus,
which changes the structure of the HTML slightly and messing up the scraping scripts.
Starbucks is still not handled, due to many drinks like the
[Caffe-Latte](https://fastfoodnutrition.org/starbucks/caffe-latte/choose-milk) requiring selections
of both milk (6 options) and size (4 options), rather than just being a singular food.
Adapting to handle this is not egregious, given that things like McDonald's successfully handle
size selection for fries and drinks, etc.

Notably, because no threading has been attempted, the download process for the 6000+ food entries is around 40 minutes.
This is largely independent of connection speed, having more to do with a reasonable ping delay repeated
for every food, drink, condiment, and corresponding size.

### Data Analysis
The ongoing goal of the research project is to determine which fast food restaurants are healthier and provide a useful guide
to individuals seeking responsible eating choices at those restaurants. This is a question for operations research and is
being tackled with the help of Python and the Gurobi solver. More information to come!