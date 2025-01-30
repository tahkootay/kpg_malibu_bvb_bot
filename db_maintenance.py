# db_maintenance.py

import sqlite3
from datetime import datetime, timedelta

def clean_old_sessions():
    """Clean up old sessions and their registrations"""
    try:
        conn = sqlite3.connect('database/kpg_malibu_bvb.db')
        cursor = conn.cursor()

        # Get today's date
        today = datetime.now().date()

        # Delete registrations for old sessions
        cursor.execute('''
            DELETE FROM registrations 
            WHERE session_id IN (
                SELECT id FROM sessions 
                WHERE date < ?
            )
        ''', (today.isoformat(),))

        # Delete old sessions
        cursor.execute('''
            DELETE FROM sessions 
            WHERE date < ?
        ''', (today.isoformat(),))

        # Remove duplicate sessions for the same date
        cursor.execute('''
            DELETE FROM sessions 
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM sessions
                GROUP BY date, time_start, time_end, max_players
            )
        ''')

        conn.commit()
        print("Database cleaned successfully")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

def check_database():
    """Check database content"""
    try:
        conn = sqlite3.connect('database/kpg_malibu_bvb.db')
        cursor = conn.cursor()

        # Check sessions
        print("\nChecking sessions table:")
        cursor.execute('''
            SELECT * FROM sessions 
            WHERE date >= date('now')
            ORDER BY date, time_start
        ''')
        sessions = cursor.fetchall()
        print(f"Found {len(sessions)} active sessions:")
        for session in sessions:
            print(f"ID: {session[0]}")
            print(f"Date: {session[1]}")
            print(f"Time: {session[2]} - {session[3]}")
            print(f"Max players: {session[4]}")
            print(f"Message ID: {session[5]}")
            print(f"Chat ID: {session[6]}\n")

        # Check registrations with correct player names
        print("\nChecking registrations table:")
        cursor.execute('''
            SELECT 
                r.id,
                r.session_id,
                p.full_name,
                p.id as player_id,
                r.status,
                r.registration_time,
                s.date,
                s.time_start
            FROM registrations r 
            JOIN players p ON r.player_id = p.id
            JOIN sessions s ON r.session_id = s.id
            WHERE s.date >= date('now')
            ORDER BY s.date, s.time_start, r.registration_time
        ''')
        registrations = cursor.fetchall()
        print(f"Found {len(registrations)} active registrations:")
        for reg in registrations:
            print(f"ID: {reg[0]}")
            print(f"Session: {reg[6]} {reg[7]}")
            print(f"Player: {reg[2]} (ID: {reg[3]})")
            print(f"Status: {reg[4]}")
            print(f"Registration time: {reg[5]}\n")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    clean = input("Do you want to clean old/duplicate sessions? (y/n): ")
    if clean.lower() == 'y':
        clean_old_sessions()
    check_database()
