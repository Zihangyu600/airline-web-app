from flask import Flask, render_template, request
#链接数据库的库
import psycopg2

#创建一个 Flask 应用实例
app = Flask(__name__)

#每次需要查数据库时，调用这个函数
def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="airline_db",
        user="postgres",
        password="yzh200331"  # 改成你的密码
    )
    return conn


from datetime import date


@app.route('/')
def index():
    #连接数据库并查询 查询所有机场（代码、名称、城市），按代码排序
    conn = get_db_connection()
    cur = conn.cursor()

    # 获取retrieve机场列表
    cur.execute("SELECT airport_code, name, city FROM Airport ORDER BY airport_code")
    airports = cur.fetchall()

    # 获取有航班的日期列表
    cur.execute("SELECT DISTINCT departure_date FROM Flight ORDER BY departure_date")
    flight_dates = cur.fetchall()
    # 转换成 YYYY-MM-DD 格式的列表
    flight_dates_list = [d[0].strftime('%Y-%m-%d') for d in flight_dates]

    #关闭连接
    cur.close()
    conn.close()

    today = date.today().isoformat()

    #把数据传给 index.html 模板
    return render_template('index.html',
                           airports=airports,
                           min_date=today,
                           flight_dates=flight_dates_list)

@app.route('/search')
def search():
    # 获取用户输入
    origin = request.args.get('origin')
    dest = request.args.get('dest')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    conn = get_db_connection()
    cur = conn.cursor()

    # 查询数据库 查询可用航班
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
    #把查询结果传给 flights.html 显示
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

    #如果有结果，计算剩余 = 容量 − 已订
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
