"""Calendar jumps use normal day/month progression rather than rewriting dates."""
WARP_OPTIONS=((1,'Skip 1 month'),(3,'Skip 3 months'),(6,'Skip 6 months'),(12,'Skip 1 year'),(60,'Skip 5 years'))

def advance_months(months,get_date,advance_day):
    if months not in dict(WARP_OPTIONS):raise ValueError('Unsupported Time Warp duration')
    year,month,day=get_date();target=year*12+month-1+months;skipped=0
    while True:
        year,month,current_day=get_date()
        if year*12+month-1>=target and current_day>=day:break
        advance_day(completed=False,save_after=False);skipped+=1
        if skipped>months*366:raise RuntimeError('Career calendar did not advance')
    return skipped
