#!/usr/bin/env python
import os
import django
import sys
from datetime import datetime, date, timedelta

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.dev")
django.setup()

from django.contrib.auth import get_user_model

from itinerary.models import Trip, TripAttendee, DayItinerary, StopBlock, ChecklistItem, Booking


def _seed_user():
    User = get_user_model()
    user = User.objects.filter(is_superuser=True).first() or User.objects.first()
    if user is None:
        user = User.objects.create_superuser("admin", "", "admin")
    return user


def seed_itinerary():
    print("Seeding Baku Family Itinerary 2026...")
    user = _seed_user()

    # 1. Create Trip
    trip, created = Trip.objects.get_or_create(
        title="🇦🇿 Baku Family Adventure 2026",
        destination="Baku, Azerbaijan",
        user=user,
        defaults={
            'start_date': date(2026, 6, 25),
            'end_date': date(2026, 7, 5),
            'currency': 'AZN',
            'conversion_rate': 1.70
        }
    )
    if not created:
        print("Trip already exists. Overwriting details...")
        trip.days.all().delete()
        trip.checklist_items.all().delete()
        trip.attendees.all().delete()
        trip.start_date = date(2026, 6, 25)
        trip.end_date = date(2026, 7, 5)
        trip.currency = 'AZN'
        trip.conversion_rate = 1.70
        trip.save()

    # 2. Add Attendees
    TripAttendee.objects.create(trip=trip, name="Abdul Jawad", role="Husband")
    TripAttendee.objects.create(trip=trip, name="Wife", role="Wife")
    TripAttendee.objects.create(trip=trip, name="Eesa", role="Toddler (3yo)")

    # 3. Add Days & Stops
    # Day 1
    d1 = DayItinerary.objects.create(
        trip=trip, day_number=1, date=date(2026, 6, 25),
        theme="Arrival & The Green Bazaar"
    )
    StopBlock.objects.create(
        day=d1, sequence_order=1, time_label="Noon — Settle in",
        title="Airbnb — 28 May area",
        description="Check in to the Airbnb at 28 May. Drop bags, freshen up, get your bearings. The Metro is right outside, with cafes and pharmacies close by.",
        latitude=40.3777, longitude=49.8467, zoom_level=15,
        cost_local=0.00, cost_usd=0.00, tags=["28 May metro outside", "ATMs nearby"],
        color_hex="#27AE60"
    )
    StopBlock.objects.create(
        day=d1, sequence_order=2, time_label="1:30 PM — First stop",
        title="Bravo Supermarket & Yashil Bazar",
        description="Stock the Airbnb fridge. Bravo has excellent fresh produce. Yashil Bazar has honey, herbs, and pomegranate juice at low prices.",
        latitude=40.3755, longitude=49.8488, zoom_level=15,
        cost_local=40.00, cost_usd=24.00, tags=["groceries", "5 min walk"],
        meal_type="Breakfast", meal_name="Roadside grocery shopping", meal_desc="Buy eggs, local yogurt, bread, and fruits for tomorrow.",
        color_hex="#E67E22"
    )
    StopBlock.objects.create(
        day=d1, sequence_order=3, time_label="3:00 PM — First meal",
        title="Nizami Street — Döner & Stroll",
        description="Walk down Nizami Street, Baku's pedestrian European high street. Try Baku-style chicken döner on thick bread.",
        latitude=40.3760, longitude=49.8430, zoom_level=15,
        cost_local=20.00, cost_usd=12.00, tags=["lunch/dinner", "Nizami street", "pedestrian"],
        meal_type="Lunch", meal_name="Baku Döner Shop", meal_desc="Order chicken döner (toyuq döner) and fresh ayran.",
        meal_recommendation="For Eesa: ask for bread to be cut open, filling served on side.",
        color_hex="#E67E22"
    )
    StopBlock.objects.create(
        day=d1, sequence_order=4, time_label="4:00 PM — Coffee stop",
        title="Friends Tarqovaya — Coffee & Cakes",
        description="Cozy cafe branch known for specialty coffees, excellent hot chocolates, and shaded terrace.",
        latitude=40.3693, longitude=49.8348, zoom_level=16,
        cost_local=18.00, cost_usd=11.00, tags=["M.Rasulzada 5", "toddler-friendly"],
        meal_type="Snack", meal_name="Friends Tarqovaya", meal_desc="Flat white, latte, fresh juice, and croissant.",
        color_hex="#8B4513"
    )
    StopBlock.objects.create(
        day=d1, sequence_order=5, time_label="5:30 PM — Evening",
        title="Fountain Square (Fəvvarələr Meydanı)",
        description="Elegant plaza surrounded by fountains and performing artists. Great for promenading and ice cream.",
        latitude=40.3699, longitude=49.8366, zoom_level=15,
        cost_local=8.00, cost_usd=5.00, tags=["fountains", "ice cream", "outdoor culture"],
        color_hex="#9B59B6"
    )
    StopBlock.objects.create(
        day=d1, sequence_order=6, time_label="7:00 PM — Night walk",
        title="Old City (İçərişəhər) — Night Walk",
        description="Enter through the main gate and wander the medieval limestone alleys lit by warm streetlamps. Quiet, safe, and historic.",
        latitude=40.3668, longitude=49.8358, zoom_level=16,
        cost_local=5.00, cost_usd=3.00, tags=["medieval alleys", "UNESCO walls", "Bolt taxi home"],
        color_hex="#1A252F"
    )

    # Day 2
    d2 = DayItinerary.objects.create(
        trip=trip, day_number=2, date=date(2026, 6, 26),
        theme="Friday Prayers, Deniz Mall & Chayki"
    )
    StopBlock.objects.create(
        day=d2, sequence_order=1, time_label="12:30 PM",
        title="🕌 Friday Prayers @ Teze Pir Mosque",
        description="Baku's largest historic mosque with beautiful gold domes and family courtyard. Built in 1914.",
        latitude=40.3722, longitude=49.8315, zoom_level=15,
        cost_local=0.00, cost_usd=0.00, tags=["Jumu'ah", "historic", "1914"],
        color_hex="#27AE60"
    )
    StopBlock.objects.create(
        day=d2, sequence_order=2, time_label="2:00 PM",
        title="Deniz Mall — Lunch & Toddler Play",
        description="Modern mall shaped like a Caspian lotus. Great indoor kids zones and lunch choices.",
        latitude=40.3585, longitude=49.8385, zoom_level=15,
        cost_local=40.00, cost_usd=24.00, tags=["shopping mall", "Caspian lotus", "kids zone"],
        meal_type="Lunch", meal_name="Deniz Mall Diner", meal_desc="Variety of choices inside mall.",
        color_hex="#1a6b9a"
    )
    StopBlock.objects.create(
        day=d2, sequence_order=3, time_label="4:00 PM",
        title="Little Venice & Baku Eye",
        description="Take boat rides on water canals and enjoy panoramic Caspian views on the giant Baku Eye Ferris wheel.",
        latitude=40.3601, longitude=49.8355, zoom_level=15,
        cost_local=15.00, cost_usd=9.00, tags=["Little Venice", "Ferris wheel", "Baku Boulevard"],
        color_hex="#2980B9"
    )
    StopBlock.objects.create(
        day=d2, sequence_order=4, time_label="7:00 PM",
        title="Chayki Restoran — Waterfront Family Dinner",
        description="Baku's premier waterfront dining spot with classic garden terrace. Known for fine Azerbaijani grills.",
        latitude=40.3557, longitude=49.8354, zoom_level=16,
        cost_local=140.00, cost_usd=82.00, tags=["luxury dinner", "waterfront", "Azerbaijani food"],
        meal_type="Dinner", meal_name="Chayki Fine Dining", meal_desc="Grilled sea bass, lamb chops, and fresh garden salad.",
        meal_recommendation="For Eesa: order plain grilled chicken breast with side of rice.",
        color_hex="#2980B9"
    )

    # Day 5 (Day Trip: Quba & Shahdag)
    d5 = DayItinerary.objects.create(
        trip=trip, day_number=5, date=date(2026, 6, 29),
        theme="Day Trip: Quba & Shahdag",
        early_start_banner="⏰ EARLY START — 7:00 AM departure. Pack tonight. Eesa sleeps in the car Baku → Quba."
    )
    StopBlock.objects.create(
        day=d5, sequence_order=1, time_label="7:00 AM — Early departure",
        title="Airbnb → Quba (170km, ~2.5 hrs)",
        description="Private driver checks in. Drive up into the Caucasus foothills. Eesa sleeps the entire route.",
        latitude=40.3777, longitude=49.8467, zoom_level=9,
        cost_local=200.00, cost_usd=118.00, tags=["private driver", "full day hire", "toddler sleeping"],
        meal_type="Breakfast", meal_name="Simit & Tea on the go", meal_desc="Simit sesame rings from 24h bakery near Airbnb.",
        color_hex="#27AE60"
    )
    StopBlock.objects.create(
        day=d5, sequence_order=2, time_label="9:30 AM — Mountain town",
        title="Quba Old Town — Carpet Workshop & Bazaar",
        description="600m altitude, cooler climate. Visit carpet workshop and local honey bazaar.",
        latitude=41.3608, longitude=48.5081, zoom_level=13,
        cost_local=50.00, cost_usd=30.00, tags=["cooler weather", "handicrafts", "organic honey"],
        meal_type="Breakfast", meal_name="Roadside Village breakfast", meal_desc="Lavash bread, village eggs, honey, mountain tea.",
        color_hex="#E67E22"
    )
    StopBlock.objects.create(
        day=d5, sequence_order=3, time_label="10:45 AM — Into the mountains",
        title="Afurja Waterfall",
        description="75m waterfall cascade through pine forests. A scenic gentle 30-minute walk to the base.",
        latitude=41.1608, longitude=48.6156, zoom_level=13,
        cost_local=0.00, cost_usd=0.00, tags=["75m falls", "spray mist", "bring light jacket"],
        meal_recommendation="For Eesa: bring a full change of clothes — spray at base gets everything wet.",
        color_hex="#2980B9"
    )
    StopBlock.objects.create(
        day=d5, sequence_order=4, time_label="12:30 PM — Forest stop",
        title="Qechresh Forest — Horse Riding for Eesa",
        description="Stunning ancient pine/oak forest canopy. roadside handlers offer calm horse riding for Eesa.",
        latitude=41.3219, longitude=48.3897, zoom_level=13,
        cost_local=15.00, cost_usd=9.00, tags=["oak forest", "horse ride", "kids fun"],
        color_hex="#1ABC9C"
    )
    StopBlock.objects.create(
        day=d5, sequence_order=5, time_label="1:30 PM — Shahdag Resort",
        title="Shahdag Mountain Resort — Cable Car & Adventure",
        description="Azerbaijan's premier ski resort. Take cable car to 2000m alpine zone. Temperatures are 15C cooler.",
        latitude=41.2700, longitude=48.0850, zoom_level=12,
        cost_local=150.00, cost_usd=88.00, tags=["cable car ride", "alpine zone", "ATV adventure"],
        meal_type="Lunch", meal_name="Resort grill trout lunch", meal_desc="Grilled trout, lamb shashlik, fresh water.",
        color_hex="#27AE60"
    )
    StopBlock.objects.create(
        day=d5, sequence_order=6, time_label="5:00 PM — Return drive",
        title="Drive back to Baku (~2.5 hrs)",
        description="Descending Caucasus mountains during golden hour. Easy return, order food delivery at Airbnb.",
        latitude=40.3777, longitude=49.8467, zoom_level=9,
        cost_local=25.00, cost_usd=15.00, tags=["return drive", "Wolt dinner"],
        meal_type="Dinner", meal_name="Wolt Delivery", meal_desc="Quick delivery dinner near Airbnb.",
        color_hex="#9B59B6"
    )

    # Add remaining days 3, 4, 6, 7, 8, 9, 10, 11 as summaries to populate structure
    remaining_days = [
        (3, "Café Baku & Sumqayit Beach", date(2026, 6, 27), "Café Baku breakfast · Caspian beach stroll · Zeytun waterfront dinner"),
        (4, "Zafferano Brunch & Flame Towers", date(2026, 6, 28), "Four Seasons brunch · Funicular ride · Flame Towers light show"),
        (6, "Spa, Koala Park & White City", date(2026, 6, 30), "Bubbles Baby Spa · Koala Park · White City waterfront stroll"),
        (7, "Day Trip: Shamakhi & Gabala", date(2026, 7, 1), "Shamakhi Juma Mosque · Tufandag cable car · Nohur Lake"),
        (8, "Bibi-Heybat Mosque & Shikhov Beach", date(2026, 7, 2), "Bibi-Heybat Mosque · Shikhov Caspian beach · Seafront fish dinner"),
        (9, "Jumu'ah, Shirvanshah Palace & Old City", date(2026, 7, 3), "Friday prayers Juma Mosque · UNESCO Palace · Maiden Tower stroll"),
        (10, "Nizami Street & Baku Boulevard", date(2026, 7, 4), "Chayki brunch · Little Venice gondolas · Nizami shopping · Central Baku"),
        (11, "Departure Day", date(2026, 7, 5), "Final neighbourhood stroll · Heydar Aliyev International Airport at 4 PM")
    ]

    for dnum, theme, ddate, desc in remaining_days:
        day_it = DayItinerary.objects.create(
            trip=trip, day_number=dnum, date=ddate, theme=theme
        )
        # Add basic placeholder stop
        StopBlock.objects.create(
            day=day_it, sequence_order=1, time_label="Day highlights",
            title=theme, description=desc,
            latitude=40.3777, longitude=49.8467, zoom_level=13,
            cost_local=100.00, cost_usd=59.00, tags=["family time", "highlights"],
            color_hex="#1a6fa8"
        )

    # 4. Add Checklist items
    ChecklistItem.objects.create(trip=trip, category="Preparation", item_text="Check passport validity (min 6 months)")
    ChecklistItem.objects.create(trip=trip, category="Preparation", item_text="Apply for Azerbaijan ASAN eVisa")
    ChecklistItem.objects.create(trip=trip, category="Preparation", item_text="Download Bolt app & register card")
    ChecklistItem.objects.create(trip=trip, category="Packing List", item_text="Compact travel stroller for Eesa")
    ChecklistItem.objects.create(trip=trip, category="Packing List", item_text="Toddler water bottles + travel hats")
    ChecklistItem.objects.create(trip=trip, category="Packing List", item_text="Windbreakers for Shahdag & Gabala mountains")
    ChecklistItem.objects.create(trip=trip, category="Packing List", item_text="Beachwear + towels for Shikhov/Sumqayit swim")

    # 5. Add Booking confirmations placeholders
    Booking.objects.create(
        trip=trip, booking_type="Hotel", title="Baku Airbnb @ 28 May area",
        confirmation_number="HM3X2YA8", details="Check-in: June 25 3:00 PM, Check-out: July 5 11:00 AM",
        cost=450.00
    )
    Booking.objects.create(
        trip=trip, booking_type="Flight", title="TK 337 (IST -> GYD) Flight",
        confirmation_number="L5G3HX9", details="June 25, Departure 10:30 AM, Arrival 2:00 PM",
        cost=380.00
    )

    print("Successfully seeded database! Baku Family Adventure 2026 is fully loaded.")

if __name__ == '__main__':
    seed_itinerary()
