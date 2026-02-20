"""Basics.py module."""

# file = open("data.txt", "w")
# file.write("Hello, World!\n")
# file.write("Welcome to Streamlit.\n")
# file.close()

# file = open("data.txt", "r")
# content = file.read()
# print(content)
# file.close()

file = open("data.txt", "a")   # "a" stands for append mode
file.write("This is a new line.\n")
file.close()

