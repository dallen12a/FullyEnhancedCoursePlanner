"""
Course Planner Application
Programmer: David Allen
Date: 2023-09-26
Version: 3.0

Intent:
This program serves as a Course Planner application, allowing users to manage and view courses.
It provides functionalities to load course data, add and delete courses, and view course details.
Additionally, it allows administrators to manage users, including listing, adding, and deleting users.

Decision:
The program uses SQLite for database management, separating courses and users into two databases.
Each database has its own connection (conn_courses and conn_users) to facilitate independent operations.
The program follows a menu-driven approach for user interaction and maintains data integrity through
appropriate error handling and validation at each step.
The code is structured into functions to enhance modularity, readability, and ease of maintenance.

!! NOTE !!
If any changes are made to courselist.csv please choose option 6 to update database for update
prior to any other options
"""

import csv
import sqlite3
import os

# Class for Course structure
class Course:
    def __init__(self):
        self.id = ""
        self.title = ""
        self.credits = ""
        self.description = ""
        self.prerequisites = []

# Function to load course data from a CSV file and create the database
def load_course_data(cursor):
    csv_file = "courselist.csv"

    # Create the database file and the "courses" table if they don't exist
    conn = sqlite3.connect("course_database.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS courses
                    (id TEXT PRIMARY KEY,
                     title TEXT,
                     credits TEXT,
                     description TEXT,
                     prerequisites TEXT)''')

    try:
        with open(csv_file, newline='') as file:
            reader = csv.reader(file, delimiter=',')

            conn.execute("DELETE FROM courses")  # Clear existing data

            for row in reader:
                if len(row) >= 4:
                    id = row[0]
                    title = row[1]
                    credits = row[2]
                    description = row[3]
                    prerequisites = row[4].split() if len(row) > 4 else "None"
                    conn.execute("INSERT INTO courses (id, title, credits, description, prerequisites) VALUES (?, ?, ?, ?, ?)",
                                   (id, title, credits, description, ', '.join(prerequisites)))
                else:
                    print("Error: Invalid data format in the CSV file.")
                    conn.rollback()  # Rollback the transaction in case of an error
                    return False

        conn.commit()  # Commit the transaction after successful data insertion
        conn.close()
        return True

    except FileNotFoundError:
        print("Error: The course data file 'courselist.csv' is unavailable.")
        return False

# Function to load user data from a CSV file and create the user database
def load_user_data(cursor):
    csv_file = "userlist.csv"

    # Check if the user database file exists, if not create it
    if not os.path.exists("user_database.db"):
        # Create the user database and the "users" table
        conn = sqlite3.connect("user_database.db")
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users
                        (username TEXT PRIMARY KEY,
                         password TEXT)''')
        conn.close()

    # Load user data from CSV and populate the "users" table
    try:
        with open(csv_file, newline='') as file:
            reader = csv.reader(file)

            conn = sqlite3.connect("user_database.db")
            cursor = conn.cursor()

            for row in reader:
                if len(row) >= 2:
                    username = row[0].strip().lower()
                    password = row[1]
                    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                                   (username, password))
                else:
                    print("Error: Invalid data format in the CSV file.")
                    conn.rollback()  # Rollback the transaction in case of an error
                    return False

            conn.commit()  # Commit the transaction after successful data insertion
            conn.close()
            return True

    except FileNotFoundError:
        print("Error: The user data file 'userlist.csv' is unavailable.")
        return False

# Function to authenticate the user
def login(cursor):
    while True:
        username = input("Enter username: ").strip().lower()
        password = input("Enter password: ")

        # Check if the provided credentials match the records in the user database
        if username == "admin" and password == "admin":
            print("Login successful.")
            return True
        if cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)):
            user = cursor.fetchone()
        if user:
            print("Login successful.")
            return True
        else:
            print("Login failed. Please try again.")

# Function to add a new course to the database
def add_course(cursor, data_loaded):
    if data_loaded:
        course = Course()
        course.id = input("Enter the course ID: ").strip().upper()
        course.title = input("Enter the course title: ").title() # Capitalize each word in the course title
        course.credits = input("Enter the course credits: ")
        course.description = input("Enter the course description: ")
        prerequisites = input("Enter course prerequisites (space-separated, leave empty for none): ")
        if prerequisites == "":
            prerequisites = "None"
        course.prerequisites = [p.strip() for p in prerequisites.split(" ") if p.strip()]  # Filter out empty prerequisites

        # Check if a course with the same ID already exists
        cursor.execute("SELECT id FROM courses WHERE id = ?", (course.id,))
        existing_course = cursor.fetchone()

        if existing_course:
            print(f"Course with the same ID '{course.id}' already exists.")
            replace_confirmation = input("Do you want to replace it? (Y/N): ").strip().lower()

            if replace_confirmation == "y":
                cursor.execute("UPDATE courses SET title=?, credits=?, description=?, prerequisites=? WHERE id=?",
                               (course.title, course.credits, course.description, ', '.join(course.prerequisites), course.id))
                print(f"Course '{course.id}' replaced successfully.")
            else:
                print("Course not replaced.")
        else:
            cursor.execute("INSERT INTO courses (id, title, credits, description, prerequisites) VALUES (?, ?, ?, ?, ?)",
                           (course.id, course.title, course.credits, course.description, ', '.join(course.prerequisites)))
            print("Course added successfully.")
    else:
        print("Course data is not loaded. Please choose option 1 to load data.")

