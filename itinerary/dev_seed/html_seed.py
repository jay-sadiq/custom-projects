import os
import re
from datetime import date, timedelta

from bs4 import BeautifulSoup

from itinerary.models import Trip, TripAttendee, DayItinerary, StopBlock, ChecklistItem, Booking

def clean_text(text):
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def parse_day_html(file_path):
    print(f"Parsing {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')
    
    # 1. Parse Day Number & Theme
    day_badge = soup.select_one('.day-badge')
    day_badge_text = day_badge.text if day_badge else ""
    # Extract day number (e.g., "Day 5 of 11")
    day_num = 1
    day_num_match = re.search(r'Day\s+(\d+)', day_badge_text, re.IGNORECASE)
    if day_num_match:
        day_num = int(day_num_match.group(1))
    
    # Extract date if possible, else default to offset from start
    # e.g., "Mon 29 Jun" or "Thursday, June 25"
    
    header_h1 = soup.select_one('.day-header h1')
    theme = clean_text(header_h1.text) if header_h1 else ""
    
    early_banner = soup.select_one('.early-banner')
    early_start_banner = clean_text(early_banner.text) if early_banner else ""
    
    # 2. Parse Stop Colors from Javascript stops array
    # Look for scripts containing stops
    scripts = soup.find_all('script')
    stop_colors = []
    color_var_map = {}
    
    for scr in scripts:
        if scr.string and 'stops=[' in scr.string.replace(' ', ''):
            scr_text = scr.string
            # Find any color variables like var A='#E67E22'; or var A = "#27AE60";
            color_vars = re.findall(r'var\s+([A-Za-z0-9_]+)\s*=\s*[\'"](#[a-fA-F0-9]{6})[\'"]', scr_text)
            for var_name, var_val in color_vars:
                color_var_map[var_name] = var_val
            
            # Find the stops definition block
            stops_block_match = re.search(r'stops\s*=\s*\[(.*?)\]', scr_text, re.DOTALL)
            if stops_block_match:
                stops_content = stops_block_match.group(1)
                # Find color assignments like col: '#27AE60' or col: A or col: '#E67E22'
                cols = re.findall(r'col:\s*([A-Za-z0-9_\'\"#]+)', stops_content)
                for c in cols:
                    c = c.strip("'\"")
                    if c in color_var_map:
                        stop_colors.append(color_var_map[c])
                    elif c.startswith('#'):
                        stop_colors.append(c)
                    else:
                        # Fallback for dynamic variables not captured
                        stop_colors.append('#E67E22')
            break

    # 3. Parse Stop Blocks
    stop_blocks_html = soup.select('.stop-block')
    stops = []
    
    for idx, block in enumerate(stop_blocks_html):
        lat = float(block.get('data-lat', 0.0))
        lng = float(block.get('data-lng', 0.0))
        zoom = int(block.get('data-zoom', 15))
        stop_idx = int(block.get('data-stop-idx', idx))
        
        stime_el = block.select_one('.stime')
        time_label = clean_text(stime_el.text) if stime_el else ""
        
        stitle_el = block.select_one('.stitle')
        title = clean_text(stitle_el.text) if stitle_el else ""
        
        sdesc_el = block.select_one('.sdesc')
        description = clean_text(sdesc_el.text) if sdesc_el else ""
        
        # Parse tags
        tags = [clean_text(tag.text) for tag in block.select('.tags .tag, .tags span.tag')]
        if not tags:
            # Check for generic .tag elements
            tags = [clean_text(tag.text) for tag in block.select('.tag')]
            
        # Parse meal details from .mbox if present
        meal_type = ""
        meal_name = ""
        meal_desc = ""
        meal_price_label = ""
        meal_rec = ""
        
        mbox = block.select_one('.mbox')
        if mbox:
            mtype_el = mbox.select_one('.mtype')
            if mtype_el:
                mtype_raw = clean_text(mtype_el.text)
                # Split emoji/type and price, e.g. "🍳 Breakfast ~0 AZN (flight food)"
                # Let's clean the price from mprice element if it's there
                mprice_el = mtype_el.select_one('.mprice')
                if mprice_el:
                    meal_price_label = clean_text(mprice_el.text)
                    mprice_el.decompose() # remove it so we can clean type
                mtype_raw = clean_text(mtype_el.text)
                
                # Extract meal type: Breakfast, Lunch, Dinner, Snack
                for t in ['Breakfast', 'Lunch', 'Dinner', 'Snack', 'Coffee']:
                    if t.lower() in mtype_raw.lower():
                        meal_type = t
                        break
                if not meal_type:
                    meal_type = "Meal"
            
            mname_el = mbox.select_one('.mname')
            meal_name = clean_text(mname_el.text) if mname_el else ""
            
            mdesc_el = mbox.select_one('.mdesc')
            meal_desc = clean_text(mdesc_el.text) if mdesc_el else ""
            
            mrec_el = mbox.select_one('.mrec')
            meal_rec = clean_text(mrec_el.text) if mrec_el else ""
            
        # Determine color
        color_hex = '#E67E22'
        if stop_idx < len(stop_colors):
            color_hex = stop_colors[stop_idx]
        elif block.select_one('.snum.home'):
            color_hex = '#27AE60' # Green for home/base
            
        # Clean tags to exclude meal pricing tag elements
        tags = [t for t in tags if not t.startswith('~') and 'AZN' not in t]
        
        stops.append({
            'sequence_order': stop_idx + 1,
            'time_label': time_label,
            'title': title,
            'description': description,
            'latitude': lat,
            'longitude': lng,
            'zoom_level': zoom,
            'meal_type': meal_type,
            'meal_name': meal_name,
            'meal_desc': meal_desc,
            'meal_price_label': meal_price_label,
            'meal_recommendation': meal_rec,
            'tags': tags,
            'color_hex': color_hex
        })
        
    return {
        'day_number': day_num,
        'theme': theme,
        'early_start_banner': early_start_banner,
        'stops': stops
    }

def seed_from_html(user, source_dir):
    if not os.path.exists(source_dir):
        raise FileNotFoundError(f"Source directory {source_dir} not found.")
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
    
    # Overwrite if exists to make it perfectly sync
    print("Clearing old days, attendees and checklists to seed from HTML files...")
    trip.days.all().delete()
    trip.checklist_items.all().delete()
    trip.attendees.all().delete()
    
    trip.start_date = date(2026, 6, 25)
    trip.end_date = date(2026, 7, 5)
    trip.currency = 'AZN'
    trip.conversion_rate = 1.70
    trip.save()

    # Create Attendees
    TripAttendee.objects.create(trip=trip, name="Abdul Jawad", role="Husband")
    TripAttendee.objects.create(trip=trip, name="Wife", role="Wife")
    TripAttendee.objects.create(trip=trip, name="Eesa", role="Toddler (3yo)")

    # Read and parse day1.html to day11.html
    for i in range(1, 12):
        file_path = os.path.join(source_dir, f"day{i}.html")
        if os.path.exists(file_path):
            day_data = parse_day_html(file_path)
            
            day_num = day_data['day_number']
            day_date = trip.start_date + timedelta(days=day_num - 1)
            
            day_itinerary = DayItinerary.objects.create(
                trip=trip,
                day_number=day_num,
                date=day_date,
                theme=day_data['theme'],
                early_start_banner=day_data['early_start_banner']
            )
            
            for stop in day_data['stops']:
                StopBlock.objects.create(
                    day=day_itinerary,
                    sequence_order=stop['sequence_order'],
                    time_label=stop['time_label'],
                    title=stop['title'],
                    description=stop['description'],
                    latitude=stop['latitude'],
                    longitude=stop['longitude'],
                    zoom_level=stop['zoom_level'],
                    meal_type=stop['meal_type'],
                    meal_name=stop['meal_name'],
                    meal_desc=stop['meal_desc'],
                    meal_price_label=stop['meal_price_label'],
                    meal_recommendation=stop['meal_recommendation'],
                    tags=stop['tags'],
                    color_hex=stop['color_hex']
                )
        else:
            print(f"Warning: File {file_path} not found.")

    # Create checklist items from essentials
    ChecklistItem.objects.create(trip=trip, category="Preparation", item_text="Apply for Azerbaijan ASAN eVisa")
    ChecklistItem.objects.create(trip=trip, category="Preparation", item_text="Download Bolt app & register card")
    ChecklistItem.objects.create(trip=trip, category="Preparation", item_text="Exchange local AZN Cash (机场 or 28 May area)")
    ChecklistItem.objects.create(trip=trip, category="Packing List", item_text="Carry a compact stroller for Eesa")
    ChecklistItem.objects.create(trip=trip, category="Packing List", item_text="Bring hats, sunblock & summer hydration packs")
    ChecklistItem.objects.create(trip=trip, category="Packing List", item_text="Pack light jackets for Shahdag & Gabala mountain days")
    
    # Add Bookings
    Booking.objects.get_or_create(
        trip=trip, booking_type="Hotel", title="Baku Airbnb @ 28 May area",
        defaults={
            'confirmation_number': 'HM3X2YA8',
            'details': 'Check-in: June 25 3:00 PM, Check-out: July 5 11:00 AM',
            'cost': 450.00
        }
    )
    Booking.objects.get_or_create(
        trip=trip, booking_type="Flight", title="TK 337 (IST -> GYD) Flight",
        defaults={
            'confirmation_number': 'L5G3HX9',
            'details': 'June 25, Departure 10:30 AM, Arrival 2:00 PM',
            'cost': 380.00
        }
    )

    print(f"Successfully seeded database from all HTML files! Baku Trip contains {trip.days.count()} days.")
    return trip
