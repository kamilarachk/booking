from fastapi import FastAPI, Depends, Form
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session
import datetime
import re
from database import SessionLocal, House, Customer, Booking, init_db

app = FastAPI(title="Forest Houses API")

init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def error_page(message: str):
    return HTMLResponse(content=f"""
        <div style="text-align: center; margin-top: 50px; font-family: sans-serif;">
            <h1 style="color: #c0392b;">Ошибка</h1>
            <p style="font-size: 18px;">{message}</p>
            <br>
            <a href="/" style="padding: 10px 20px; background: #e67e22; color: white; text-decoration: none; border-radius: 5px;">Вернуться назад</a>
        </div>
    """, status_code=400)

@app.get("/")
def read_index():
    return FileResponse("templates/index.html")

@app.get("/register")
def register_page():
    return FileResponse("templates/register.html")

@app.post("/api/register")
def register_user(
    name: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    existing_user = db.query(Customer).filter(Customer.phone == phone).first()
    if existing_user:
        return error_page("Пользователь с таким телефоном уже зарегистрирован.")
    
    new_user = Customer(name=name, phone=phone, password=password)
    db.add(new_user)
    db.commit()
    
    return HTMLResponse(content=f"""
        <div style="text-align: center; margin-top: 50px; font-family: sans-serif;">
            <h1 style="color: #2c4c3b;">Регистрация успешна</h1>
            <p>Теперь вы можете бронировать дома.</p>
            <a href="/" style="padding: 10px 20px; background: #e67e22; color: white; text-decoration: none; border-radius: 5px;">На главную</a>
        </div>
    """)

@app.post("/api/book")
def create_booking(
    house_id: int = Form(...),
    name: str = Form(...),
    phone: str = Form(...),
    check_in: datetime.date = Form(...),
    check_out: datetime.date = Form(...),
    db: Session = Depends(get_db)
):
    if check_in >= check_out:
        return error_page("Дата выезда должна быть позже даты заезда.")
    
    name_check = name.replace(" ", "").replace("-", "")
    if not name_check.isalpha():
        return error_page("Имя должно содержать только буквы.")

    clean_phone = re.sub(r'\D', '', phone)
    if len(clean_phone) < 10:
        return error_page("Некорректный номер телефона.")

    try:
        customer = db.query(Customer).filter(Customer.phone == phone).first()
        
        if not customer:
            customer = Customer(name=name, phone=phone)
            db.add(customer)
            db.commit()
            db.refresh(customer)

        new_booking = Booking(
            house_id=house_id,
            customer_id=customer.id,
            check_in=check_in,
            check_out=check_out
        )
        db.add(new_booking)
        db.commit()
        
        return HTMLResponse(content=f"""
            <div style="text-align: center; margin-top: 50px; font-family: sans-serif;">
                <h1 style="color: #2c4c3b;">Заявка успешно принята!</h1>
                <p style="font-size: 18px;">Номер вашей брони: <b>{new_booking.id}</b></p>
                <p>Мы свяжемся с вами в ближайшее время.</p>
                <br>
                <a href="/" style="padding: 10px 20px; background: #e67e22; color: white; text-decoration: none; border-radius: 5px;">Вернуться на главную</a>
            </div>
        """, status_code=200)

    except Exception as e:
        db.rollback()
        return error_page(f"Ошибка базы данных: {str(e)}")

@app.get("/api/bookings")
def get_all_bookings(db: Session = Depends(get_db)):
    results = db.query(Booking, House, Customer).join(House).join(Customer).all()
    response = []
    for booking, house, customer in results:
        response.append({
            "booking_id": booking.id,
            "house": house.name,
            "price": house.price,
            "customer_name": customer.name,
            "phone": customer.phone,
            "check_in": booking.check_in,
            "check_out": booking.check_out
        })
    return response

@app.get("/view-bookings", response_class=HTMLResponse)
def view_bookings(db: Session = Depends(get_db)):
    results = db.query(Booking, House, Customer).join(House).join(Customer).all()
    
    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Все брони</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; background: #f4f7f6; padding: 40px; }
            h1 { color: #2c4c3b; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; background: white; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background-color: #2c4c3b; color: white; }
            tr:hover { background-color: #f1f1f1; }
            .back-btn { display: inline-block; margin-top: 20px; padding: 10px 20px; background: #e67e22; color: white; text-decoration: none; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>Список всех броней</h1>
        <table>
            <tr>
                <th>ID</th>
                <th>Дом</th>
                <th>Цена/ночь</th>
                <th>Клиент</th>
                <th>Телефон</th>
                <th>Заезд</th>
                <th>Выезд</th>
            </tr>
    """
    
    if not results:
        html_content += "<tr><td colspan='7' style='text-align:center;'>Пока нет ни одной брони</td></tr>"
    else:
        for booking, house, customer in results:
            html_content += f"""
            <tr>
                <td>{booking.id}</td>
                <td>{house.name}</td>
                <td>{house.price} руб.</td>
                <td>{customer.name}</td>
                <td>{customer.phone}</td>
                <td>{booking.check_in.strftime('%d.%m.%Y')}</td>
                <td>{booking.check_out.strftime('%d.%m.%Y')}</td>
            </tr>
            """
            
    html_content += """
        </table>
        <a href="/" class="back-btn">Вернуться на главную</a>
    </body>
    </html>
    """
    
    return html_content