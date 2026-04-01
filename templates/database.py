import pyodbc

def get_connection():
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 18 for SQL Server};'
        'SERVER=localhost;'
        'DATABASE=DIIP;'
        'Trusted_Connection=yes;'
        'TrustServerCertificate=yes;'
    )
    return conn


def test_connection():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT GETDATE()")
        result = cursor.fetchone()
        conn.close()
        print("✅ Conexiune OK:", result)
    except Exception as e:
        print("❌ Eroare:", e)


if __name__ == "__main__":
    test_connection()