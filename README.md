# GeoCal

This library provides a set of functions to handle and manipulate iCalendar objects, and includes functionalities to read, validate, sort, and perform specific operations like buffer, sum, union, and intersect on calendar events.

## Features

- **Buffer**: Add buffer time before and after events.
- **Sum**: Calculate the total time of events.
- **Intersect**: Find overlapping time between two calendars.
- **Union**: Merge two calendars and handle event overlaps.

## Requirements

- Python (3.x recommended)
- icalendar
- pytz

## Usage

### Importing the Library

```python
from your_library_path import calend
```

### Creating a Calendar Object

```python
calendar_object = calend()
```

### Buffering Events

```python
buffered_calendar = calendar_object.buffer(ics_content, buffer_time=15)
```

### Calculating the Sum of Events

```python
total_time = calendar_object.sum(ics_content)
```

### Union of Two Calendars

```python
union_calendar = calendar_object.union(ics_content_1, ics_content_2)
```

### Intersection of Two Calendars

```python
intersect_calendar = calendar_object.intersect(ics_content_1, ics_content_2)
```

### Print Event Timeline

```python
calendar_object.print_event_timeline(ics_content)
```

### Print Top N Events

```python
calendar_object.print_top_n(ics_content, n=5)
```

### Save to ICS File

```python
calendar_object.save_to_ics(sorted_events, file_path)
```

## Contributing

Feel free to fork the repository and submit pull requests.

## Contact

Please contact the author or create an issue in the repository if you have any questions or need further assistance.

---
