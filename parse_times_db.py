import os
import django
import re
from datetime import datetime, date, time, timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.dev")
django.setup()

from itinerary.models import DayItinerary, StopBlock

def parse_time_label(label):
    if not label:
        return None
    # check for HH:MM AM/PM
    match = re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)', label)
    if match:
        h = int(match.group(1))
        m = int(match.group(2))
        ampm = match.group(3).lower()
        if ampm == 'pm' and h < 12:
            h += 12
        if ampm == 'am' and h == 12:
            h = 0
        return time(h, m)
    
    # check for H AM/PM (e.g. 7 AM)
    match2 = re.search(r'(\d{1,2})\s*(AM|PM|am|pm)', label)
    if match2:
        h = int(match2.group(1))
        ampm = match2.group(2).lower()
        if ampm == 'pm' and h < 12:
            h += 12
        if ampm == 'am' and h == 12:
            h = 0
        return time(h, 0)
    
    label_lower = label.lower()
    if 'noon' in label_lower:
        return time(12, 0)
    if 'morning' in label_lower:
        return time(9, 0)
    if 'evening' in label_lower:
        return time(18, 0)
    if 'night' in label_lower:
        return time(20, 0)
    return None

def run():
    print("Updating stop block times...")
    for day in DayItinerary.objects.all().prefetch_related('stops'):
        print(f"Day {day.day_number}:")
        current_dt = datetime.combine(date.today(), time(9, 0))
        
        for stop in day.stops.all():
            parsed = parse_time_label(stop.time_label)
            if parsed:
                # If we parsed a time, use it
                start_dt = datetime.combine(date.today(), parsed)
                # If it's earlier than the previous stop's start, and it's the same day,
                # we let it be, but let's make sure it's at least progressive if possible
                # actually, let's trust the parsed time.
            else:
                # Use current_dt as start
                start_dt = current_dt
            
            # Default duration: 1.5 hours
            duration = timedelta(hours=1, minutes=30)
            
            # Let's adjust duration based on some keywords
            if 'dinner' in stop.title.lower() or 'dinner' in stop.description.lower():
                duration = timedelta(hours=2)
            elif 'lunch' in stop.title.lower() or 'brunch' in stop.title.lower():
                duration = timedelta(hours=1, minutes=30)
            elif 'drive' in stop.title.lower() or 'transfer' in stop.title.lower() or '→' in stop.title:
                duration = timedelta(hours=2, minutes=30)
            elif 'quick' in stop.description.lower() or 'photo' in stop.description.lower():
                duration = timedelta(minutes=45)
            
            end_dt = start_dt + duration
            
            stop.start_time_of_day = start_dt.time()
            stop.end_time_of_day = end_dt.time()
            
            # Also regenerate time_label to match the start/end times if we want,
            # or keep the original. The original is nice, but we can format it dynamically too.
            # Let's keep it but update database fields
            stop.save()
            print(f"  - Stop {stop.sequence_order}: {stop.title} | {stop.start_time_of_day} - {stop.end_time_of_day}")
            
            # Next stop starts 15 mins after this one ends, by default
            current_dt = end_dt + timedelta(minutes=15)

if __name__ == '__main__':
    run()