# Function to delete a course from the database
def delete_course(cursor, data_loaded):
    if data_loaded:
        cursor.execute("SELECT id, title FROM courses ORDER BY id")  # Sort by course ID
        courses = cursor.fetchall()
        if len(courses) == 0:
            print("No courses found.")
            return

        print("List of Courses:")
        for i, course in enumerate(courses, start=1):
            print(f"{i}. ID: {course[0]}, Title: {course[1]}")

        try:
            choice = int(input("Enter the number of the course to delete: "))
            if 1 <= choice <= len(courses):
                course_id = courses[choice - 1][0]
                confirmation = input(f"Enter 'Y' to confirm delete course {course_id} or 'N' to cancel: ")
                if confirmation.lower() == "y":
                    cursor.execute("DELETE FROM courses WHERE id = ?", (course_id,))
                    print(f"Course {course_id} deleted successfully.")
                else:
                    print("Deletion canceled.")
            else:
                print("Invalid choice. Please enter a valid course number.")
        except ValueError:
            print("Invalid input. Please enter a valid course number.")
    else:
        print("Course data is not loaded. Please choose option 1 to load data.")
        
# Function to wrap text to a specified width
def word_wrap(text, width=80):
    words = text.split()
    lines = []
    current_line = words[0]

    for word in words[1:]:
        if len(current_line) + len(word) + 1 <= width:
            current_line += ' ' + word
        else:
            lines.append(current_line)
            current_line = word

    lines.append(current_line)
    return '\n'.join(lines)

# Function to list all users in the user database
def list_users(cursor):
    cursor.execute("SELECT username, password FROM users ORDER BY username")  # Sort by username
    users = cursor.fetchall()
    # Print table headers
    print("+---------------------+---------------------+")
    print("|{:<21}|{:<21}|".format("Username", "Password"))
    print("+---------------------+---------------------+")
    
    # Print each user in a formatted row
    for user in users:
        print("|{:<21}|{:<21}|".format(user[0], '*' * len(user[1])))  # Fixed format string

    print("+---------------------+---------------------+")

# Function to add a new user to the user database
def add_user(cursor):
    username = input("Enter the username: ").strip().lower()
    password = input("Enter the password: ")
    cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
    existing_user = cursor.fetchone()
    if existing_user:
        print("Error: Username already exists.")
    else:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        print(f"User {username} added successfully.")
    conn_users.commit()

# Function to delete a user from the user database
def delete_user(cursor):
    username = input("Enter the username to delete: ").strip().lower()
    if username == 'admin':
        print("Error: Cannot delete admin.")
        return
    cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
    existing_user = cursor.fetchone()
    if existing_user:
        cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        print(f"User {username} deleted successfully.")
    else:
        print("Error: User not found in the database.")
    conn_users.commit()

# Function to print the course list
def print_course_list(cursor):
    if data_loaded:
        print("List of Courses:")
        cursor.execute("SELECT id, title FROM courses ORDER BY id")  # Sort by course ID
        courses = cursor.fetchall()
        if not courses:
            print("No courses found.")
            return
        for course in courses:
            print(f"{course[0]}, {course[1]}")
    else:
        print("Course data is not loaded. Please choose option 1 to load data.")

# Function to print course details
def print_course_details(course):
    print(f"Course Details:")
    print(f"ID: {course[0]}")
    print(f"Title: {course[1]}")
    print(f"Credits: {course[2]}")
    print(f"Description: ")
    wrapped_description = word_wrap(course[3])
    print(wrapped_description)
    prerequisites = course[4]
    if prerequisites.lower() == "none":  # Check if prerequisites are "None"
        print("Prerequisites: None")
    else:
        print(f"Prerequisites: {prerequisites}")

# Function to display the main menu with a border
def display_main_menu():
    if user_authenticated:
        authenticated_text = "\033[1;32;40mUser Authenticated\033[m"
        
    print("+" + "-"*30 + "+")
    print("|{:<30}|".format("Welcome to the Course Planner"))
    print("|{:<30}|".format("-" * 30))
    print("|{:<30}|".format("1. Load Data Structure"))
    print("|{:<30}|".format("2. Print Course List"))
    print("|{:<30}|".format("3. Print Course Details"))
    print("|{:<30}|".format("0. Exit Program"))
    print("|{:<30}|".format("-" * 30))
    print("|{:<30}|".format("Options below require login"))
    print("|{:<30}|".format("-" * 30))
    print("|{:<30}|".format("4. Add Course"))
    print("|{:<30}|".format("5. Delete Course"))
    print("|{:<30}|".format("6. Reset Default Course List"))
    print("|{:<30}|".format("-" * 30))
    print("|{:<30}|".format("* User Management Database"))
    print("+" + "-"*30 + "+")
    
    if user_authenticated:
        print("|" + authenticated_text + " " * 12 + "|")
        print("|{:<30}|".format("-" * 30))

    print("+" + "-"*30 + "+")

