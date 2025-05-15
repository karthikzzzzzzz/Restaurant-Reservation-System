from fastapi import Depends
from mcp.server.fastmcp import FastMCP
from sqlalchemy import and_
import uvicorn
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Mount, Route
from mcp.server import Server
from database import get_db
from typing import List, Optional
from datetime import datetime, timedelta
from models import Reservation, Restaurant, UserFeedback

mcp = FastMCP("Reservation-Agent")

@mcp.tool()
def check_availability(location: str,date_time: str,guests: int,preferences: Optional[List[str]] = [],restaurant: str = None) -> dict:
    """
    Checks the availability of restaurants based on the location, date and time, number of guests, and optional preferences.

    Args:
        location (str): City or area name where the user wants to dine.
        date_time (str): Desired reservation time in ISO format (e.g., '2025-05-15T19:30').
        guests (int): Number of guests for the reservation.
        preferences (list[str], optional): User preferences like 'rooftop', 'vegan', 'live music'.
        restaurant (str, optional): Specific restaurant name if the user has already selected one.

    Returns:
        dict: {
            "available": bool,
            "matched_restaurant": str,
            "available_slots": list[str],
            "daily_specials": str,
            "price_for_two": str,
            "amenities": list[str]
        }
    """
    db = next(get_db())
    date_time_obj = datetime.fromisoformat(date_time)

    restaurant_query = db.query(Restaurant).filter(Restaurant.location.ilike(location))

    if restaurant:
        restaurant_query = restaurant_query.filter(Restaurant.name.ilike(f"%{restaurant}%"))
    
    for pref in preferences:
        restaurant_query = restaurant_query.filter(Restaurant.amenities.ilike(f"%{pref}%"))
    
    matched_restaurant = restaurant_query.first()
    
    if not matched_restaurant:
        return {
            "available": False,
            "matched_restaurant": None,
            "available_slots": [],
            "daily_specials": "",
            "price_for_two": "",
            "amenities": []
        }


    start_time = date_time_obj - timedelta(hours=1)
    end_time = date_time_obj + timedelta(hours=1)

    existing_reservations = (
        db.query(Reservation)
        .filter(
            and_(
                Reservation.restaurant_id == matched_restaurant.id,
                Reservation.reservation_time >= start_time,
                Reservation.reservation_time <= end_time,
            )
        )
        .all()
    )

    total_guests = sum(res.guests for res in existing_reservations)
    available_capacity = matched_restaurant.seating_capacity - total_guests

    is_available = available_capacity >= guests


    available_slots = []
    if is_available:
        available_slots = [date_time_obj.strftime("%Y-%m-%d %H:%M")]
    else:
        for i in range(1, 4):
            new_time = date_time_obj + timedelta(hours=i)
            available_slots.append(new_time.strftime("%Y-%m-%d %H:%M"))
    amenities = matched_restaurant.amenities.split(",") if matched_restaurant.amenities else []

    return {
        "available": is_available,
        "matched_restaurant": matched_restaurant.name,
        "available_slots": available_slots,
        "daily_specials": matched_restaurant.daily_specials or "Not available",
        "price_for_two": f"₹{int(matched_restaurant.price_for_two)}",
        "amenities": [a.strip() for a in amenities]
    }

@mcp.tool()
def make_reservation(user_name: str,user_contact: str,restaurant_name: str,date_time: str,guests: int) -> dict:
    """
    Books a reservation if availability exists.
    
    Args:
        user_name (str): Name of the user making the reservation.
        user_contact (str): Contact number of the user.
        restaurant_name (str): Name of the restaurant.
        date_time (str): Reservation datetime in ISO format.
        guests (int): Number of guests.
    
    Returns:
        dict: {
            "success": bool,
            "message": str,
            "reservation_details": dict or None
        }
    """
    db = next(get_db())
    print(f"get_db is callable? {callable(get_db)}")

    date_time_obj = datetime.fromisoformat(date_time)

    restaurant = (
        db.query(Restaurant)
        .filter(Restaurant.name.ilike(f"%{restaurant_name}%"))
        .first()
    )

    if not restaurant:
        return {
            "success": False,
            "message": f"No restaurant found named '{restaurant_name}'.",
            "reservation_details": None
        }


    start_time = date_time_obj - timedelta(hours=1)
    end_time = date_time_obj + timedelta(hours=1)

    existing_reservations = (
        db.query(Reservation)
        .filter(
            Reservation.restaurant_id == restaurant.id,
            Reservation.reservation_time >= start_time,
            Reservation.reservation_time <= end_time
        )
        .all()
    )

    total_guests = sum(res.guests for res in existing_reservations)

    if total_guests + guests > restaurant.seating_capacity:
        return {
            "success": False,
            "message": "Selected time slot is full. Please try a different time.",
            "reservation_details": None
        }

    
    new_reservation = Reservation(
        user_name=user_name,
        user_contact=user_contact,
        restaurant_id=restaurant.id,
        reservation_time=date_time_obj,
        guests=guests
    )
    db.add(new_reservation)
    db.commit()
    db.refresh(new_reservation)

    return {
        "success": True,
        "message": f"Reservation confirmed at {restaurant.name}!",
        "reservation_details": {
            "restaurant": restaurant.name,
            "location": restaurant.location,
            "reservation_time": date_time_obj.strftime("%Y-%m-%d %H:%M"),
            "guests": guests,
            "contact": user_contact
        }
    }

