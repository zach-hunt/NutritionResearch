Attribute VB_Name = "Module1"
Option Explicit
'Zachary Hunt

Sub clean_categories()

    Worksheets("Sheet1").Activate
    Dim main_cats As Range
    Set main_cats = Range("C2", Range("C1").End(xlDown))
    Dim iCat, iCats As Integer
    iCats = main_cats.Rows.Count
    
    Dim word, split_word As Variant
    Dim problem_cat, splits(2) As String
    Dim curr_cat As Range
    problem_cat = "Soups and Salads"
    splits(0) = "Soup"
    splits(1) = "Salad"
    
    For iCat = 1 To iCats
        Set curr_cat = main_cats.Cells(iCat, 1)
        If curr_cat.Value = problem_cat Then
            For Each word In split(curr_cat.Offset(0, 1).Value, " ")
                For Each split_word In splits
                    If Replace(word, ",", "") = split_word Then
                        curr_cat.Value = split_word & "s"
                        Exit For
                    End If
                Next split_word
            Next word
        End If
    Next iCat
    
End Sub


Sub categorize()

    Application.SendKeys "^g ^a {DEL}"

    Dim cats, fcats, curr_cat As Range
    Worksheets("Category Mappings").Activate
    Set fcats = Range("A2", Range("A1").End(xlDown))
    Set cats = Range("D2", Range("D2").End(xlDown))
    
    Dim defined As Scripting.Dictionary
    Dim new_cat As String
    Dim partial_match As Boolean
    
    Set defined = init_dict()
    
    For Each curr_cat In cats
        defined.Add curr_cat.Value, curr_cat.Value
    Next curr_cat
    
    Dim cat_key, cat_word, curr_cat_word As Variant
    Dim temp_curr_cat_word As String
    
    For Each curr_cat In fcats
        'curr_cat.Select
        If defined.Exists(curr_cat.Value) Then
            curr_cat.Offset(0, 1).Value = defined(curr_cat.Value)
        Else
            partial_match = False
            For Each cat_key In defined.Keys()
                For Each cat_word In split(cat_key, " ")
                    For Each curr_cat_word In split(curr_cat.Value, " ")
                        If curr_cat_word = cat_word Then
                            curr_cat.Offset(0, 1).Value = defined(cat_key)
                            partial_match = True
                            Exit For
                        End If
                    Next curr_cat_word
                Next cat_word
            Next cat_key

            If Not partial_match Then
                new_cat = InputBox("Please select a category for " & curr_cat.Value, "New Label!")
                defined.Add Replace(curr_cat.Value, " and ", " "), new_cat
                Debug.Print "defined.Add """ & Replace(curr_cat.Value, " and ", " ") & """, " & """" & new_cat & """"
                curr_cat.Offset(0, 1).Value = new_cat
            End If
        End If
    Next curr_cat
    

End Sub


Function init_dict() As Scripting.Dictionary
    Dim defined As New Scripting.Dictionary
    
    defined.Add "Sliders", "Sandwiches"
    defined.Add "Drinks", "Beverages"
    defined.Add "Ice Cream", "Desserts"
    defined.Add "Cones", "Desserts"
    defined.Add "Cookies Brownies", "Desserts"
    defined.Add "Grab-N-Go", "To-Go"
    defined.Add "Dressings Sauces", "Condiments"
    defined.Add "Subs", "Sandwiches"
    defined.Add "Meals", "General"
    defined.Add "Add-in Flavors Toppings", "Condiments"
    defined.Add "Bagels", "Breakfast"
    defined.Add "Bakery Favorites", "Dessert"
    defined.Add "Baskets", "General"
    defined.Add "Beef & Pork", "Sandwiches"
    defined.Add "Blizzards", "Beverages"
    defined.Add "Boneless Wings", "General"
    defined.Add "Boosts", "Beverages"
    defined.Add "Breads", "Beverages"
    defined.Add "Bunless Burgers", "Sandwiches"
    defined.Add "Burrito Bowls", "General"
    defined.Add "Burritos", "General"
    defined.Add "ButterBurgers", "Sandwiches"
    defined.Add "Chalupas", "General"
    defined.Add "Cheeses", "Condiments"
    defined.Add "Chicken", "General"
    defined.Add "Ciabatta Toasties", "General"
    defined.Add "Cocktails", "Beverages"
    defined.Add "Coffee", "Beverages"
    defined.Add "Concrete Mixers", "Beverages"
    defined.Add "Cool Wraps", "Sandwiches"
    defined.Add "Coolattas", "General"
    defined.Add "Dinners", "General"
    defined.Add "Dogs", "Sandwiches"
    defined.Add "Donuts", "Dessert"
    defined.Add "DQ Cakes", "Dessert"
    defined.Add "Flatizza", "Pizzas"
    defined.Add "French Fries", "Sides"
    defined.Add "Fresco Menu", "General"
    defined.Add "Frosty Treats", "Desserts"
    defined.Add "Frozen Custard Shoppe To Go", "Desserts"
    defined.Add "Golden Crust Pizza", "Pizzas"
    defined.Add "Haagen Dazs Shakes Malts", "Desserts"
    defined.Add "Iced Teas", "Beverages"
    defined.Add "Iceflow Lemonade", "Beverages"
    defined.Add "Jack's Munchies Meal Items", "General"
    defined.Add "Julius Originals", "Beverages"
    defined.Add "Kids", "General"
    defined.Add "Limeades", "Beverages"
    defined.Add "Main Dishes", "General"
    defined.Add "Milkshakes", "Desserts"
    defined.Add "Minute Made Juices", "Beverages"
    defined.Add "MooLattes", "Beverages"
    defined.Add "Munchkins", "Desserts"
    defined.Add "Nachos", "Snack"
    defined.Add "Novelties", "General"
    defined.Add "Ocean Water", "Beverages"
    defined.Add "Other", "General"
    defined.Add "Pasta", " General"
    defined.Add "Premium Roast Coffees", "Beverages"
    defined.Add "Salad Bar", "Salads"
    defined.Add "Single Topping Sundaes", "Desserts"
    defined.Add "Slushes", "Desserts"
    defined.Add "Sonic Blast", "Desserts"
    defined.Add "Soup", "Soups"
    defined.Add "Specialties", "General"
    defined.Add "Tortilla Chips", "Sides"
    defined.Add "Vegetables", "Vegetables"
    defined.Add "Wing Accompaniments", "Condiments"
    defined.Add "Zalads", "Salads"
    defined.Add "Zappetizers", "Appetizers"
    
    Set init_dict = defined

End Function


Sub match()

    Sheet2.Activate
    Dim cats As Range, common_cats As Range
    Set cats = Range("A2", Range("A2").End(xlDown))
    Set common_cats = cats.Offset(0, 1)
    
    Sheet1.Activate
    Dim food_cats As Range, match_cats As Range
    Set food_cats = Range("C2", Range("C2").End(xlDown))
    Set match_cats = Range("Y2", Range("Y2").End(xlDown)).Offset(0, 1)
    
    Dim i As Integer, j As Integer
    For i = 1 To food_cats.Rows.Count
        For j = 1 To cats.Rows.Count
            If food_cats.Cells(i, 1).Value = cats.Cells(j, 1).Value Then
                match_cats.Cells(i, 1).Value = common_cats.Cells(j, 1).Value
            End If
        Next j
    Next i

End Sub
