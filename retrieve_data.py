import sqlite3
import csv

def retrieve_data():
    conn = sqlite3.connect("conjoint_data.db")
    cursor = conn.cursor()

    # Example: Retrieve all participants
    cursor.execute("SELECT * FROM participants")
    participants = cursor.fetchall()

    # Example: Retrieve all choices (survey responses)
    cursor.execute("SELECT * FROM choices")
    choices = cursor.fetchall()

    conn.close()

    return participants, choices

def save_data_to_csv(participants, choices):
    # Save participants data to CSV
    with open('participants.csv', 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['id', 'age', 'gender', 'race_ethnicity'])
        csv_writer.writerows(participants)

    # Save choices data to CSV
    with open('choices.csv', 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['id', 'participant_id', 'decision', 'severity', 'explanation', 'performance', 'responsibility', 'discrimination', 'cost', 'user_choice'])
        csv_writer.writerows(choices)

# Example usage
participants_data, choices_data = retrieve_data()
save_data_to_csv(participants_data, choices_data)
