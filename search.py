import os

base = r"C:\Users\lonan\Desktop\Projects\recycling-robot"

for root, dirs, files in os.walk(base):
    for file in files:
        if file == "best.pt":
            print(os.path.join(root, file))