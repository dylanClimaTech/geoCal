from icalendar import Calendar, Event
from datetime import datetime, date, time, timedelta
import pytz
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

class CalendarProcessor:
    def __init__(self):
        self.console = Console()

    def extract_datetime(self, dt_object):
        if hasattr(dt_object, 'dt'):
            return dt_object.dt
        return dt_object

    def validate(self, inp):
        if isinstance(inp, str):
            try:
                with open(inp, 'r') as f:
                    cal = Calendar.from_ical(f.read())
                    events = self.sort(cal.walk('vevent'))
                    for event in events:
                        self.update_event_times(event)
                    return events
            except Exception as e:
                self.console.print(f"[bold red]Error reading file:[/bold red] {e}")
                return []
        return inp if isinstance(inp, list) else []

    def get_event_start(self, event):
        start_time = event.get('dtstart').dt
        if isinstance(start_time, date) and not isinstance(start_time, datetime):
            start_time = datetime.combine(start_time, time())
        if start_time.tzinfo:
            start_time = start_time.astimezone(pytz.utc).replace(tzinfo=None)
        return start_time

    def sort(self, events):
        return sorted(events, key=self.get_event_start)

    def update_event_times(self, event):
        for key in ['dtstart', 'dtend']:
            dt = event.get(key).dt
            if isinstance(dt, (datetime, date)):
                event[key] = datetime.strptime(dt.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M')

    def print_event_timeline(self, ics_content):
        events = self.validate(ics_content)
        table = Table(title="Event Timeline")
        table.add_column("Start Time", style="cyan")
        table.add_column("Summary", style="magenta")

        for event in events:
            start_time = event.get('dtstart')
            if hasattr(start_time, 'dt'):
                start_time = start_time.dt
            if isinstance(start_time, datetime):
                start_time = start_time.strftime('%Y-%m-%d %H:%M')
            summary = event.get('summary', 'No summary')
            table.add_row(start_time, summary)

        self.console.print(table)

    def print_top_n(self, ics_content, n=5):
        events = self.validate(ics_content)[-n:]
        for event in events:
            summary = event.get('summary', 'No summary')
            start_time = event.get('dtstart')
            end_time = event.get('dtend')
            
            # Handle both datetime and vDDDType objects
            if hasattr(start_time, 'dt'):
                start_time = start_time.dt
            if hasattr(end_time, 'dt'):
                end_time = end_time.dt
            
            location = event.get('location', 'No location')

            panel = Panel(
                f"[cyan]Start:[/cyan] {start_time}\n"
                f"[cyan]End:[/cyan] {end_time}\n"
                f"[cyan]Location:[/cyan] {location}",
                title=f"[bold magenta]{summary}[/bold magenta]",
                expand=False
            )
            self.console.print(panel)

    def save_to_ics(self, events, file_path):
        cal = Calendar()
        cal.add('prodid', '-//CalendarProcessor//EN')
        cal.add('version', '2.0')
        for event in events:
            cal.add_component(event)

        with open(file_path, 'wb') as f:
            f.write(cal.to_ical())
        self.console.print(f"[green]Saved to {file_path}[/green]")

    def buffer(self, ics_content, buffer_time=15):
        events = self.validate(ics_content)
        for event in events:
            start_time = self.extract_datetime(event.get('dtstart'))
            end_time = self.extract_datetime(event.get('dtend'))
            event['dtstart'] = start_time - timedelta(minutes=buffer_time)
            event['dtend'] = end_time + timedelta(minutes=buffer_time)
        return events

    def sum_duration(self, ics_content):
        events = self.validate(ics_content)
        total_minutes = sum(
            (self.extract_datetime(event.get('dtend')) - self.extract_datetime(event.get('dtstart'))).total_seconds() / 60
            for event in events
        )
        hours, minutes = divmod(total_minutes, 60)
        self.console.print(f"[bold green]Total duration:[/bold green] {int(hours)} hours and {int(minutes)} minutes")
        return total_minutes

    def union(self, ics_content_1, ics_content_2):
        events1 = self.validate(ics_content_1)
        events2 = self.validate(ics_content_2)
        all_events = events1 + events2
        merged_events = []

        for event in sorted(all_events, key=self.get_event_start):
            if not merged_events or self.extract_datetime(event.get('dtstart')) > self.extract_datetime(merged_events[-1].get('dtend')):
                merged_events.append(event)
            else:
                last_event = merged_events[-1]
                last_event['dtend'] = max(self.extract_datetime(last_event.get('dtend')), self.extract_datetime(event.get('dtend')))
                last_event['summary'] = f"{last_event.get('summary')}; {event.get('summary')}"

        return merged_events

    def intersect(self, ics_content_1, ics_content_2):
        events1 = self.validate(ics_content_1)
        events2 = self.validate(ics_content_2)
        intersect_events = []

        for event1 in events1:
            for event2 in events2:
                start = max(self.extract_datetime(event1.get('dtstart')), self.extract_datetime(event2.get('dtstart')))
                end = min(self.extract_datetime(event1.get('dtend')), self.extract_datetime(event2.get('dtend')))
                if start < end:
                    intersect_event = Event()
                    intersect_event.add('dtstart', start)
                    intersect_event.add('dtend', end)
                    intersect_event.add('summary', f"{event1.get('summary')}; {event2.get('summary')}")
                    intersect_events.append(intersect_event)

        return intersect_events

    def find_free_slots(self, ics_content, min_duration=30):
        events = self.validate(ics_content)
        free_slots = []
        for i in range(len(events) - 1):
            end_current = self.extract_datetime(events[i].get('dtend'))
            start_next = self.extract_datetime(events[i+1].get('dtstart'))
            duration = (start_next - end_current).total_seconds() / 60
            if duration >= min_duration:
                free_slots.append((end_current, start_next))

        table = Table(title=f"Free Time Slots (Minimum {min_duration} minutes)")
        table.add_column("Start", style="cyan")
        table.add_column("End", style="magenta")
        table.add_column("Duration", style="green")

        for start, end in free_slots:
            duration = (end - start).total_seconds() / 60
            table.add_row(
                start.strftime('%Y-%m-%d %H:%M'),
                end.strftime('%Y-%m-%d %H:%M'),
                f"{int(duration)} minutes"
            )

        self.console.print(table)
        return free_slots

    def difference(self, ics_content_1, ics_content_2):
        events1 = self.validate(ics_content_1)
        events2 = self.validate(ics_content_2)
        return [e for e in events1 if e not in events2]

    def clip(self, ics_content, start_time, end_time):
        events = self.validate(ics_content)
        clipped_events = []
        for event in events:
            event_start = self.extract_datetime(event.get('dtstart'))
            event_end = self.extract_datetime(event.get('dtend'))
            if event_start < end_time and event_end > start_time:
                new_event = event.copy()
                new_event['dtstart'] = max(event_start, start_time)
                new_event['dtend'] = min(event_end, end_time)
                clipped_events.append(new_event)
        return clipped_events

    def dissolve(self, ics_content, attribute='summary'):
        events = self.validate(ics_content)
        dissolved_events = []
        for event in sorted(events, key=self.get_event_start):
            if not dissolved_events or \
               event.get(attribute) != dissolved_events[-1].get(attribute) or \
               self.extract_datetime(event.get('dtstart')) > self.extract_datetime(dissolved_events[-1].get('dtend')):
                dissolved_events.append(event)
            else:
                dissolved_events[-1]['dtend'] = max(self.extract_datetime(dissolved_events[-1].get('dtend')),
                                                    self.extract_datetime(event.get('dtend')))
        return dissolved_events

    def density(self, ics_content, time_unit='day'):
        events = self.validate(ics_content)
        if not events:
            return {}
        
        start = min(self.extract_datetime(e.get('dtstart')) for e in events)
        end = max(self.extract_datetime(e.get('dtend')) for e in events)
        
        density = {}
        current = start
        while current <= end:
            key = current.strftime('%Y-%m-%d') if time_unit == 'day' else current.strftime('%Y-%m-%d %H:00')
            density[key] = sum(1 for e in events if self.extract_datetime(e.get('dtstart')) <= current < self.extract_datetime(e.get('dtend')))
            if time_unit == 'day':
                current += timedelta(days=1)
            else:
                current += timedelta(hours=1)
        
        return density

    def symmetric_difference(self, ics_content_1, ics_content_2):
        events1 = set(self.validate(ics_content_1))
        events2 = set(self.validate(ics_content_2))
        return list(events1.symmetric_difference(events2))

    def simplify(self, ics_content, time_threshold=timedelta(minutes=30)):
        events = self.sort(self.validate(ics_content))
        simplified = []
        for event in events:
            if not simplified or (self.extract_datetime(event.get('dtstart')) - 
                                  self.extract_datetime(simplified[-1].get('dtend'))) > time_threshold:
                simplified.append(event)
            else:
                simplified[-1]['dtend'] = event.get('dtend')
                simplified[-1]['summary'] += f"; {event.get('summary')}"
        return simplified

    def spatial_join(self, ics_content_1, ics_content_2, attribute='location'):
        events1 = self.validate(ics_content_1)
        events2 = self.validate(ics_content_2)
        joined_events = []
        for event1 in events1:
            for event2 in events2:
                start = max(self.extract_datetime(event1.get('dtstart')), self.extract_datetime(event2.get('dtstart')))
                end = min(self.extract_datetime(event1.get('dtend')), self.extract_datetime(event2.get('dtend')))
                if start < end:
                    joined_event = event1.copy()
                    joined_event['dtstart'] = start
                    joined_event['dtend'] = end
                    joined_event[f'{attribute}_2'] = event2.get(attribute)
                    joined_events.append(joined_event)
        return joined_events

    def aggregate(self, ics_content, attribute='location'):
        events = self.validate(ics_content)
        aggregated = {}
        for event in events:
            key = event.get(attribute, 'Unknown')
            if key not in aggregated:
                aggregated[key] = []
            aggregated[key].append(event)
        return aggregated

    def nearest_neighbor(self, ics_content, target_time):
        events = self.validate(ics_content)
        if not events:
            return None
        
        # Ensure target_time is offset-aware
        if target_time.tzinfo is None:
            target_time = target_time.replace(tzinfo=pytz.UTC)
        
        def time_difference(event):
            event_time = self.extract_datetime(event.get('dtstart'))
            # Make event_time offset-aware if it's naive
            if event_time.tzinfo is None:
                event_time = event_time.replace(tzinfo=pytz.UTC)
            return abs(event_time - target_time)
        
        return min(events, key=time_difference)

    def centroid(self, ics_content):
        events = self.validate(ics_content)
        if not events:
            return None
        total_duration_seconds = 0
        weighted_sum_seconds = 0
        start_time = None
        for event in events:
            start = self.extract_datetime(event.get('dtstart'))
            end = self.extract_datetime(event.get('dtend'))
            if start_time is None:
                start_time = start
            duration_seconds = (end - start).total_seconds()
            mid_point_seconds = (start - start_time).total_seconds() + duration_seconds / 2
            total_duration_seconds += duration_seconds
            weighted_sum_seconds += duration_seconds * mid_point_seconds
        
        if total_duration_seconds == 0:
            return None
        
        centroid_seconds = weighted_sum_seconds / total_duration_seconds
        return (start_time + timedelta(seconds=centroid_seconds)).replace(tzinfo=pytz.UTC)

    def time_range(self, ics_content):
        events = self.validate(ics_content)
        if not events:
            return None, None
        start_times = [self.extract_datetime(e.get('dtstart')) for e in events]
        end_times = [self.extract_datetime(e.get('dtend')) for e in events]
        return min(start_times), max(end_times)

# Example usage
if __name__ == "__main__":
    processor = CalendarProcessor()
    
    # Assuming you have sample.ics files
    processor.print_event_timeline('sample1.ics')
    processor.print_top_n('sample1.ics', 3)
    processor.sum_duration('sample1.ics')
    
    union_result = processor.union('sample1.ics', 'sample2.ics')
    processor.save_to_ics(union_result, 'union_result.ics')
    
    intersect_result = processor.intersect('sample1.ics', 'sample2.ics')
    processor.save_to_ics(intersect_result, 'intersect_result.ics')
    
    processor.find_free_slots('sample1.ics', 60)
