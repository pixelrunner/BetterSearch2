#!/usr/bin/env python3

# Search settings

# Leisure Centres:
# 119 = London Aquatics Centre
# 15 is Waltham Forest Feel Good Centre
# 13 = Leytonstone
leisure_centres = [119, 15, 13]

# Days of the week:
# Sunday (0) - Saturday (6)
search_days = [6, 0]

# Course type:
# 842 is Dippers,
# 843 is Dippers-2,
# 844 is Splashers,
# 845 is Paddlers
course_level = [845]


# User settings
healthcheck_url = 'https://hc-ping.com/4ead2448-XXXX-XXXX-XXXX-b98983bce757'
skipped_courses = [] # list course id's you want to skip (enter in strings in to list)
extra_search = [{"courseId": "91349", "course_spaces": -1}] # an extra search where any courses that match the courseId
                                                            # are then alerted if the number of spaces differ from
                                                            # number stated in this dict

# System settings
search_url = 'https://better.coursepro.co.uk/portal/api/HomePortal/booking/search'
debugging = False