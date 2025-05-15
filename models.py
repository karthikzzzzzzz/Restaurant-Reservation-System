from database import Base
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship


class Restaurant(Base):
    __tablename__ = "restaurants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)                     
    location = Column(String, nullable=False)                
    cuisine = Column(String, nullable=False)               
    seating_capacity = Column(Integer, nullable=False)        
    rating = Column(Float, nullable=True, default=0.0)       
    price_for_two = Column(Float, nullable=True, default=0.0) 
    contact_number = Column(String, nullable=False)     
    daily_specials = Column(String, nullable=True)            
    amenities = Column(String, nullable=True)                 


class Reservation(Base):
    __tablename__ = "reservations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, nullable=False)            
    user_contact = Column(String, nullable=False)            
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    reservation_time = Column(DateTime, nullable=False)       
    guests = Column(Integer, nullable=False)                

    restaurant = relationship("Restaurant", backref="reservations")


class UserFeedback(Base):
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    reservation_id = Column(Integer, ForeignKey("reservations.id"), nullable=False)
    rating = Column(Float, nullable=True)                     
    comments = Column(String, nullable=True)                  

    reservation = relationship("Reservation", backref="feedback")
