# check_db.py

import sqlite3
from datetime import datetime

def check_database():
    """Check database content"""
    try:
        # Connect to database
        conn = sqlite3.connect('database/kpg_malibu_bvb.db')
        cursor = conn.cursor()

        # Check sessions
        print("\nChecking sessions table:")
        cursor.execute('SELECT * FROM sessions')
        sessions = cursor.fetchall()
        print(f"Found {len(sessions)} sessions:")
        for session in sessions:
            print(f"ID: {session[0]}")
            print(f"Date: {session[1]}")
            print(f"Time: {session[2]} - {session[3]}")
            print(f"Max players: {session[4]}")
            print(f"Message ID: {session[5]}")
            print(f"Chat ID: {session[6]}\n")

        # Check players
        print("\nChecking players table:")
        cursor.execute('SELECT * FROM players')
        players = cursor.fetchall()
        print(f"Found {len(players)} players:")
        for player in players:
            print(f"ID: {player[0]}")
            print(f"Name: {player[1]}")
            print(f"Telegram ID: {player[2]}")
            print(f"Created at: {player[3]}\n")

        # Check registrations
        print("\nChecking registrations table:")
        cursor.execute('''
            SELECT r.*, p.full_name 
            FROM registrations r 
            JOIN players p ON r.player_id = p.id
        ''')
        registrations = cursor.fetchall()
        print(f"Found {len(registrations)} registrations:")
        for reg in registrations:
            print(f"ID: {reg[0]}")
            print(f"Session ID: {reg[1]}")
            print(f"Player: {reg[4]} (ID: {reg[2]})")
            print(f"Status: {reg[3]}")
            print(f"Registration time: {reg[3]}\n")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    check_database()
