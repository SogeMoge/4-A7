import csv
import re

def fomat_to_xws(data_column, replacements):
    '''apply fomatting to card name or type'''
    for old, new in replacements.items():
        data_column = data_column.replace(old, new)
    return data_column

replacements = {"•": "",
                "“": "",
                "”": "",
                "’": "",
                "'": "",
                '"': "",
                "–": "-",
                "(cyborg)": "",
                "(open)": "",
                "(perfected)": "",
                "(closed)": "",
                "(erratic)": "",
                "(active)": "",
                "(inactive)": "",
                "-": "",
                " ": "",
                "é": "e",
                "/":"",
                "(BoY)": "-battleofyavin",
                "(BoY SL)": "-battleofyavin",
                "(SoC)": "-siegeofcoruscant",
                "(SoC SL)": "-siegeofcoruscant",
}

# Open the CSV file in read mode
with open('X-Wing 2.0 Legacy Points document (March 23) - Rebel Alliance.csv',
          'r',
          encoding="utf8") as csvfile:

    # Create a CSV reader object with ',' as the delimiter
    csvreader = csv.reader(csvfile, delimiter=',')

    # # Define the regex patterns for substitution
    # pattern1 = re.compile(r'[^a-zA-Z0-9(]')
    # pattern2 = re.compile(r'\s+')

    # Loop through the rows and extract data from the 3rd and 7th columns
    for i, row in enumerate(csvreader):
        if i == 2:
            continue  # skip the 3rd row
        elif row[0] == "Standard" and row[3]:  # parse only rows where first column is "Standard" and column 4 is not empty
            data_type_column = row[1]
            data_name_column = row[2]
            data_points_column = row[6]
            # Apply the xws formatting to the data in the 2nd column
            data_type_column = fomat_to_xws(data_type_column, replacements).lower().strip()
            # Apply the xws formatting to the data in the 3rd column
            data_name_column = fomat_to_xws(data_name_column, replacements).lower().strip()
            # Apply the xws formatting to the data in the 7th column
            data_points_column = data_points_column.strip()
            print(data_type_column, data_name_column, data_points_column)
