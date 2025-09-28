from app import init_db, get_db, ROLLS_37_54
init_db()
conn = get_db()
for r in ROLLS_37_54:
    conn.execute("INSERT INTO internships (roll, student_name, company, created_at) VALUES (?, ?, ?, ?)",
                 (r, f"Student {r}", "Example Corp", "2025-01-01T00:00:00"))
conn.commit()
conn.close()
print("Populated rolls 37-54 (demo)")
