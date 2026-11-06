from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./forest_booking.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class House(Base):
    __tablename__ = "houses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    price = Column(Integer)

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    phone = Column(String, unique=True)
    password = Column(String, nullable=True)

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    house_id = Column(Integer, ForeignKey("houses.id"))
    customer_id = Column(Integer, ForeignKey("customers.id"))
    check_in = Column(Date)
    check_out = Column(Date)

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if db.query(House).count() == 0:
        db.add_all([
            House(id=1, name="Дом ближе к озеру", price=25000),
            House(id=2, name="Дом ближе к лесу", price=26000),
            House(id=3, name="Дом с большим крыльцом", price=27000),
            House(id=4, name="Дом с 3 этажами", price=32000)
        ])
        db.commit()
    db.close()