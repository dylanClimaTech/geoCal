#will hold all of the gis funcitons
#buffer
#sum
#intersect
#union

from icalendar import Calendar,Event
from datetime import datetime,date,time,timedelta
import pytz
#will take in a calendar object and return a calendar object
#will have a seperate save function

class calend:
    def __init__(self):
        pass

    def validate(self,inp):
        #if passed as a file open the file and read the contents return the input
        if type(inp) == str:
            try:
                with open(inp,'r') as f:            
                    base = self.sort(Calendar.from_ical(f.read()))
                    for event in base:
                        self.update_event_times(event)
                    return base
            except:
                return inp
        return inp

    def get_event_start(self, event):
        start_time = event.get('dtstart').dt
        # If it's a date, convert to datetime assuming midnight
        if isinstance(start_time, date) and not isinstance(start_time, datetime):
            start_time = datetime.combine(start_time, time())
        # If the datetime is offset-aware, convert it to UTC and then make it offset-naive
        if start_time.tzinfo is not None and start_time.tzinfo.utcoffset(start_time) is not None:
            start_time = start_time.astimezone(pytz.utc).replace(tzinfo=None)
        return start_time

    def sort(self, inp):
        events = [event for event in inp.walk('vevent')]
        sorted_events = sorted(events, key=self.get_event_start)
        return sorted_events
    def update_event_times(self, event):
        start_time = event.get('dtstart').dt
        end_time = event.get('dtend').dt

        if isinstance(start_time, datetime) or isinstance(start_time, date):
            start_time = start_time.strftime('%Y-%m-%d %H:%M')
        if isinstance(end_time, datetime) or isinstance(end_time, date):
            end_time = end_time.strftime('%Y-%m-%d %H:%M')

        start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M')
        end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M')

        # Update the event object
        event['dtstart'] = start_time
        event['dtend'] = end_time

    def print_event_timeline(self,ics_content):
        # Parse the ICS content
                
        cal = self.validate(ics_content)
        #cal = self.validate(ics_content)
        # Header
        print("Timeline:")
        print("=" * 50)
        # Iterate through events, extract the title and datetime, and print them
        for event in cal:
            summary = event.get('summary')
            start_time = event.get('dtstart').dt
            if isinstance(start_time, datetime): # Check if it's a datetime object
                start_time = start_time.strftime('%Y-%m-%d %H:%M')

            print(f"| {start_time} |---- {summary}")

        print("=" * 50)  # Footer
    
    def print_top_n(self,ics_content,n=5):
        cal = self.validate(ics_content)
        for event in cal[len(cal)-n:]:
            summary = event.get('summary')
            start_time = event.get('dtstart')
            end_time = event.get('dtend')
            location = event.get('location')

            # Print the details in a visually appealing way
            print("-" * 50)  # Separator
            print(f"| {start_time} - {end_time} |---- {summary}")
            if location:
                print(f"|    Location: {location}")
            
            print("-" * 50)  # Separator
            print("|")
            print("")
            print("|")

    def save_to_ics(self, sorted_events, file_path):
        # Create a new iCalendar object
        cal = Calendar()
        # Add some standard properties to the calendar (you can customize these)
        cal.add('prodid', '-//Your Product//')
        cal.add('version', '2.0')

        # Add the sorted events to the calendar
        for event in sorted_events:
            cal.add_component(event)

        # Write the calendar to the specified file
        with open(file_path, 'wb') as f:
            f.write(cal.to_ical())

        print(f"Saved to {file_path}")
    
    def buffer(self,ics_content,buffer_time=15):
        cal = self.validate(ics_content)
        for event in cal:
            event['dtstart'] = event.get('dtstart') - timedelta(minutes=buffer_time)
            event['dtend'] = event.get('dtend') + timedelta(minutes=buffer_time)
        return cal
    
    def sum(self,ics_content):
        cal = self.validate(ics_content)
        total = 0
        for event in cal:
            total += (event.get('dtend') - event.get('dtstart')).total_seconds()
        total /= 60
        return total

    def union(self, ics_content_1, ics_content_2):
        cal1 = self.validate(ics_content_1)
        cal2 = self.validate(ics_content_2)
        
        union_events = []

        # Check all events in cal1 against all events in cal2
        for event1 in cal1:
            start1, end1 = event1.get('dtstart').dt, event1.get('dtend').dt
            summary1 = event1.get('summary')

            # Track whether the event was merged
            merged = False

            for event2 in cal2:
                start2, end2 = event2.get('dtstart').dt, event2.get('dtend').dt
                summary2 = event2.get('summary')

                # Check for overlap
                if start1 < end2 and start2 < end1:
                    # Merge the overlapping events
                    union_start = min(start1, start2)
                    union_end = max(end1, end2)
                    union_summary = f"{summary1}; {summary2}"

                    union_event = Event()
                    union_event.add('dtstart', union_start)
                    union_event.add('dtend', union_end)
                    union_event.add('summary', union_summary)

                    union_events.append(union_event)

                    # Mark the event as merged and break from loop
                    merged = True
                    break

            # If the event wasn't merged, add it to the union list
            if not merged:
                union_events.append(event1)

        # Add non-overlapping events from cal2
        for event2 in cal2:
            if not any(self.overlaps(event2, event1) for event1 in cal1):
                union_events.append(event2)

        # Create the final calendar
        union_cal = Calendar()
        union_cal.add('prodid', '-//Your Organization//')
        union_cal.add('version', '2.0')
        for event in union_events:
            union_cal.add_component(event)

        return union_cal

    def overlaps(self, event1, event2):
        start1, end1 = event1.get('dtstart').dt, event1.get('dtend').dt
        start2, end2 = event2.get('dtstart').dt, event2.get('dtend').dt
        return start1 < end2 and start2 < end1


    def intersect(self, ics_content_1, ics_content_2):
        cal1 = self.validate(ics_content_1)
        cal2 = self.validate(ics_content_2)
        
        intersect_events = []

        # Check all events in cal1 against all events in cal2
        for event1 in cal1:
            start1, end1 = event1.get('dtstart').dt, event1.get('dtend').dt
            summary1 = event1.get('summary')

            for event2 in cal2:
                start2, end2 = event2.get('dtstart').dt, event2.get('dtend').dt
                summary2 = event2.get('summary')

                # Check for overlap
                if start1 < end2 and start2 < end1:
                    # Create an intersect event for the overlapping period
                    intersect_start = max(start1, start2)
                    intersect_end = min(end1, end2)
                    intersect_summary = f"{summary1}; {summary2}"

                    intersect_event = Event()
                    intersect_event.add('dtstart', intersect_start)
                    intersect_event.add('dtend', intersect_end)
                    intersect_event.add('summary', intersect_summary)

                    intersect_events.append(intersect_event)

        # Create the final calendar
        intersect_cal = Calendar()
        intersect_cal.add('prodid', '-//Your Organization//')
        intersect_cal.add('version', '2.0')
        for event in intersect_events:
            intersect_cal.add_component(event)

        return intersect_cal
