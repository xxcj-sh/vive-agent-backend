import sqlite3

conn = sqlite3.connect('vmatch_dev.db')
cursor = conn.cursor()

# Check all users with location data
cursor.execute('SELECT id, phone, location, interests FROM users WHERE location IS NOT NULL')
print('Users with location data:')
for row in cursor.fetchall():
    print(f'ID: {row[0]}, Phone: {row[1]}, Location: {repr(row[2])}, Interests: {repr(row[3])}')

# Check for empty strings or problematic data
cursor.execute('SELECT id, phone, location, interests FROM users WHERE location = ""')
print('\nUsers with empty location:')
for row in cursor.fetchall():
    print(f'ID: {row[0]}, Phone: {row[1]}, Location: {repr(row[2])}, Interests: {repr(row[3])}')

cursor.execute('SELECT id, phone, location, interests FROM users WHERE interests IS NOT NULL AND interests != ""')
print('\nUsers with interests data:')
for row in cursor.fetchall():
    print(f'ID: {row[0]}, Phone: {row[1]}, Location: {repr(row[2])}, Interests: {repr(row[3])}')

conn.close()