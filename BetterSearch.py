#!/usr/bin/env python3

import asyncio
import json
import settings
from typing import Any
import aiohttp
from aiohttp import ClientSession, ClientTimeout
import telegram_send
import time
from datetime import datetime


def main(event: Any = None, context: Any = None) -> None:
    while True:
        asyncio.run(main_async())
        time.sleep(1800)


async def main_async() -> None:
    session = ClientSession(timeout=ClientTimeout(total=10))

    fetches = [fetch(session, i) for i in settings.leisure_centres]
    responses = await asyncio.gather(*fetches, return_exceptions=True)
    await session.close()

    available_courses, keep_alive = find_available_courses(responses)
    if available_courses:
        # print_courses(available_courses)
        send_telegram(available_courses)
    else:
        print(str(datetime.now().strftime("%d/%m/%Y %H:%M:%S")) + ' - No courses available') #debug

    # send healthcheck ping if keepalive is set to true (no errors in retrieving data)
    if keep_alive == True:
        session_hc = ClientSession(timeout=ClientTimeout(total=10))
        async with session_hc.get(settings.healthcheck_url) as response:
            await response.text()
        await session_hc.close()



async def fetch(session: ClientSession, centre_id: int) -> Any:
    filters = {
        "centre": centre_id,
        "courseGroupCategory": 1,  # Swimming
        "courseType": 1,  # Continuous Programme
        "showFullCourses": True,  # Show classes that a full
        "dayOfWeek": settings.search_days,  # Saturday, Sunday
        "level196": settings.course_level,  # 196 is the Swimbies category, 842 is Dippers level, 844 is Splashers level
    }
    async with session.get(
        settings.search_url, params={"filter": json.dumps(filters)}
    ) as response:
        return await response.json()


def find_available_courses(all_courses: tuple[Any, ...]) -> list[dict[str, Any]]:
    courses = []
    keep_alive = True

    for centre in all_courses:
        if isinstance(centre, asyncio.exceptions.TimeoutError):
            keep_alive = False
            continue
        elif isinstance(centre, aiohttp.client_exceptions.ClientConnectorError):
            keep_alive = False
            continue

        for course in centre.get("resultSet", {}).get("results", []):
            if str(course.get("courseId", "")) in settings.skipped_courses:
                continue

            for extra_check_course in settings.extra_search:
                # extra search created:
                # if any courses come up from the predefined list, then check them against the defined spaces and
                # add them to the list to send if the number of spaces differ
                # the example is a course that was shown as -1 and as soon as it goes to 0 then alert
                if str(course.get("courseId", "")) == extra_check_course.get('courseId', '') and \
                        course.get("availability", {}).get("spaces", {}).get("free", 0) != extra_check_course.get('course_spaces', ''):
                    courses.append(course)
                    continue
            if settings.debugging:
                courses.append(course) # Show all courses, for testing purposes
            elif course.get("availability", {}).get("spaces", {}).get("free", 0) > 0:
                courses.append(course)
    return courses, keep_alive

'''
def print_courses(courses: list[dict[str, Any]]) -> None:
    print("Courses available:")

    for course in courses:
        print()
        print(f"  - {course['centre']['name']}")
        print(f"    {course['schedule']['dayOfWeek']}s {course['schedule']['time']['start']} - {course['schedule']['time']['end']}")
        print(f"    {course['availability']['spaces']['free']} spaces available")
        print(f"    Course ID: {course['courseId']}")
'''

def send_telegram(courses: list[dict[str, Any]]) -> None:
    message = "** Swimming Courses available! **\n\n"

    for course in courses:
        message += f"{course['centre']['name']}\n"
        message += f"{course['schedule']['dayOfWeek']}s {course['schedule']['time']['start']} - {course['schedule']['time']['end']}\n"
        message += f"{course['availability']['spaces']['free']} spaces available\n"
        message += f"Course ID: {course['courseId']}\n\n"

    telegram_send.send(messages=[message])
    print(message)


if __name__ == "__main__":
    main()