@mcp.tool()
def cancel_reservation(reservation_id: int = None,user_contact: str = None,restaurant_name: str = None,date_time: str = None) -> dict:
    """
    Cancels a reservation by reservation ID or by contact + restaurant + datetime.
    
    Args:
        reservation_id (int, optional): Unique ID of the reservation to cancel.
        user_contact (str, optional): Contact number of the user.
        restaurant_name (str, optional): Name of the restaurant.
        date_time (str, optional): Reservation datetime in ISO format.
    
    Returns:
        dict: {
            "success": bool,
            "message": str
        }
    """
   
    db = next(get_db())
   
    if reservation_id:
        reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
        if not reservation:
            return {
                "success": False,
                "message": f"No reservation found with ID {reservation_id}."
            }

    
    elif user_contact and restaurant_name and date_time:
        date_time_obj = datetime.fromisoformat(date_time)

        restaurant = (
            db.query(Restaurant)
            .filter(Restaurant.name.ilike(f"%{restaurant_name}%"))
            .first()
        )

        if not restaurant:
            return {
                "success": False,
                "message": f"No restaurant found named '{restaurant_name}'."
            }

        reservation = (
            db.query(Reservation)
            .filter(
                Reservation.user_contact == user_contact,
                Reservation.restaurant_id == restaurant.id,
                Reservation.reservation_time == date_time_obj
            )
            .first()
        )

        if not reservation:
            return {
                "success": False,
                "message": "No matching reservation found with the given details."
            }

    else:
        return {
            "success": False,
            "message": "Please provide either reservation ID or (contact, restaurant, and datetime)."
        }

    db.delete(reservation)
    db.commit()

    return {
        "success": True,
        "message": f"Reservation successfully canceled for {reservation.user_name} at {reservation.reservation_time.strftime('%Y-%m-%d %H:%M')}."
    }

@mcp.tool()
def submit_feedback(reservation_id: int, rating: float = None, comments: str = None) -> dict:
    """
    Records user feedback for a specific reservation.
    
    Args:
        reservation_id (int): ID of the reservation the feedback is linked to.
        rating (float, optional): User rating (e.g., 4.0 out of 5).
        comments (str, optional): Additional comments or suggestions from the user.
    
    Returns:
        dict: {
            "success": bool,
            "message": str
        }
    """
    db = next(get_db())
    
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        return {
            "success": False,
            "message": f"No reservation found with ID {reservation_id}."
        }


    feedback = UserFeedback(
        reservation_id=reservation_id,
        rating=rating,
        comments=comments
    )
    db.add(feedback)
    db.commit()

    return {
        "success": True,
        "message": "Thank you for your feedback! It has been recorded successfully."
    }




# def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    
#     sse = SseServerTransport("/messages/")

#     async def handle_sse(request: Request) -> None:
#         async with sse.connect_sse(
#                 request.scope,
#                 request.receive,
#                 request._send,
#         ) as (read_stream, write_stream):
#             await mcp_server.run(
#                 read_stream,
#                 write_stream,
#                 mcp_server.create_initialization_options(),
#             )

#     return Starlette(
#         debug=debug,
#         routes=[
#             Route("/sse", endpoint=handle_sse),
#             Mount("/messages/", app=sse.handle_post_message),
#         ],
#     )



# if __name__ == "__main__":
#     mcp_server = mcp._mcp_server
    
#     starlette_app = create_starlette_app(mcp_server, debug=True)
#     port = 9090
#     print(f"Starting MCP server with SSE transport on port {port}...")
#     print(f"SSE endpoint available at: http://localhost:{port}/sse")
    
#     uvicorn.run(starlette_app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    mcp.run(transport="stdio")