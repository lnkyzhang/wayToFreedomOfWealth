
import pandas_market_calendars as mcal
from datetime import time

# Create a calendar
sse = mcal.get_calendar('SSE', open_time=time(9, 30), close_time=time(15, 00))
print(sse.tz.zone)
print('open, close: %s, %s' % (sse.open_time, sse.close_time))
# Show available calendars
# print(mcal.get_calendar_names())
early = sse.schedule(start_date='2000-01-01', end_date='2000-04-10')

print(early)

