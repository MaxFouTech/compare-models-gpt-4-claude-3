import sqlite3
import csv

# The path to the SQLite database file
db_path = 'db_model_compare.db'
# List of tables to convert to CSV
tables = ['questions', 'answers', 'comparisons', 'comparison_gpt4_claude3']

# Function to fetch data from a table
def fetch_table_data(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    data = cursor.fetchall()  # Fetch all data from the table
    columns = [description[0] for description in cursor.description]
    return data, columns

# Function to write data to a CSV file
def write_to_csv(file_name, data, columns):
    with open(file_name, 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(columns)  # Write the column headers
        writer.writerows(data)  # Write the data

def main():
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    
    for table in tables:
        data, columns = fetch_table_data(conn, table)
        # Generate CSV file name (e.g., 'questions.csv')
        csv_file_name = f"{table}.csv"
        write_to_csv(csv_file_name, data, columns)
        print(f"Data from table '{table}' has been written to {csv_file_name}")

    # Close the connection to the database
    conn.close()

if __name__ == "__main__":
    main()
