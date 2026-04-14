from flask import Flask, render_template, request
import psycopg2

app = Flask(__name__)


def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="airline_db",
        user="postgres",
        password="yzh200331"  # 改成你的密码
    )
    return conn


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search')
def search():
    # 获取用户输入
    origin = request.args.get('origin')
    dest = request.args.get('dest')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    conn = get_db_connection()
    cur = conn.cursor()

    # 查询可用航班
    cur.execute("""
                SELECT f.flight_number,
                       f.departure_date,
                       fs.origin_code,
                       fs.dest_code,
                       fs.departure_time
                FROM Flight f
                         JOIN FlightService fs ON f.flight_number = fs.flight_number
                WHERE fs.origin_code = %s
                  AND fs.dest_code = %s
                  AND f.departure_date BETWEEN %s AND %s
                ORDER BY f.departure_date, fs.departure_time
                """, (origin, dest, start_date, end_date))

    flights = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('flights.html', flights=flights)


@app.route('/details')
def details():
    flight_number = request.args.get('flight_number')
    departure_date = request.args.get('departure_date')

    conn = get_db_connection()
    cur = conn.cursor()

    # 查询飞机容量和已订座位数
    cur.execute("""
                SELECT a.capacity,
                       COUNT(b.seat_number) AS booked
                FROM Flight f
                         JOIN Aircraft a ON f.plane_type = a.plane_type
                         LEFT JOIN Booking b
                                   ON f.flight_number = b.flight_number
                                       AND f.departure_date = b.departure_date
                WHERE f.flight_number = %s
                  AND f.departure_date = %s
                GROUP BY a.capacity
                """, (flight_number, departure_date))

    row = cur.fetchone()
    cur.close()
    conn.close()

    if row:
        capacity = row[0]
        booked = row[1] if row[1] else 0
        available = capacity - booked
    else:
        capacity = 0
        booked = 0
        available = 0

    return render_template('details.html',
                           flight_number=flight_number,
                           departure_date=departure_date,
                           capacity=capacity,
                           booked=booked,
                           available=available)

if __name__ == '__main__':
    app.run(debug=True)