# Function to display the user management menu with a border
def display_user_management_menu():
    print("+" + "-"*30 + "+")
    print("|{:<30}|".format("User Management Database"))
    print("|{:<30}|".format("-" * 30))
    print("|{:<30}|".format("A. List Users"))
    print("|{:<30}|".format("B. Add User"))
    print("|{:<30}|".format("C. Delete User"))
    print("|{:<30}|".format("R. Return to Main Menu"))
    print("+" + "-"*30 + "+")

if __name__ == "__main__":
    conn_courses = sqlite3.connect("course_database.db")
    cursor_courses = conn_courses.cursor()

    # Create the user database and the "users" table if they don't exist
    conn_users = sqlite3.connect("user_database.db")
    cursor_users = conn_users.cursor()
    cursor_users.execute('''CREATE TABLE IF NOT EXISTS users
                    (username TEXT PRIMARY KEY,
                     password TEXT)''')

    data_loaded = False
    user_authenticated = False  # To track user authentication
    user_choice = None

    # Load user data if the database doesn't exist
    if not os.path.exists("user_database.db"):
        data_loaded = load_user_data(cursor_users)
    else:
        data_loaded = True

    while True:
        display_main_menu()

        try:
            option = input("Select an option: ")

            # Validate the option
            if option not in ["0", "1", "2", "3", "4", "5", "6", "*"]:
                print("Invalid option. Please enter a valid menu option.")
                continue

            if option == "1":
                if not data_loaded or user_choice == option:
                    data_loaded = load_course_data(cursor_courses)
                    if data_loaded:
                        print("Course data loaded successfully.")
                else:
                    print("Course data is already loaded.")
            elif option == "2":
                if data_loaded:
                    print_course_list(cursor_courses)
                else:
                    print("Course data is not loaded. Please choose option 1 to load data.")
            elif option == "3":
                if data_loaded:
                    course_id = input("Enter the course ID: ").strip().upper()
                    cursor_courses.execute("SELECT * FROM courses WHERE id = ?", (course_id,))
                    course = cursor_courses.fetchone()
                    if course:
                        print_course_details(course)
                    else:
                        print(f"Course {course_id} not found.")
                else:
                    print("Course data is not loaded. Please choose option 1 to load data.")
            elif option == "0":
                save_changes = input("Do you want to save changes? (Y/N): ").strip().lower()
                if save_changes == "y":
                    conn_courses.commit()  # Save changes to the course database
                    print("Changes saved successfully.")
                print("Thank You For Using The Course Planner.")
                break
            elif option in ["4", "5", "6"]:
                if user_authenticated or user_choice == option:
                    user_choice = option  # Store the user's choice
                if not user_authenticated:  # If not authenticated, prompt for login
                    print("Login required.")
                    user_authenticated = login(cursor_users)
                    if user_authenticated:
                        print("User authenticated.")
                    else:
                        print("Login failed. Please try again.")
                        continue
                if option == "4":
                    add_course(cursor_courses, data_loaded)
                elif option == "5":
                    delete_course(cursor_courses, data_loaded)
                elif option == "6":
                    reset_confirmation = input("Are you sure you want to reset the default course list? (Y/N): ").strip().lower()
                    if reset_confirmation == "y":
                        # Delete the database file and reload the data
                        conn_courses.close()
                        os.remove("course_database.db")
                        conn_courses = sqlite3.connect("course_database.db")
                        cursor_courses = conn_courses.cursor()
                        data_loaded = load_course_data(cursor_courses)
                        if data_loaded:
                            print("Database reset. Default data structure loaded.")
                    elif reset_confirmation != "n":
                        print("Invalid choice. Please enter 'Y' to confirm reset or 'N' to cancel.")
                else:
                    print("Login required.")
            elif option == "*":
                admin_username = "admin"
                admin_password = "admin"
                print("Only an administrator can login for user management.")
                admin_login_username = input("Enter admin username: ").strip().lower()
                admin_login_password = input("Enter admin password: ")
                if admin_login_username == admin_username and admin_login_password == admin_password:
                    user_choice = "*"  # Set the user_choice to '*' so the menu is displayed after login
                    user_authenticated = True
                    while True:
                        display_user_management_menu()
                        user_option = input("Select a user management option: ").strip().upper()
                        if user_option == "A":
                            list_users(cursor_users)
                        elif user_option == "B":
                            add_user(cursor_users)
                        elif user_option == "C":
                            delete_user(cursor_users)
                        elif user_option == "R":
                            user_authenticated = False
                            break
                        else:
                            print("Invalid option. Please select a valid user management option.")
                else:
                    print("Invalid admin credentials. Access denied.")
        except ValueError:
            print("Invalid choice. Please enter a valid menu option.")
            continue

    conn_courses.close()
    conn_users.close()
