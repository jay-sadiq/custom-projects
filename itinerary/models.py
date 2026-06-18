from django.db import models
from django.contrib.auth.models import User

class Trip(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="trips", null=True, blank=True)
    title = models.CharField(max_length=200, default="My Family Adventure")
    destination = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    currency = models.CharField(max_length=10, default="USD")
    conversion_rate = models.DecimalField(max_digits=10, decimal_places=4, default=1.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    @property
    def duration_days(self):
        return (self.end_date - self.start_date).days + 1

    @property
    def total_cost_local(self):
        # Sum cost of all stops in local currency
        stops_cost = sum(stop.cost_local for day in self.days.all() for stop in day.stops.all())
        # Sum booking costs if applicable
        bookings_cost = sum(booking.cost for booking in self.bookings.all() if booking.cost)
        return stops_cost + bookings_cost

    @property
    def total_cost_usd(self):
        return self.total_cost_local / self.conversion_rate

class TripAttendee(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="attendees")
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100, help_text="e.g., Husband, Wife, Toddler (3yo)")

    def __str__(self):
        return f"{self.name} ({self.role})"

class DayItinerary(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="days")
    day_number = models.PositiveIntegerField()
    date = models.DateField()
    theme = models.CharField(max_length=200, blank=True, help_text="e.g., Arrival & The Green Bazaar")
    early_start_banner = models.CharField(max_length=300, blank=True)
    notes = models.TextField(blank=True, help_text="User's personal saved notes for this day")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['day_number']
        unique_together = ('trip', 'day_number')

    def __str__(self):
        return f"Trip {self.trip.id} - Day {self.day_number}: {self.theme or 'Untitled'}"

    @property
    def day_cost_local(self):
        return sum(stop.cost_local for stop in self.stops.all())

    @property
    def day_cost_usd(self):
        return sum(stop.cost_usd for stop in self.stops.all())

class StopBlock(models.Model):
    MEAL_CHOICES = [
        ('Breakfast', 'Breakfast'),
        ('Lunch', 'Lunch'),
        ('Dinner', 'Dinner'),
        ('Snack', 'Snack'),
    ]
    day = models.ForeignKey(DayItinerary, on_delete=models.CASCADE, related_name="stops")
    sequence_order = models.PositiveIntegerField()
    time_label = models.CharField(max_length=100, help_text="e.g., 1:30 PM — First stop")
    title = models.CharField(max_length=200)
    description = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    zoom_level = models.PositiveIntegerField(default=15)
    
    # Time Coordination
    start_time_of_day = models.TimeField(null=True, blank=True, help_text="e.g. 13:30:00")
    end_time_of_day = models.TimeField(null=True, blank=True, help_text="e.g. 15:00:00")

    @property
    def calendar_top(self):
        start_mins = self.start_time_of_day.hour * 60 + self.start_time_of_day.minute if self.start_time_of_day else 540
        # 06:00 AM is 360 mins. Each minute is 80/60 px.
        mins_from_start = start_mins - 360
        if mins_from_start < 0:
            mins_from_start = 0
        return int(mins_from_start * 80 / 60)

    @property
    def calendar_height(self):
        start_mins = self.start_time_of_day.hour * 60 + self.start_time_of_day.minute if self.start_time_of_day else 540
        end_mins = self.end_time_of_day.hour * 60 + self.end_time_of_day.minute if self.end_time_of_day else 630
        duration = end_mins - start_mins
        if duration < 30: # minimum 30 mins
            duration = 30
        return int(duration * 80 / 60)

    # Cost Tracking
    cost_local = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    cost_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Optional Meal Details
    meal_type = models.CharField(max_length=50, blank=True, choices=MEAL_CHOICES)
    meal_name = models.CharField(max_length=200, blank=True)
    meal_desc = models.TextField(blank=True)
    meal_price_label = models.CharField(max_length=100, blank=True)
    meal_recommendation = models.TextField(blank=True, help_text="e.g. Tip for Eesa or menu recommendation")
    
    # Metadata
    tags = models.JSONField(default=list, blank=True, help_text="List of string badges")
    color_hex = models.CharField(max_length=7, default="#E67E22", help_text="Color for map marker")

    class Meta:
        ordering = ['sequence_order']

    def __str__(self):
        return f"Day {self.day.day_number} - Stop {self.sequence_order}: {self.title}"

class Booking(models.Model):
    BOOKING_TYPES = [
        ('Flight', 'Flight'),
        ('Hotel', 'Hotel/Airbnb'),
        ('Activity', 'Activity/Driver'),
        ('Restaurant', 'Restaurant'),
    ]
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="bookings")
    booking_type = models.CharField(max_length=50, choices=BOOKING_TYPES)
    title = models.CharField(max_length=200)
    confirmation_number = models.CharField(max_length=100, blank=True)
    details = models.TextField(blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    attachment = models.FileField(upload_to="bookings/", blank=True, null=True)

    def __str__(self):
        return f"{self.booking_type} - {self.title}"

class ChecklistItem(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="checklist_items")
    category = models.CharField(max_length=100, default="Packing List")
    item_text = models.CharField(max_length=255)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category}: {self.item_text} ({'Done' if self.is_completed else 'Pending'})"

class PlaceDetail(models.Model):
    stop = models.OneToOneField(StopBlock, on_delete=models.CASCADE, related_name="place_detail")
    place_id = models.CharField(max_length=255, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    reviews_json = models.JSONField(default=list, blank=True, help_text="Cache of 10 recent reviews")
    photos_json = models.JSONField(default=list, blank=True, help_text="Cache of image URLs")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Place details for {self.stop.title}"

class StopPhoto(models.Model):
    stop = models.ForeignKey(StopBlock, on_delete=models.CASCADE, related_name="user_photos")
    image = models.ImageField(upload_to="stops/photos/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo {self.id} for {self.stop.title}"

