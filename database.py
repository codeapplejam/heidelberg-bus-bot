from sqlalchemy import Column, Integer, String, Date, Time, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Driver(Base):
    __tablename__ = 'drivers'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    telegram_id = Column(Integer, unique=True)

class Schedule(Base):
    __tablename__ = 'schedules'
    id = Column(Integer, primary_key=True)
    driver_id = Column(Integer)
    date = Column(Date)
    umlauf = Column(String)
    start_time = Column(Time)
    end_time = Column(Time)
    routes = Column(JSON)

class BusRoute(Base):
    __tablename__ = 'bus_routes'
    id = Column(Integer, primary_key=True)
    route_number = Column(String)
    name = Column(String)
    stations = Column(JSON)
